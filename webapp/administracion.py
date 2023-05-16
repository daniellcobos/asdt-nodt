# Programa de Administracion
from flask import Flask, flash, jsonify, redirect, url_for, session, send_file, g, send_from_directory
import psycopg2
from flask import render_template
from flask import request
import numpy as np
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta  
import os
import sys
from xlsxwriter import Workbook
import smtplib, ssl
from email.mime.text import MIMEText
import psycopg2.extras
import time
from webapp import app
from .informes import *

app.config.from_object('configuraciones.local')
db_connection_string = app.config["POSTGRESQL_CONNECTION"]

@app.route('/freegoods', methods=['GET'])
def freegoods():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae la tabla de freegoods
    msql =  "SELECT * FROM dt_freegood where pais = '" + session['pais'] + "' and usar = 1 order by idplazo, idfreegood"
    cur.execute(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close()
    return render_template('parametros/freegoods.html', data = data)



@app.route('/usuarios_grilla', methods=['GET'])
def usuarios_grilla():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae los usuarios
    # niveles:
    # -2 Super administrdor
    # -1 Administrador del pais
    # +0 Auditor del pais
    # +1 Consultor
    msql = ""
    nivel = {
        -2: "SELECT * FROM dt_usuarios",
        -1: "SELECT * FROM dt_usuarios WHERE pais ='" + session['pais'] + "'",
        10: "SELECT * FROM dt_usuarios WHERE pais ='" + session['pais'] + "'",
        11: "SELECT * FROM dt_usuarios WHERE pais ='" + session['pais'] + "'",
        12: "SELECT * FROM dt_usuarios WHERE pais ='" + session['pais'] + "'",        
         1: "SELECT * FROM dt_usuarios WHERE idusuario = '" + session['idconsultor'] + "'",
         2: "SELECT * FROM dt_usuarios WHERE idusuario = '" + session['idconsultor'] + "'"}
    msql = nivel.get(session['nivel'], "Invalido")         
    cur.execute(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close()
    return render_template('administracion/usuarios_grilla.html', data = data)

@app.route('/usuarios_add/<string:pais>', methods=['GET'])
def usuarios_add(pais):
    return render_template('administracion/usuarios_add.html')


@app.route('/usuarios_guardar', methods=['POST'])
def usuarios_guardar():
    mensaje = 'Iniciar Proceso'

    idusuario = request.form.getlist('idusuario')
    usuario = request.form.getlist('usuario')
    email = request.form.getlist('email')
    password = request.form.getlist('password')
    perfil = request.form.getlist('perfil')
    pais = request.form.getlist('pais')
    
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "INSERT INTO dt_usuarios(idusuario, usuario, email, contrasena, nivel, pais, region) "
    msql = msql + "	VALUES ('" + idusuario[0] + "','" + usuario[0] + "','" + email[0] + "','" + password[0] + "','" + perfil[0] + "', '" + pais[0] + "', 0);"
    try:    
        cur.execute(msql)  
        mensaje = 'Ok. Registro agregado'          
    except Exception as e:
        mensaje = 'Error ' + str(e)
    conn.commit()    
    cur.close()
    conn.close()
    return mensaje


@app.route('/usuarios_edit/<string:idusuario>', methods=['GET'])
def usuarios_edit(idusuario):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "SELECT * FROM dt_usuarios WHERE idusuario = '" + idusuario + "'"
    cur.execute(msql)
    data = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('administracion/usuarios_edit.html', data = data)

@app.route('/usuarios_delete/<string:idusuario>', methods=['GET'])
def usuarios_delete(idusuario):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "DELETE FROM dt_usuarios WHERE idusuario = '" + idusuario + "'"
    cur.execute(msql)    
    conn.commit()    
    cur.close()
    conn.close()
    return redirect('/usuarios_grilla')


@app.route('/usuarios_actualizar/', methods=['POST'])
def usuarios_actualizar():
    mensaje = 'Iniciar Proceso'

    idusuario = request.form.getlist('idusuario')
    usuario = request.form.getlist('usuario')
    email = request.form.getlist('email')
    password = request.form.getlist('password')
    perfil = request.form.getlist('perfil')
    pais = request.form.getlist('pais')
    
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "UPDATE dt_usuarios "
    msql = msql +  "SET usuario='" + usuario[0] + "', email= '" + email[0] + "', contrasena='"+ password[0] + "', nivel= '" + perfil[0] + "'"
    msql = msql + " WHERE idusuario = '" + idusuario[0] + "';"
    print(msql)
    try:    
        cur.execute(msql)  
        mensaje = 'Ok. Registro editado'          
    except Exception as e:
        mensaje = 'Error ' + str(e)
    conn.commit()    
    cur.close()
    conn.close()
    return mensaje

@app.route('/usuarios_exportar/', methods=['GET'])
def usuarios_exportar():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    cur.execute("Select idusuario, usuario, email, nivel, pais, region from dt_usuarios where pais = '" + session['pais'] + "'")

    results = {}
    column = 0
    for d in cur.description:
        results[d[0]] = column
        column = column + 1

    now = datetime.now()
    date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    # Put it all to a data frame
    mnombre = 'Usuarios_'  + date_time  + '.xlsx'
    archivo = os.path.join(app.root_path, 'static/downloads/' , '', mnombre)
    sql_data = pd.DataFrame(cur.fetchall())
    sql_data.columns =results
    sql_data.to_excel (archivo, index = False, header=True)

    cur.close()
    conn.close()

    return mnombre



def enviar_correo():

    # Evniar a:
    receiver_email = "javier.cartagena@synapsis-rs.com"
    # creates SMTP session
    s = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
    # start TLS for security
    s.starttls()
    # Authentication
    s.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    # message to be sent
    message = '<html><body> <b>Hay un Acuerdo para su aprobacion</b> </body></html>'
    my_email = MIMEText(message, "html")
    my_email["Subject"] = "Accion requerida para Acuerdos Allergan.easynet.me "
    # sending the mail
    s.sendmail(app.config['MAIL_USERNAME'], receiver_email, my_email.as_string())
    # terminating the session
    s.quit()

    return "ok"  

# Ver las ventas
@app.route('/ventas', methods=['GET'])
def ventas():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae todas las ventas
    msql =  "SELECT * FROM dt_ventas where pais = '" + session['pais'] + "'"
    cur.execute(msql)
    data = cur.fetchall()
    msql = "Select distinct idperiodo from dt_ventas order by idperiodo asc"
    cur.execute(msql)
    lista = cur.fetchall()
    listarr= []
    for l in lista:
        listarr.append(l[0])
    cur.close()
    conn.close()
    return render_template('parametros/ventas.html', data = data, lista=listarr)

# Importa el archivo de ventas
@app.route('/importar_ventas' , methods=["GET", "POST"])    
def importar_ventas():
    # Importa el archivo de ventas
    mensaje = "Sin procesar"        
    uploaded_file = request.files['file']
    archivo = os.path.join(app.root_path, 'static/uploads/' , uploaded_file.filename)
    archivolog = os.path.join(app.root_path, 'static/', "uploadlog.txt")
    if uploaded_file.filename != '':
        archivo = uploaded_file.save(archivo)
        df = pd.read_excel(os.path.join(app.root_path, 'static/uploads/' , uploaded_file.filename), sheet_name= 0 , engine='openpyxl')
        #Numero de clientes de ventas, para el reporte
        nc = str(df["sap_id"].nunique())
        df = df.fillna(0)
        #numero de ventas por cliente para el reporte
        df2 = df.groupby(['sap_id'])['cantidad'].sum().to_string()
        cansum = df['cantidad'].sum()
        print(cansum)
        dt = df.to_numpy()
        conn = psycopg2.connect(db_connection_string)
        cur = conn.cursor()
        i = 1
        for row in dt:  
            invoice_date = '1'
            idcliente = str(row[1])
            venta_mes = str(row[6])
            venta_ano = str(row[7])
            sap_id = str(row[0])
            pais = str(row[1])
            producto = str(row[2])
            idproducto = str(row[3])
            cantidad = str(row[4])
            idveeva = str(row[5])
            idacuerdo = ''
            if row[6] < 10:
                mperiodo = venta_ano + "0" + venta_mes
            else:
                mperiodo = venta_ano + venta_mes
            idperiodo = mperiodo
            observacion = ''

            mensaje = ventas_insertar(invoice_date, venta_mes, venta_ano, sap_id, pais, producto, idproducto, cantidad, idveeva, idacuerdo, idperiodo, observacion)
            i = i + 1
        
        # Determina a que acuerdo esta una venta
        #ventasxacuerdos1(session['pais'])
        with open(archivolog, "a+") as log:
            log.write("Cantidad de Clientes: " + nc + " Ventas: "+ str(cansum) + " Pais: "+ session['pais']  + "Fecha: "+ datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +"\n" )
            log.write("Ventas por SAP" +"\n"  )
            log.write(df2)
            log.write("\n")
    mensaje = 'Ok, importado'

    return mensaje
        
def ventas_insertar(invoice_date, venta_mes, venta_ano, sap_id, pais, producto, idproducto, cantidad, idveeva, idacuerdo, idperiodo, observacion):
    msql = "INSERT INTO dt_ventas "
    msql = msql + "(invoice_date, venta_mes, venta_ano, sap_id, pais, producto, idproducto, cantidad, idveeva, idacuerdo, idperiodo, observacion)"
    msql = msql + " VALUES ('" +  invoice_date + "','"  + venta_mes + "','"  + venta_ano + "','"  + sap_id + "','"  + pais + "','"  + producto + "','"  + idproducto + "',"  + cantidad + ",'"  + idveeva + "','"  + idacuerdo + "','"  + idperiodo + "','"  + observacion + "')"
    mensaje = ""
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Factura Guardada'
    except Exception as e:
        mensaje = 'Error al guardar ' + str(e)
    cur.close()
    conn.close()  

    return mensaje 

def pcd_identificar_ventaxacuerdo(idacuerdo):
  conn = psycopg2.connect(db_connection_string)
  cur = conn.cursor()


  # Identifica los clientes de un acuerdo
  clientes = []

  # 1. cliente principal
  msql = "select * from dt_acuerdo where idacuerdo = '" + idacuerdo + "'"
  cur.execute(msql)

  row = cur.fetchall()
  colnames = [desc[0] for desc in cur.description]

  df1 = pd.DataFrame(row, columns=colnames)


  cliente = df1.idcliente
  clientes.append(cliente.iloc[0])

  # 2. identifica los clientes multiples
  msql = "SELECT * FROM dt_cliente_multiple where idacuerdo = '" + idacuerdo + "'"
  cur.execute(msql)

  row = cur.fetchall()
  colnames = [desc[0] for desc in cur.description]

  df2 = pd.DataFrame(row, columns=colnames)
  df2

  for index, row in df2.iterrows():
    s = row.iloc[2]
    clientes.append(s)  


  # Identifica los periodos de un acuerdo
  periodos = []

  duracion = df1.duracion[0]
  i = 0
  for n in range(duracion):
    try:
        p = datetime(df1.ano_ini,df1.mes_ini,1)
        q = p + relativedelta(months=n)
        i = i + 1
        periodos.append(q)
    except:
        p = datetime(df1["ano_ini"].iloc[0], df1["mes_ini"].iloc[0], 1)
        q = p + relativedelta(months=n)
        i = i + 1
        periodos.append(q)



  # Para cada cliente de un acuerdo busca si hay ventas y le pone el id del acuerdo
  for cliente in clientes:
    #Convierte el id del cliente a mayuscula
    clientequery = cliente.upper()
    print(clientequery)
    for periodo in periodos:    
      msql = "update dt_ventas set idacuerdo = '"+ idacuerdo + "' where sap_id = '" + clientequery + "' and idperiodo = '" + periodo.strftime("%Y%m") + "'"
      cur.execute(msql)
      conn.commit()

  cur.close()
  conn.close() 



@app.route('/ventasxacuerdos1/<string:pais>', methods=['GET',"POST"])
@app.route('/ventasxacuerdos1/<string:pais>', methods=['GET',"POST"])
def ventasxacuerdos1(pais):
    start = time.time()
    archivolog = os.path.join(app.root_path, 'static/', "uploadlog.txt")
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()

    msql = "SELECT * FROM dt_acuerdo where pais = '" + pais + "' and aprobado <> '3'"
    cur.execute(msql)

    row = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]

    df2 = pd.DataFrame(row, columns=colnames)

    for index, row in df2.iterrows():
        idacuerdo = row.iloc[0]
        pcd_identificar_ventaxacuerdo(idacuerdo)
        message = str(index) + " acuerdo :" + str(idacuerdo)
        print(message)

    cur.close()
    conn.close()
    end = time.time()
    with open(archivolog, "a+") as log:
        log.write("Vinculacion ejecutada en: "+ datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +"\n")
        log.write("Acuerdos Vinculados: " + message +"\n")
        log.write("Tiempo: " + str(end - start) +"\n")

    return "Termino"

def totalizar_ventas(f1,f2,idacuerdo,porcentaje):
    # Calcula las ventas del periodo
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()    
    msql = "SELECT producto, sum(cantidad) from dt_ventas WHERE idperiodo BETWEEN " + str(f1) + " AND " + str(f2) + " AND idacuerdo = '" + idacuerdo + "' and PRODUCTO <> 'LATISSE' GROUP BY producto;"
    cur.execute(msql)
    print(msql)
    productos = cur.fetchall() 
    p1 = 0
    p2 = 0
    p3 = 0
    p4 = 0
    p5 = 0
    p6 = 0
    p7 = 0
    p8 = 0    
    for p in productos:
        if p[0] == "BOTOX":
            p1 = round(p[1])
        if p[0] == "ULTRA":
            p2 = round(p[1])
        if p[0] == "ULTRA PLUS":
            p3 = round(p[1])
        if p[0] == "VOLBELLA":
            p4 = round(p[1])
        if p[0] == "VOLIFT":
            p5 = round(p[1])
        if p[0] == "VOLITE":
            p6 = round(p[1])
        if p[0] == "VOLUMA":
            p7 = round(p[1])
        if p[0] == "VOLUX":
            p8 = round(p[1])
    
    mtotal = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8

    for p in productos:
        if p[0] == "BOTOX":
            p1 = round(p[1] * porcentaje)
            if p1 == mtotal:
                break
        if p[0] == "ULTRA":
            p2 = round(p[1] * porcentaje)
            if p1 + p2 == mtotal:
                break
        if p[0] == "ULTRA PLUS":
            p3 = round(p[1] * porcentaje)
            if p1 + p2 + p3 == mtotal:
                break
        if p[0] == "VOLBELLA":
            p4 = round(p[1] * porcentaje)
            if p1 + p2 + p3 + p4 == mtotal:
                break
        if p[0] == "VOLIFT":
            p5 = round(p[1] * porcentaje)
            if p1 + p2 + p3 + p4 + p5 == mtotal:
                break
        if p[0] == "VOLITE":
            p6 = round(p[1] * porcentaje)
            if p1 + p2 + p3 + p4 + p5 + p6 == mtotal:
                break
        if p[0] == "VOLUMA":
            p7 = round(p[1] * porcentaje)
            if p1 + p2 + p3 + p4 + p5 + p6 + p7 == mtotal:
                break
            
        if p[0] == "VOLUX":
            p8 = round(p[1] * porcentaje)            
            if p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 == mtotal:                
                break
            
    mtotal = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8
    arr = [p1,p2,p3,p4,p5,p6,p7,p8,mtotal]

    print(arr)

    cur.close()
    conn.close()       
    return arr


# Borra un periodo del archivo de ventas
@app.route('/ventas_delete/<string:periodo>' , methods=["GET", "POST"])    
def ventas_delete(periodo):
    msql = "DELETE from dt_ventas WHERE idperiodo = " + periodo + " and pais = '" + session['pais'] + "'"
    mensaje = ""
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Periodo Borrado'
    except Exception as e:
        mensaje = 'Error al borrar' + str(e)
    cur.close()
    conn.close() 

    borrar_liberacion(periodo) 

    return mensaje    

# Importa el archivo de precios
@app.route('/importar_precios' , methods=["GET", "POST"])    
def importar_precios():
    # Importa el archivo de precios
    mensaje = "Sin procesar"        
    uploaded_file = request.files['file']
    archivo = os.path.join(app.root_path, 'static/uploads/' , uploaded_file.filename)
    if uploaded_file.filename != '':
        archivo = uploaded_file.save(archivo)
        df = pd.read_excel(os.path.join(app.root_path, 'static/uploads/' , uploaded_file.filename), sheet_name= 0 , engine='openpyxl')
        df = df.fillna(0)
        dt = df.to_numpy()
        conn = psycopg2.connect(db_connection_string)
        cur = conn.cursor()
        for row in dt:  
            producto = str(row[0])
            idproducto = str(row[1])
            periodo = str(row[2])
            precio_lista = str(row[3])
            precio = str(row[4])
            pais = str(row[5])

            mensaje = precios_insertar(producto,idproducto,periodo,precio_lista,precio,pais)

    return 'Ok, importado'

def precios_insertar(producto, idproducto, periodo, precio_lista, precio, pais):
    msql = "INSERT INTO dt_precios"
    msql = msql + "(producto,idproducto,periodo,precio_lista,precio,pais)"
    msql = msql + " VALUES ('" +  producto + "','"  + idproducto + "','" + periodo + "','"  + precio_lista + "','"  + precio + "','"  + pais + "')"
    mensaje = ""
    
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Precio Guardado'
    except Exception as e:
        mensaje = 'Error al guardar ' + str(e)
    cur.close()
    conn.close()  

    return mensaje     

# Borra un periodo del archivo de precios
@app.route('/precios_delete/<string:periodo>' , methods=["GET", "POST"])    
def precios_delete(periodo):
    msql = "DELETE from dt_precios WHERE periodo = " + periodo
    mensaje = ""
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Periodo Borrado'
    except Exception as e:
        mensaje = 'Error al borrar' + str(e)
    cur.close()
    conn.close()  

    return mensaje        

def liquidar_mes(mperiodo):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "SELECT * from dt_acuerdo where pais = '" +  session['pais']  + "' and vigente = 1 and aprobado = 1 "
    cur.execute(msql)
    data = cur.fetchall() 
    mvector = []
    for row in data:
        # Trae los datos del acuerdo
        idacuerdo = row[0]
        año = row[6]
        mes = row[5]
        duracion = row[9]
        unidades_total = row[10]
        idcliente = row[3].upper()
        porcentaje = row[24] / 100
        # Calcula las ventas para este acuerdo
        msql =  "SELECT sum(cantidad) from dt_ventas where sap_id = '" + idcliente + "' and PRODUCTO <> 'LATISSE' and idperiodo = " + str(mperiodo)
        cur.execute(msql)
        venta = cur.fetchone() 
        if (venta[0] != None):
            cumplimiento = round((venta[0] / unidades_total)*100)
        else:
            cumplimiento = 0
        msql =  "SELECT producto, sum(cantidad) from dt_ventas  where sap_id = '" + idcliente + "' and PRODUCTO <> 'LATISSE' group by producto" 
        cur.execute(msql)
        print(msql)
        productos = cur.fetchall() 
        p1 = 0
        p2 = 0
        p3 = 0
        p4 = 0
        p5 = 0
        p6 = 0
        p7 = 0
        p8 = 0    
        for p in productos:
            if p[0] == "BOTOX":
                p1 = round(p[1] * porcentaje)
            if p[0] == "ULTRA":
                p2 = round(p[1] * porcentaje)
            if p[0] == "ULTRA PLUS":
                p3 = round(p[1] * porcentaje)
            if p[0] == "VOLBELLA":
                p4 = round(p[1] * porcentaje)
            if p[0] == "VOLIFT":
                p5 = round(p[1] * porcentaje)
            if p[0] == "VOLITE":
                p6 = round(p[1] * porcentaje)
            if p[0] == "VOLUMA":
                p7 = round(p[1] * porcentaje)
            if p[0] == "VOLUX":
                p8 = round(p[1] * porcentaje)

        mtotal = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8

        # Trae los clientes multiples
        msql =  "SELECT * from dt_cliente_multiple where idacuerdo = '" + str(idacuerdo) + "'"
        cur.execute(msql)
        clientesm = cur.fetchall() 

        idc = ['','','','']
        cl = ['','','','']
        i=0
        for c in clientesm:
            try:
                idc[i] = c[2]
                cl[i] = c[1]
                i = i + 1
            except:
                i = i +1
            
        vector = [mperiodo, row[0], row[2], row[3], row[4], cumplimiento, p1, p2, p3, p4, p5, p6, p7, p8, mtotal, idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3]]
        mvector.append(vector)
        if mtotal > 0 :
            msql = "INSERT INTO dt_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, cumplimiento, botox, ultra, ultra_plus, volbella, volift, volite, voluma, volux, total_venta, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4) "
            msql = msql + " VALUES (" + str(mperiodo) + ", '" + session['pais'] + "'"
            msql = msql + ", '"+ str(row[0]) +"', '"+ str(row[2]) +"', '"+ str(row[3]) +"', '"+ str(row[4]) +"', "+ str(cumplimiento) +", "+ str(p1) +", "+ str(p2) +", "+ str(p3) +", "+ str(p4) +", "+ str(p5) +", "+ str(p6) +", "+ str(p7) +", "+ str(p8) +", "+ str(mtotal) +", '"+ str(idc[0]) +"', '"+ str(cl[0]) +"', '"+ str(idc[1]) +"', '"+ str(cl[1]) +"', '"+ str(idc[2]) + "', '"+ str(cl[2]) +"', '"+ str(idc[3]) + "', '"+ str(cl[3]) +"'); "
            cur.execute(msql)
            conn.commit()
    cur.close()
    conn.close()  
    return mvector


def borrar_liberacion(mperiodo):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "DELETE FROM dt_liberacion where pais = '" +  session['pais']  + "' and periodo = " + str(mperiodo)
    cur.execute(msql)
    conn.commit()
    cur.close()
    conn.close()    
    return "ok"  


@app.route('/importar_freegood' , methods=["GET", "POST"])
def importar_freegood():
    # Importa el archivo de freegoods
    mensaje = "Sin procesar"
    uploaded_file = request.files['file']
    archivo = os.path.join(app.root_path, 'static/uploads/' , uploaded_file.filename)
    if uploaded_file.filename != '':
        archivo = uploaded_file.save(archivo)
        df = pd.read_excel(os.path.join(app.root_path, 'static/uploads/' , uploaded_file.filename), sheet_name= 0 , engine='openpyxl')
        df = df.fillna(0)
        dt = df.to_numpy()

    return  freegood_insertar(dt)


def freegood_insertar(df):

    freegoodList = []
    for row in df:
        ftuple = (row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11],row[12])
        freegoodList.append(ftuple)

    msql = "insert into " \
           "dt_freegood(idbanda,banda,banda_min,banda_max,idplazo,plazo,porc_descuento,cant_mes_x_banda,resumen_banda,porc_fgs,pais,usar) " \
           "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    print(msql,ftuple)
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    try:
        cur.execute("update dt_freegood set usar = 0 where pais = %s",(session['pais'], ) )
        psycopg2.extras.execute_batch(cur, msql, freegoodList)
        conn.commit()
        mensaje = 'Freegood Guardado'
    except Exception as e:
        mensaje = 'Error al guardar ' + str(e)
        print(e)
    cur.close()
    conn.close()

    return mensaje


# Opciones del sistema
@app.route('/sistema' , methods=["GET", "POST"])    
def sistema():
    if session['nivel'] == -1:
        return render_template('parametros/sistema.html')
    else:
         return redirect('/misacuerdos')

@app.route('/metricas')
def metricas():
    archivolog = os.path.join(app.root_path, 'static/', "informelog.txt")
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "select venta_ano,venta_mes,sum(cantidad) from dt_ventas where pais = %s group by venta_mes,venta_ano order by venta_ano, venta_mes;"
    cur.execute(msql, (session['pais'],))
    df = pd.DataFrame(cur.fetchall(), columns=["Año","Mes","Cantidad"])
    msql = "select venta_ano,venta_mes,sum(cantidad) from dt_ventas where pais = %s and idacuerdo <> '' group by venta_mes,venta_ano order by venta_ano, venta_mes;"
    cur.execute(msql, (session['pais'],))
    df2 = pd.DataFrame(cur.fetchall(), columns=["Año","Mes","Cantidad"])
    msql = "select ano_ini,mes_ini,count(idacuerdo) from dt_acuerdo where vigente = 1 and pais=%s group by mes_ini,ano_ini order by ano_ini, mes_ini;"
    cur.execute(msql, (session['pais'],))
    df3 = pd.DataFrame(cur.fetchall(), columns=["Año","Mes","Cantidad"])
    msql = "select ano_ini,mes_ini,count(idacuerdo) from dt_acuerdo where vigente = 1 and pais=%s and idacuerdo in (select dt_ventas.idacuerdo from dt_ventas) group by mes_ini,ano_ini order by ano_ini, mes_ini;"
    cur.execute(msql, (session['pais'],))
    df4 = pd.DataFrame(cur.fetchall(), columns=["Año","Mes","Cantidad"])
    msql = "select count(*) from dt_liberacion where pais = %s;"
    cur.execute(msql, (session['pais'],))
    n1 = cur.fetchone()
    msql = "select count(*) from dt_liberacion where pais = %s and idacuerdo in (select dt_acuerdo.idacuerdo  from dt_acuerdo where vigente = 1);"
    cur.execute(msql, (session['pais'],))
    n2 = cur.fetchone()
    df.to_excel("v1.xlsx")
    df2.to_excel("v2.xlsx")
    df3.to_excel("v3.xlsx")
    df4.to_excel("v4.xlsx")
    with open(archivolog, "w+") as log:
            log.write("Cantidad de ventas por mes: \n" )
            log.write(df.to_string() + "\n")
            log.write("Cantidad de ventas por mes vinculadas a un acuerdo:" +"\n"  )
            log.write(df2.to_string() + "\n")
            log.write("Cantidad de acuerdos activos por mes:" +"\n")
            log.write(df3.to_string() + "\n")
            log.write("Cantidad de acuerdos activos por mes vinculados a una venta:" + "\n")
            log.write(df4.to_string() + "\n")
            log.write("Liberaciones totales: " + str(n1[0])+ "\n")
            log.write("Liberaciones totales activas: " + str(n2[0]) + "\n")
            log.write("\n")
    folder = os.path.join(app.root_path, "static")
    print(vrf_acuerdos_multiples())
    print(vrf_ventas_liberaciones())
    try:
        return send_from_directory(path=archivolog, directory=folder, filename="informelog.txt")
    except:
        return redirect('/misacuerdos')
