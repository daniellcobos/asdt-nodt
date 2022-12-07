# Programa de Clientes
from flask import Flask,  flash, jsonify, redirect, url_for, session, send_file, g
import psycopg2
from flask import render_template
from flask import request
import os
import sys
import pandas as pd 
import numpy as np
import time
from datetime import datetime
from webapp import app

app.config.from_object('configuraciones.local')
db_connection_string = app.config["POSTGRESQL_CONNECTION"]

@app.route('/clientes', methods=['GET'])
def clientes():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae tabla de clientes
    msql =  "SELECT * FROM dt_cliente WHERE pais = '"  + session['pais'] + "'"
    cur.execute(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close()
    return render_template('clientes/clientes_grilla.html', data = data)


@app.route('/clientes_add', methods=['GET'])
def clientes_add():    
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae tabla de usuarios
    msql = "SELECT idusuario, usuario  FROM dt_usuarios WHERE pais ='" + session['pais'] + "' and nivel = 1"
    cur.execute(msql)
    consultores = cur.fetchall() 
    consultores = list(consultores)
    print(consultores)
    # Caso de Argentina de clientes sin consultor asignado
    if (session['pais'] == 'AR'):
        consultores.append(['AR-02-0-1-0105', 'UNALLOCATED'])
    return render_template('clientes/clientes_add.html', consultores = consultores)

@app.route('/clientes_guardar', methods=['POST'])
def clientes_guardar():
    idcliente= request.form.getlist('row[idcliente]')
    cliente= request.form.getlist('row[cliente]')
    idveeva= request.form.getlist('row[idveeva]')
    idconsultor= request.form.getlist('row[idconsultor]')
    consultor= request.form.getlist('row[consultor]')
    pais= request.form.getlist('row[pais]')

    mensaje = clientes_insertar(idcliente[0],cliente[0],idconsultor[0],consultor[0],idveeva[0],pais[0])
    
    return mensaje

@app.route('/clientes_edit/<string:idcliente>', methods=['GET'])
def clientes_edit(idcliente):    
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Trae los datos del cliente
    msql = "SELECT * FROM dt_cliente WHERE idcliente ='" + idcliente + "'"
    cur.execute(msql)
    data = cur.fetchall()     
    # Trae tabla de usuarios
    msql = "SELECT idusuario, usuario  FROM dt_usuarios WHERE pais ='" + session['pais'] + "' and nivel = 1"
    cur.execute(msql)
    consultores = cur.fetchall() 
    consultores = list(consultores)
    print(consultores)
    # Caso de Argentina de clientes sin consultor asignado
    if (session['pais'] == 'AR'):
        consultores.append(['AR-02-0-1-0105', 'UNALLOCATED'])
    return render_template('clientes/clientes_edit.html', data = data ,consultores = consultores)

@app.route('/clientes_edit_guardar', methods=['POST'])
def clientes_edit_guardar():
    idcliente= request.form.getlist('row[idcliente]')
    cliente= request.form.getlist('row[cliente]')
    idconsultor= request.form.getlist('row[idconsultor]')
    consultor= request.form.getlist('row[consultor]')
    idveeva = request.form.getlist('row[idveeva]')
    

    msql = "UPDATE dt_cliente SET "
    msql = msql + " cliente = '" + cliente[0] + "' , id_consultor = '" + idconsultor[0] + "', consultor = '" + consultor[0] + "', idveeva  = '" + idveeva[0] + "'"
    msql = msql + " where idcliente = '" + idcliente[0] + "'"

    mensaje = ""
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Cliente Guardado'
    except Exception as e:
         mensaje = 'Error al guardar ' + str(e)
    cur.close()
    conn.close()    

    return mensaje

@app.route('/clientes_borrar/<string:idcliente>', methods=['GET','POST'])
def clientes_borrar(idcliente):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "DELETE from dt_cliente where idcliente = '" + idcliente + "'"
    try:    
        cur.execute(msql)
        conn.commit()
    except Exception as e:
         mensaje = 'Error al borrar ' + str(e)
    cur.close()
    conn.close()  
    path = '/clientes'
    return redirect(path)    

def clientes_insertar(idcliente, cliente, idconsultor, consultor, idveeva, pais ):
    msql = "INSERT INTO dt_cliente "
    msql = msql + "(idcliente, cliente, id_consultor, consultor, idveeva, pais)"
    msql = msql + " VALUES ('" +  idcliente + "','"  + (cliente) + "','"  + (idconsultor) + "','"  + (consultor) + "','"  + (idveeva) + "','"  + (pais) + "')"
    mensaje = ""
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    try:
        cur.execute(msql)
        conn.commit()
        mensaje = 'Cliente Guardado'
    except Exception as e:
            mensaje = 'Error al guardar ' + str(e)
    cur.close()
    conn.close()

    return mensaje

# Importa el archivo de clientes
@app.route('/importar_clientes' , methods=["GET", "POST"])    
def importar_clientes():
    # Importa el archivo de clientes
    mensaje = "Sin procesar"        
    uploaded_file = request.files['file']
    archivo = os.path.join(app.root_path, 'static/uploads/' , uploaded_file.filename)
    try:
        if uploaded_file.filename != '':
            archivo = uploaded_file.save(archivo)
            df = pd.read_excel(os.path.join(app.root_path, 'static/uploads/' , uploaded_file.filename), sheet_name= 0 , engine='openpyxl')
            df = df.fillna(0)
            dt = df.to_dict('records')
            conn = psycopg2.connect(db_connection_string)
            cur = conn.cursor()
            for row in dt:
                try:
                    idcliente = str(row['idcliente'])
                except:
                    idcliente = str(row['idCliente'])
                cliente = str(row['cliente'])
                idconsultor = str(row['id_consultor'])
                consultor = str(row['consultor'])
                try:
                    idveeva = str(row['idveeva'])
                except:
                    idveeva = str(row['idVeeva'])
                pais = str(row['pais'])
                print(idcliente,cliente,idconsultor,consultor,idveeva,pais)
                mensaje = clientes_insertar(idcliente,cliente,idconsultor,consultor,idveeva,pais)

            return 'Ok, importado'
    except Exception as e:

        print(e)
        return str(e)


@app.route('/clientes_exportar/', methods=['GET'])
def clientes_exportar():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    cur.execute("Select * from dt_cliente where pais = '" + session['pais'] + "'")

    results = {}
    column = 0
    for d in cur.description:
        results[d[0]] = column
        column = column + 1

    now = datetime.now()
    date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    # Put it all to a data frame
    mnombre = 'Clientes_'  + date_time  + '.xlsx'
    archivo = os.path.join(app.root_path, 'static/downloads/' , '', mnombre)
    sql_data = pd.DataFrame(cur.fetchall())
    sql_data.columns =results
    sql_data.to_excel (archivo, index = False, header=True)

    cur.close()
    conn.close()

    return mnombre



