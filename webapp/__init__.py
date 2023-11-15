# -*- coding: utf-8 -*-
# Programa Principal
import pandas as pd
from flask import Flask,  flash, jsonify, redirect, url_for, session, send_file, g, make_response
from flask_cors import CORS
import psycopg2
from flask import render_template
from flask import request
import os
import sys
from flask_login import LoginManager,login_user,logout_user,login_required,current_user
import smtplib, ssl
from email.mime.text import MIMEText
import random
import string
#from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.triggers.interval import IntervalTrigger
#import atexit
#import time
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from urllib.parse import urlparse

# Iniciar la app
app = Flask(__name__, static_url_path = '/static')
app.config.from_object('configuraciones.local')
dir_path = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(dir_path,"static","uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = app.config["APP_SECRET_KEY"]
db_connection_string = app.config["POSTGRESQL_CONNECTION"]
app.url_map.strict_slashes = False
CORS(app, resources={r"/*": {"origins": "*"}})

# Llamar los modulos de la app
from .clientes import *
from .acuerdos import *
from .administracion import *
from .reportes import *


# Parametros de la sesion de usuario
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Debe ingresar su credenciales para acceder al sistema"


@login_manager.user_loader
def load_user(user_id):
    return 'ok'
    #return User.objects(id=user_id).first()

salt = app.config["APP_SECRET_KEY"]
app.config['SAML_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saml')
logging.basicConfig(filename='mainlog.log', level=logging.DEBUG)
def init_saml_auth(req):

    auth = OneLogin_Saml2_Auth(req, custom_base_path=app.config['SAML_PATH'])
    return auth


def prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    url_data = urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'query_string': request.query_string
    }
# Ingreso al sistema con validacion de usuario funcion login
@app.route('/', methods=['GET', 'POST'])
def login():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    if 'sso' in request.args:

        return redirect(auth.login())
        # If AuthNRequest ID need to be stored in order to later validate it, do instead
        # sso_built_url = auth.login()
        # request.session['AuthNRequestID'] = auth.get_last_request_id()
        # return redirect(sso_built_url)
    elif 'sso2' in request.args:
        return_to = '%sattrs/' % request.host_url
        return redirect(auth.login(return_to))
    elif 'slo' in request.args:
        name_id = session_index = name_id_format = name_id_nq = name_id_spnq = None
        if 'samlNameId' in session:
            name_id = session['samlNameId']
        if 'samlSessionIndex' in session:
            session_index = session['samlSessionIndex']
        if 'samlNameIdFormat' in session:
            name_id_format = session['samlNameIdFormat']
        if 'samlNameIdNameQualifier' in session:
            name_id_nq = session['samlNameIdNameQualifier']
        if 'samlNameIdSPNameQualifier' in session:
            name_id_spnq = session['samlNameIdSPNameQualifier']

        # return redirect(auth.logout(name_id=name_id, session_index=session_index, nq=name_id_nq, name_id_format=name_id_format, spnq=name_id_spnq))
        #  If LogoutRequest ID need to be stored in order to later validate it, do instead
        slo_built_url = auth.logout(name_id=name_id, session_index=session_index)
        session['LogoutRequestID'] = auth.get_last_request_id()
        return redirect(slo_built_url)
    elif 'acs' in request.args:
        return acshandler(auth, req)
    elif 'sls' in request.args:
        request_id = None
        if 'LogoutRequestID' in session:
            request_id = session['LogoutRequestID']
        dscb = lambda: session.clear()
        url = auth.process_slo(request_id=request_id, delete_session_cb=dscb)
        errors = auth.get_errors()
        if len(errors) == 0:
            if url is not None:
                # To avoid 'Open Redirect' attacks, before execute the redirection confirm
                # the value of the request.form['RelayState'] is a trusted URL.
                return redirect(url)
            else:
                success_slo = True
        elif auth.get_settings().is_debug_active():
            error_reason = auth.get_last_error_reason()

    if 'samlUserdata' in session:
        paint_logout = True
        if len(session['samlUserdata']) > 0:
            attributes = session['samlUserdata'].items()

    return render_template(
        'index.html',
        errors=errors,
        error_reason=error_reason,
        not_auth_warn=not_auth_warn,
        success_slo=success_slo,
        attributes=attributes,
        paint_logout=paint_logout
    )



def acshandler(auth,req):

    request_id = None
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()

    if 'AuthNRequestID' in session:
        request_id = session['AuthNRequestID']

    auth.process_response(request_id=request_id)
    errors = auth.get_errors()
    not_auth_warn = not auth.is_authenticated()
    if len(errors) == 0:
        if 'AuthNRequestID' in session:
            del session['AuthNRequestID']
        session['samlUserdata'] = auth.get_attributes()
        email = auth.get_attributes()["email_address"][0]
        msql = "SELECT * FROM dt_usuarios WHERE email = %s"
        cur.execute(msql, (email, ))
        user = cur.fetchone()
        if user is None:
            return "No existes"
        else:


            session['samlNameIdFormat'] = auth.get_nameid_format()
            session['samlNameIdNameQualifier'] = auth.get_nameid_nq()
            session['samlNameIdSPNameQualifier'] = auth.get_nameid_spnq()
            session['samlSessionIndex'] = auth.get_session_index()
            self_url = OneLogin_Saml2_Utils.get_self_url(req)
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = user[2]
            session['username'] = user[2]
            session['nivel'] = user[4]
            session['idconsultor'] = user[0]
            session['pais'] = user[5]
            session['usuario'] = user[1]
            session.permanent = True
            # Redirect to home page
            cur.close()
            conn.close()

            current = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

            if 'RelayState' in request.form and self_url != request.form['RelayState']:
                # To avoid 'Open Redirect' attacks, before execute the redirection confirm
                # the value of the request.form['RelayState'] is a trusted URL

                return redirect(url_for('misacuerdos'))
    elif auth.get_settings().is_debug_active():
        error_reason = auth.get_last_error_reason()



# Este es el decorador de seguridad, se corre cada vez que alguien hace un request a cualquier pagina
@app.before_request
def before_request():
    if (request.endpoint == 'recuperar_acceso'):
        return
    session.permanent = True    
    if 'loggedin' not in session and request.endpoint != 'login':
        msg = 'Realice el ingreso a la cuenta de easynet'
        return redirect('/?sso')

# Cierra la sesion actual
@app.route('/logout')
def logout():
    logger = setup_logger('auth', 'auth.log')
    # Remove session data, this will log the user out
    current = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    logger.info(session['username'] + ' has logged out on ' + current)
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page


    return redirect(url_for('login'))


# Rutas para los usuarios
@app.route('/parametrosfg', methods=['GET'])
def parametrosfg():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae tabla de clientes
    msql =  "SELECT * FROM dt_parametros_sistema"
    cur.execute(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close()
    return render_template('parametros/parametrosfg.html', data = data)


@app.route('/liberaciones', methods=['GET'])
def liberaciones():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae tabla de liberaciones
    msql =  "SELECT * FROM dt_liberacion order by idliberacion desc"
    cur.execute(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close()
    return render_template('parametros/liberaciones.html', data = data)


@app.route('/productos', methods=['GET'])
def productos():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae la tabla de productos
    pais =  session['pais']  
    msql =  "SELECT * FROM dt_producto where pais = '" + pais + "'"
    cur.execute(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close()
    return render_template('parametros/productos.html', data = data)
 


@app.route('/precios', methods=['GET'])
def precios():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae todas los precios
    pais =  session['pais']  
    msql =  "SELECT * FROM dt_precios where pais = '" + pais + "'"
    cur.execute(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close()
    return render_template('parametros/precios.html', data = data)



@app.route('/precios_exportar/', methods=['GET'])
def precios_exportar():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    cur.execute("Select * from dt_precios where pais = '" + session['pais'] + "'")

    results = {}
    column = 0
    for d in cur.description:
        results[d[0]] = column
        column = column + 1

    now = datetime.now()
    date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    # Put it all to a data frame
    mnombre = 'Precios_' + date_time + '.xlsx'
    archivo = os.path.join(app.root_path, 'static/downloads/' , '', mnombre)
    sql_data = pd.DataFrame(cur.fetchall())
    sql_data.columns =results
    #Formatos
    writer = pd.ExcelWriter(archivo, engine="xlsxwriter")
    sql_data.to_excel (writer, sheet_name='Sheet1',startrow=1 ,index=False, header=False)
    worksheet = writer.sheets['Sheet1']
    worksheet.set_column(0, 10, 15)
    wb = writer.book
    fmt = wb.add_format({'bg_color': '#0073b7', 'font_color': '#FFFFFF', 'bold': True, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter'})
    for col_num, value in enumerate(sql_data.columns.values):
        worksheet.write(0, col_num , value, fmt)
    writer.save()
    cur.close()
    conn.close()

    return mnombre

@app.route('/freegoods_exportar/', methods=['GET'])
def freegoods_exportar():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    cur.execute("Select * from dt_freegood where pais = '" + session['pais'] + "'")

    results = {}
    column = 0
    for d in cur.description:
        results[d[0]] = column
        column = column + 1

    now = datetime.now()
    date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    # Put it all to a data frame
    mnombre = 'Freegood_' + date_time + '.xlsx'
    archivo = os.path.join(app.root_path, 'static/downloads/' , '', mnombre)
    sql_data = pd.DataFrame(cur.fetchall())
    sql_data.columns = results
    #Formatos
    writer = pd.ExcelWriter(archivo, engine="xlsxwriter")
    sql_data.to_excel(writer, sheet_name='Sheet1', startrow=1,index=False, header=False)
    worksheet = writer.sheets['Sheet1']
    worksheet.set_column(0, 10, 16)
    worksheet.set_column(12, 15, 15)
    wb = writer.book
    fmt = wb.add_format({'bg_color': '#0073b7', 'font_color': '#FFFFFF', 'bold': True, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter'})
    print(sql_data)
    for col_num, value in enumerate(sql_data.columns.values):
        worksheet.write(0, col_num, value, fmt)
    writer.save()
    cur.close()
    conn.close()

    return mnombre


@app.route('/recuperar_acceso/<string:email>', methods=['GET'])
def recuperar_acceso(email):
    username = email
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "SELECT * FROM dt_usuarios WHERE email = %s"
    characters = string.ascii_letters + string.digits
    passwordplain = ''.join(random.choice(characters) for i in range(9))
    saltpass = salt + passwordplain
    m = hashlib.sha3_256()
    m.update(saltpass.encode('utf-8'))
    password = m.hexdigest()
    cur.execute(msql, (username, ))
    row = cur.fetchone()


    if row == None:
        cur.close()
        conn.close()
        return "No es un usuario del sistema."  

    else:
        msql = "UPDATE dt_usuarios  SET contrasena= %s WHERE idusuario = %s ;"
        cur.execute(msql, (password, row[0]))
        conn.commit()
        cur.close()
        conn.close()
        # Evniar a:
        receiver_email = email
        # creates SMTP session
        s = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        # start TLS for security
        s.starttls()
        # Authentication
        s.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        # message to be sent
        message = '<html><body> <b>Su nuvea contraseña de acceso al sistema es: </b> ' + passwordplain + ', recuerde cambiarla al entrar</body></html>'
        my_email = MIMEText(message, "html")
        my_email["Subject"] = "Revise este correo para su acceso a Allergan.easynet.me "
        # sending the mail
        s.sendmail(app.config['MAIL_USERNAME'], receiver_email, my_email.as_string())
        # terminating the session
        s.quit()

        return "La contraseña fue enviada a su email registrado."
 

#Procedimientos de mantenimiento
def sistema_mantenimiento():
    print (time.strftime('%H:%M:%S'))
    #Deja sin vigencia los acuerdos vencidos
    now = datetime.now()
    year = now.year
    mes = now.month
    if mes == 1:
        year = year - 1
        mes = 12
    else:
        year = year
        mes = mes - 1
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "update dt_acuerdo set vigente = 0 where ano_fin = " + str(year)  + " and mes_fin = " + str(mes)
    cur.execute(msql)
    conn.commit()
    cur.close()
    conn.close()  
    return "ok"


# create schedule for printing time
#scheduler = BackgroundScheduler()
#scheduler.start()
#scheduler.add_job(
#    func=sistema_mantenimiento,
#    trigger=IntervalTrigger(seconds=30),
#    id='printing_time_job',
#    name='Print time every 1 hour',
#    replace_existing=True)
# Shut down the scheduler when exiting the app
#atexit.register(lambda: scheduler.shutdown())  



@app.route('/bajar_liberaciones', methods=['GET'])
def bajar_liberaciones():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "SELECT * FROM dt_liberacion WHERE pais = '" + 'AR' + "'"
    cur.execute(msql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows,columns=colnames)
    df.to_excel('liberaciones.xlsx', index=False)
    cur.close()
    conn.close()  
    return 'ok'

@app.route('/bajar_ventas', methods=['GET'])
def bajar_ventas():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "SELECT * FROM dt_ventas WHERE pais = '" + 'AR' + "'"
    cur.execute(msql)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows,columns=colnames)
    df.to_excel('ventas.xlsx', index=False)
    cur.close()
    conn.close()  
    return 'ok'    

@app.template_filter()
def formatomes(value):
    mes = ""
    if value == 1:
        mes = "Enero"
    if value == 2:
        mes = "Febrero"
    if value == 3:
        mes = "Marzo"
    if value == 4:
        mes = "Abril"
    if value == 5:
        mes = "Mayo"
    if value == 6:
        mes = "Junio"
    if value == 7:
        mes = "Julio"
    if value == 8:
        mes = "Agosto"
    if value == 9:
        mes = "Septiembre"
    if value == 10:
        mes = "Octubre"
    if value == 11:
        mes = "Noviembre"
    if value == 12:
        mes = "Diciembre"
        
    return mes


@app.template_filter()
def formatovigente(value):
    vigente = ""
    if value == 0:
        vigente = "No"
    if value == 1:
        vigente = "Si"
    if value == 2:
        vigente = "No"
    if value == 3:
        vigente = "Cancelado"
        
    return vigente

def setup_logger(name, log_file, level=logging.INFO):


    handler = logging.FileHandler(log_file)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

@app.route('/metadata/')
def metadata():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    settings = auth.get_settings()
    metadata = settings.get_sp_metadata()
    errors = settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = make_response(metadata, 200)
        resp.headers['Content-Type'] = 'text/xml'
    else:
        resp = make_response(', '.join(errors), 500)
    return resp
