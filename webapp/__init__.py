# -*- coding: utf-8 -*-
# Programa Principal
import pandas as pd
from flask import Flask,  flash, jsonify, redirect, url_for, session, send_file, g
from flask_cors import CORS
import psycopg2
from flask import render_template
from flask import request
import os
import sys
from flask_login import LoginManager,login_user,logout_user,login_required,current_user
import smtplib, ssl
from email.mime.text import MIMEText
import hashlib
#from apscheduler.schedulers.background import BackgroundScheduler
#from apscheduler.triggers.interval import IntervalTrigger
#import atexit
#import time



# Iniciar la app
app = Flask(__name__, static_url_path = '/static')
app.config.from_object('configuraciones.local')
dir_path = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = os.path.join(dir_path,"static","uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = app.config["APP_SECRET_KEY"]
db_connection_string = app.config["POSTGRESQL_CONNECTION"]
app.url_map.strict_slashes = False

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


# Ingreso al sistema con validacion de usuario funcion login
@app.route('/', methods=['GET', 'POST'])
def login():
    salt = app.config["APP_SECRET_KEY"]
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        conn = psycopg2.connect(db_connection_string)
        cur = conn.cursor()
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        #saltpass = salt+password
        #m = hashlib.sha3_256()
        #m.update(saltpass.encode('utf-8'))
        #password = m.hexdigest()

        # Check if account exists using postgress
        msql =  "SELECT * FROM dt_usuarios WHERE email = '" + username + "' AND contrasena = '" + password + "'"
        cur.execute(msql)
        # Fetch one record and return result
        row = cur.fetchone()
        # If account exists in accounts table in out database
        if row:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = row[2]
            session['username'] = row[2]
            session['nivel'] = row[4]
            session['idconsultor'] = row[0]
            session['pais'] = row[5]
            session['usuario'] = row[1]
            session.permanent = True
            # Redirect to home page
            cur.close()
            conn.close()
            return redirect(url_for('misacuerdos'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Usuario/Clave Incorrecto!'
    # Show the login form with message (if any)
    return render_template('autenticacion/login.html', msg=msg)

# Este es el decorador de seguridad, se corre cada vez que alguien hace un request a cualquier pagina
@app.before_request
def before_request():
    if (request.endpoint == 'api_acuerdos'):
        return
    if (request.endpoint == 'recuperar_acceso'):
        return
    session.permanent = True    
    if 'loggedin' not in session and request.endpoint != 'login':
        msg = 'Realice el ingreso a la cuenta de easynet'
        return render_template('autenticacion/login.html', msg = msg)

# Cierra la sesion actual
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
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
    writer.close()
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
    writer.close()
    cur.close()
    conn.close()

    return mnombre


@app.route('/recuperar_acceso/<string:email>', methods=['GET'])
def recuperar_acceso(email):
    username = email
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "SELECT * FROM dt_usuarios WHERE email = '" + username + "'"
    cur.execute(msql)
    row = cur.fetchone()
    cur.close()
    conn.close()  

    if row == None:
        return "No es un usuario del sistema."  


    # Evniar a:
    receiver_email = email
    # creates SMTP session
    s = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
    # start TLS for security
    s.starttls()
    # Authentication
    s.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    # message to be sent
    message = '<html><body> <b>Su contraseña de acceso al sistema es: </b> ' + row[3] + '</body></html>'
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