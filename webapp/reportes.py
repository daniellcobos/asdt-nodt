# Programa de Administracion
from json import encoder
from flask import Flask,  flash, jsonify, redirect, url_for, session, send_file, g
from flask.json import JSONEncoder
import psycopg2
from flask import render_template
from flask import request
import numpy as np
import pandas as pd
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import locale
import os
import sys
import math
from xlsxwriter import Workbook
import smtplib, ssl
from email.mime.text import MIMEText
import json

from webapp import app
from .utilidades import *
from flask import send_from_directory
from werkzeug.utils import secure_filename
from os import listdir
from os.path import isfile, join

app.config.from_object('configuraciones.local')
db_connection_string = app.config["POSTGRESQL_CONNECTION"]
locale.setlocale(locale.LC_ALL, 'es_CO.utf8')


@app.route('/liberaciones_total', methods=['GET','POST'])
def liberaciones_total():
    today = datetime.now()
    if request.method == 'POST':
        year = request.form['year']
    elif today.month == 12:
        year = str(today.year + 1)
    else:
        year = today.strftime("%Y")


    actualizar_bandas()
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()



    msql = "select max(idperiodo) from dt_ventas where pais = '" + session['pais'] + "'"
    cur.execute(msql)
    mperiodo = cur.fetchone()
    mperiodo = mperiodo[0]
    print(year)
    if session['nivel'] != 1 :
        msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux,dl.harmonyca, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, dl.banda, dl.banda_min, dl.banda_max, dl.cantidad_periodo, dl.periodo ,  da.porc_descuento , '' as cumplimiento from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = %s and (da.ano_fin = %s or da.ano_fin = '2024') order by dl.idacuerdo,dl.corte"
        cur.execute(msql, (session['pais'], year))
    else:
        msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux,dl.harmonyca, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, dl.banda, dl.banda_min, dl.banda_max dl, dl.cantidad_periodo,  dl.periodo, da.porc_descuento ,  '' as cumplimiento from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = %s and da.idconsultor = %s  and (da.ano_fin = %s or da.ano_fin = '2024')   order by dl.idacuerdo,dl.corte"
        cur.execute(msql, (session['pais'], session['idconsultor'], year))
    print(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close() 

    arr = []

    for t in data:
        arr.append(t)    

    arr = np.array(arr)  



    for t in arr:
        for i,x in enumerate(t):
             if x == None:
                t[i] = ''
        t[36] = float(t[36])
        p= str(t[35])
        p = p[0:6]
        p = int(p)


        if (int(t[4]) < 4) or (t[5] == 'Cierre'):
            t[34] = ""
        elif (p > mperiodo):
            t[34] = ""
        elif (int(t[32])*3) > int(t[12]) :
            t[34] = "Incumple"
        elif (int(t[32])*3) <= int(t[12]) and (int(t[12]) <= int(t[33])*3):
            t[34] = "Cumple"
        elif (int(t[12]) > int(t[33])*3):
            t[34] = "Excede"
            
    
    altarr = []
    for row in arr:
        reorderedRoW = [row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[32], row[9], row[12], row[10]
        , row[11], row[22], round(row[36] * 100,2), row[13], row[14], row[15], row[16], row[17], row[18], row[19], row[20],row[21], row[23], row[24]
        , row[25], row[26], row[27], row[28], row[29], row[30], row[31], row[32], row[33],row[34]]
        altarr.append(reorderedRoW)



    
    return render_template('reportes/liberaciones_total.html', data1 = altarr)

@app.route('/liberaciones_total_exportar/', methods=['GET'])
def liberaciones_total_exportar():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    if session['nivel'] != 1 :
        msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux,dl.harmonyca, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, da.cantidad_periodo from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = '" +  session['pais']  + "' order by dl.idacuerdo,dl.corte"
    else:
        msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux,dl.harmonyca, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, da.cantidad_periodo from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = '" +  session['pais']  + "' and da.idconsultor = '" + session['idconsultor'] + "' order by dl.idacuerdo,dl.corte"
    cur.execute(msql)
    df = cur.fetchall()
    arr = []
    # Recodifica la salida
    for d in df:
        t = list(d)
        arr.append(t)

    results = {}
    column = 0
    for d in cur.description:
        results[d[0]] = column
        column = column + 1

    now = datetime.now()
    date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    # Put it all to a data frame
    mnombre = 'Liberaciones_total_'  + date_time  + '.xlsx'
    archivo = os.path.join(app.root_path, 'static/downloads/' , '', mnombre)
    sql_data = pd.DataFrame(arr)
    sql_data.columns =results
    sql_data.to_excel (archivo, index = False, header=True)

    cur.close()
    conn.close()

    return mnombre


@app.route('/liberaciones_mes', methods=['GET'])
def liberaciones_mes():
    actualizar_bandas()
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    ano_actual = datetime.now().strftime("%Y")
    mes_actual = datetime.now().strftime("%B")
    first_day_of_this_month = date.today().replace(day=1)
    last_day_prev_month = first_day_of_this_month - timedelta(days=1)
    last_day_prev_month = first_day_of_this_month - timedelta(days=0)
    prev_month_name = last_day_prev_month.strftime('%B') 
    mes_actual = prev_month_name

    if session['nivel'] != 1 :
        msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux,dl.harmonyca, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, dl.banda, dl.banda_min, dl.banda_max, dl.cantidad_periodo, dl.periodo , '' as cumplimiento from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = '" +  session['pais']  + "' and dl.mes_entrega = '" + mes_actual + "'  and dl.ano_entrega = " + ano_actual +  " and total_venta >0 and corte <> 'Cierre' and da.aprobado <> '3' order by dl.idacuerdo,dl.corte"
    else:
        msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux, dl.harmonyca,dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, dl.banda, dl.banda_min, dl.banda_max, dl.cantidad_periodo, dl.periodo , '' as cumplimiento from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = '" +  session['pais']  + "' and dl.mes_entrega = '" + mes_actual + "'  and dl.ano_entrega = " + ano_actual +  " and total_venta > 0 and corte <> 'Cierre' and da.idconsultor = '" + session['idconsultor'] + "' and da.aprobado <> '3' order by dl.idacuerdo,dl.corte"
    print(msql)
    cur.execute(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close() 

    arr = []

    for t in data:
        arr.append(t)    

    arr = np.array(arr)        

    return render_template('reportes/liberaciones_mes.html', data = arr, mes_actual = mes_actual)    

def actualizar_bandas():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    
    msql = "UPDATE dt_liberacion SET banda =  dt_acuerdo.banda FROM dt_acuerdo WHERE dt_acuerdo.idacuerdo = dt_liberacion.idacuerdo;"
    cur.execute(msql)
    msql = "UPDATE dt_liberacion SET banda_min =  0 ;"
    cur.execute(msql)
    msql = "UPDATE dt_liberacion SET banda_min =  dt_freegood.banda_min FROM dt_freegood WHERE dt_freegood.idfreegood = dt_liberacion.banda;"
    cur.execute(msql)
    msql = "UPDATE dt_liberacion SET banda_max =  0 ;"
    cur.execute(msql)
    msql = "UPDATE dt_liberacion SET banda_max =  dt_freegood.banda_max  FROM dt_freegood WHERE dt_freegood.idfreegood = dt_liberacion.banda;"
    cur.execute(msql)
    msql = "UPDATE dt_liberacion SET cantidad_periodo =  0 ;"
    cur.execute(msql)
    msql = "UPDATE dt_liberacion SET cantidad_periodo =  dt_acuerdo.cantidad_periodo FROM dt_acuerdo WHERE dt_acuerdo.idacuerdo = dt_liberacion.idacuerdo;"
    cur.execute(msql)
    conn.commit()
    cur.close()
    conn.close()


@app.route('/liberaciones_mes_exportar/', methods=['GET'])
def liberaciones_mes_exportar():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    ano_actual = datetime.now().strftime("%Y")
    mes_actual = datetime.now().strftime("%B")
    print(mes_actual)
    if session['nivel'] != 1 :
        msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, da.cantidad_periodo from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = '" +  session['pais']  + "' and dl.mes_entrega = '" + mes_actual + "'  and dl.ano_entrega = " + ano_actual +  " and total_venta >0 order by dl.idacuerdo,dl.corte"
    else:
        msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, da.cantidad_periodo from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = '" +  session['pais']  + "' and dl.mes_entrega = '" + mes_actual + "'  and dl.ano_entrega = " + ano_actual +  " and total_venta >0 and da.idconsultor = '" + session['idconsultor'] + "' order by dl.idacuerdo,dl.corte"    
    cur.execute(msql)
    df = cur.fetchall()
    arr = []
    # Recodifica la salida
    for d in df:
        t = list(d)
        arr.append(t)

    results = {}
    column = 0
    for d in cur.description:
        results[d[0]] = column
        column = column + 1

    now = datetime.now()
    date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    # Put it all to a data frame
    mnombre = 'Liberaciones_mes_'  + date_time  + '.xlsx'
    archivo = os.path.join(app.root_path, 'static/downloads/' , '', mnombre)
    sql_data = pd.DataFrame(arr)
    sql_data.columns =results
    sql_data.to_excel (archivo, index = False, header=True)

    cur.close()
    conn.close()

    return mnombre

@app.route('/aprobaciones_pendientes', methods=['GET'])
def aprobaciones_pendientes():
    auth = False
    authorized = [11, 12, 10]
    if session['nivel'] in authorized:
        auth = True
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "SELECT * from dt_acuerdo where pais = '" +  session['pais']  + "' and vigente = 1 and aprobado = 0 "
    cur.execute(msql)
    data = cur.fetchall() 
    cur.close()
    conn.close()  

    return render_template('reportes/aprobaciones_pendientes.html', data = data, auth = auth)

@app.route('/net_floor', methods=['GET'])
def net_floor():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "Select distinct producto, idproducto from dt_precios where pais = '" +  session['pais'] + "'"
    cur.execute(msql)
    data = cur.fetchall() 
    return render_template('reportes/net_floor.html', data = data)

@app.route('/crear_net_floor/<string:producto>', methods=['POST'])
def crear_net_floor(producto):

    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    campos = "idacuerdo,idconsultor,consultor,idcliente,cliente,ano_ini,mes_ini,ano_fin,mes_fin,duracion,cantidad_periodo,0 as Meta_Periodo, 0 as Unid_Totales, 0 as total_venta,fgs_sobre_cien, 0 as freegoods_Periodo, 0 as freegoods_Total,porc_descuento,0 as  Precio_Inicial, 0 as Inversion_Mes, 0 as Frecuencia"
    msql =  "SELECT * from dt_acuerdo where pais = '" +  session['pais']  + "' and vigente = 1 and idacuerdo = 'AR-20210002' "
    msql =  "SELECT " + campos + " from dt_acuerdo where pais = '" +  session['pais']  + "' and vigente = 1  "
    cur.execute(msql)
    data = cur.fetchall() 

    # Calcula el mes minimo y maximo de la proyeccion con los acuerdos vigentes x pais

    msql =  "SELECT  min(make_date(ano_ini, mes_ini, 1)) from dt_acuerdo where pais = '" +  session['pais']  + "' and vigente = 1 "
    cur.execute(msql)
    data1 = cur.fetchone()     
    mmin = data1[0]
    msql =  "SELECT  max(make_date(ano_fin, mes_fin, 1)) from dt_acuerdo where pais = '" +  session['pais']  + "' and vigente = 1 "
    cur.execute(msql)
    data2 = cur.fetchone()     
    mmax = data2[0]

    p = (mmax - mmin)

    diff = relativedelta(mmax, mmin)

    periodos = diff.months + diff.years * 12

    # Crea la matriz de periodos para ser llenada con los precios
    largo = (periodos + 1) * 2

    # Trae los precios de los periodos entre min y max
    msql = "Select * from dt_precios where idproducto = '" + producto + "' and pais = '" +  session['pais'] + "'"
    cur.execute(msql)
    datap = cur.fetchall() 
    dfp = pd.DataFrame(datap)

    u = np.empty([largo])


    # Creaa las 2 matrices de acuerdo + periodos de tiempo
    arr1 = []
    arr2 = []

    for t in data:
        arr1.append(t)    
        arr2.append(u)    

    df1 = np.array(arr1) 
    df2 = np.array(arr2) 


    d = pd.DataFrame(df1)
    e = pd.DataFrame(df2)

    result = pd.concat([d, e], axis=1, join='inner')
    
    arr = np.array(result)    

    # Inicia la matriz de periodos en cero
    mcol = 21 # Esta es la columna que se cambia del inicio
    for t in arr:
        for  i in range(0, largo ):
            t[mcol + i] = 0

    result = pd.DataFrame(arr)

    # Crea los nombres del la matriz dee acuerdo                                                            
    # cantidad_periodo = Meta mes y en el formulario Cant. Mnesual
                                                                                                                                                                                                                                                        
    nom_col = ['Idacuerdo','Id Consultor','Consultor','Id Cliente','Cliente','Año Inicio','Mes Inicio','Año Fin','Mes Fin','Duracion','Meta Mes','Meta Periodo', 'Unid. Totales','Total Venta','%Freegoods acuerdo','freegoods Periodo','freegoods Total','% Descuento','Precio con Descuento Inicial - ASP','Inversion Incial Estimada Mes','Frecuencia Liberaciones Fgs']
    mes_col = []
    pre_col = []
    pre_colb = []

    # Crea los nombres de los periodos
    for  i in range(0, largo):
        media = (largo / 2)
        if i < media:
            mes = mmin + relativedelta(months=i)
            mes = mes.strftime("%Y" + "-" + "%m")
            nom_col.append(mes)
            mes_col.append(mes)
            pre_col.append(0)  
            pre_colb.append(0)  
        else: 
            mes = mmin + relativedelta(months=(i-media))
            mes = mes.strftime("%Y" + "-" + "%m")
            nom_col.append(mes + "s")
            mes_col.append(mes)
            pre_col.append(0)  
            pre_colb.append(0)  

    # Pone los precios a los periodos
    l = 0
    for p in dfp.iterrows():
        mes = dfp.iloc[l,3]
        m = 0
        for q in mes_col:
            if mes == q:
                pre_col[m] = dfp.iloc[l,5]
                #pre_col[m] = (dfp.iloc[l,4] * 100) / 121
                pre_colb[m] = dfp.iloc[l,5]
                #pre_colb[m] = (dfp.iloc[l,4] * 100) / 121                
            m = m + 1
        l = l + 1
    # Llena el vector con el ultimo precio conocido
    m = 0
    for q in pre_col:
        if pre_col[m] == 0:
            pre_col[m] = pre_col[m-1]
            pre_colb[m] = pre_col[m-1]
        m = m + 1
    # Caso de blindaje AR
    if session['pais'] == 'AR':
        for  m in range(1, 6):
            pre_colb[m] = pre_colb[0]

    # Esta es la matriz final de trabajo 
    df = pd.DataFrame(result)
    df.columns =nom_col
    
    # Estandariza formatos para presentar el informe
    i = 0
    for row in df.iterrows():
        
        mes_inicio = datetime(df['Año Inicio'][i], df['Mes Inicio'][i], 1)  
        mes_fin = datetime(df['Año Fin'][i], df['Mes Fin'][i], 1)  
        mduracion = df['Duracion'][i]
        
        df['Mes Inicio'][i] = mes_inicio.strftime("%B")
        df['Mes Fin'][i] = mes_fin.strftime("%B")
        df['% Descuento'][i] = int(round(df['% Descuento'][i] * 100,0))

        if mduracion < 3:
            df['Meta Periodo'][i] = df['Meta Mes'][i] * mduracion
        else:
            df['Meta Periodo'][i] = df['Meta Mes'][i] * 3
        
        df['Unid. Totales'][i] =   df['Duracion'][i] *  df['Meta Mes'][i]
        
        df['freegoods Periodo'][i] = int(round(df['Meta Periodo'][i] * ( df['%Freegoods acuerdo'][i] / 100),0))
        df['freegoods Periodo'][i] = df['Meta Periodo'][i] * ( df['%Freegoods acuerdo'][i] / 100)
        df['freegoods Total'][i] =  int(round(df['Unid. Totales'][i] * ( df['%Freegoods acuerdo'][i] / 100),0))        
        df['Frecuencia Liberaciones Fgs'][i] = int(round(df['Duracion'][i] / 3,0))

        # Calcula la ventas de este acuerdo
        msql = "Select sum(cantidad) from dt_ventas where idacuerdo = '" +  df['Idacuerdo'][i] + "'"
        cur.execute(msql)
        ventas = cur.fetchone() 
        if ventas[0] == None:
            mventas = 0
        else:
            mventas = ventas[0]

        df['Total Venta'][i] = mventas


        # Establece el espacio temporal del acuerdo
        # Determina donde inicia el acuerdo
        for  j in range(0, largo):
            mes =  mes_inicio.strftime("%Y" + "-" + "%m")
            if mes == df.columns[mcol + j]:
                break
        
        # Marca el espacio temporal del acuerdo
        inicio = mcol + j 
        # Busca el precio de ese mes
        l = 0
        for p in dfp.iterrows():
            mprecio = dfp.iloc[l,5]        
            l = l + 1
        
        # Recorre el espacio temporal y pone el precio
        m = 1 # contador de corte trimestral
        n = 0
        for  k in range(inicio, inicio + mduracion):
            if df['Mes Inicio'][i] == 'marzo':
                mprecio = pre_colb[k - mcol ]
            else:
                mprecio = pre_col[k - mcol ]


            # En el primer calculo pone la inversion y precio inicial

            precio = round(mprecio - ( mprecio * (df['% Descuento'][i] /100) ),0)
            q = k + periodos + 1
            if (k == inicio):
                df['Precio con Descuento Inicial - ASP'][i] = precio
                df['Inversion Incial Estimada Mes'][i] = precio * df['Meta Mes'][i]

            if (m == 4 + n ):
                df.iloc[i, k] = round((precio * df['Meta Mes'][i]) / (df['Meta Mes'][i] + df['freegoods Periodo'][i] ),0)
                df.iloc[i, q] = precio * df['Meta Mes'][i]
                n = n + 3
            else:
                df.iloc[i, k] = precio
                df.iloc[i, q] = precio * df['Meta Mes'][i]
        
            m = m + 1

        i = i + 1

    # Crea los nombres de los periodos
    for  i in range(0, largo):
        media = (largo / 2)
        a = nom_col[mcol + i]
        if i < media:            
            df.rename(columns = {a:a + " avg Price"}, inplace = True)
        else: 
            df.rename(columns = {a:a + " avg Sales"}, inplace = True)
    
    mnombre = 'Calculo_NetFloor_' + producto + "_"  + datetime.now().strftime("%Y_%m_%d_%H_%M_%S")  + '.xlsx'
    archivo = os.path.join(app.root_path, 'static', 'downloads', mnombre )

    df.to_excel (archivo, index = False, header=True)   
             
    cur.close()
    conn.close() 
    return mnombre


@app.route('/busqueda_general/<string:pais>', methods=['GET'])
def busqueda_general(pais):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Busca los clientes del consultor
    msql =  "SELECT * FROM dt_cliente where pais = '" + pais + "'"
    cur.execute(msql)
    clientes = cur.fetchall() 
    
    return render_template('reportes/busqueda_general.html', clientes = clientes)

@app.route('/busqueda_generalxcliente', methods=['POST'])
def busqueda_generalxcliente():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    campos = request.form
    idcliente = campos["cliente"]
    # Busca los acuerdos de un cliente en la tabla principal o en la multiple
    msql =  "SELECT idacuerdo,idcliente FROM dt_acuerdo where idcliente = '" + idcliente + "' "
    msql = msql + " UNION "
    msql =  msql + " SELECT idacuerdo,idcliente FROM dt_cliente_multiple where idcliente = '" + idcliente + "' "
    cur.execute(msql)
    acuerdos = cur.fetchall()    
    ids = []
    for x in acuerdos:
        ids.append(x[0]) 
    print(ids)
    acuerdos = ', '.join(["'{}'".format(value) for value in ids])
    if len(acuerdos) > 0:
        msql = "SELECT * FROM dt_acuerdo where idacuerdo in (" + acuerdos + ") order by fecha_creacion"
    else:
        msql = "SELECT * FROM dt_acuerdo where idacuerdo = 'a'"
    cur.execute(msql)
    dt = cur.fetchall()    
    
    return render_template('reportes/sub_busqueda_general_tabla_acuerdos.html', dt = dt)

@app.route('/busqueda_generalxidacuerdo', methods=['POST'])
def busqueda_generalxidacuerdo():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    campos = request.form
    idacuerdo = campos["idacuerdo"]
    msql =  "SELECT * FROM dt_liberacion where idacuerdo = '" + idacuerdo + "' order by idliberacion "
    cur.execute(msql)
    dt = cur.fetchall()
    print(dt)
    return render_template('reportes/sub_busqueda_general_tabla_liberaciones.html', dt = dt)

@app.route('/busqueda_generalxventas', methods=['POST'])
def busqueda_generalxventas():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    campos = request.form
    idacuerdo = campos["idacuerdo"]
    msql =  "SELECT * FROM dt_ventas where idacuerdo = '" + idacuerdo + "' order by idventas "
    cur.execute(msql)
    dt = cur.fetchall()         
    return jsonify(dt)



@app.route('/constancia/<string:idacuerdo>')
def constancias(idacuerdo):
    path = os.path.join(app.config['UPLOAD_FOLDER'], idacuerdo)
    exists = os.path.exists(path)
    onlyfiles = []

    if exists:
        for f in listdir(path):
            el = []
            el.append(f)
            el.append(math.floor(os.path.getsize(join(path, f))/1000))
            el.append(datetime.fromtimestamp(os.path.getctime(join(path, f))).strftime("%m/%d/%Y, %H:%M:%S"))
            onlyfiles.append(el)


    else:
        onlyfiles = []
    print(onlyfiles)
    return render_template('reportes/constancia.html', idacuerdo=idacuerdo, file=onlyfiles)


@app.route('/constancia/subirconstancia/<string:idacuerdo>', methods=['GET', 'POST'])
def upload_file(idacuerdo):
    if request.method == 'POST':
        try:
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], idacuerdo)
                exists = os.path.exists(path)

                if not exists:
                    os.makedirs(path)
                file.save(os.path.join(path, filename))
                return redirect(url_for('constancias', idacuerdo=idacuerdo, name=filename))
        except Exception as e:
            print(e)
            return "Archivo no Seleccionado"
    else:
        return redirect(url_for('constancias', idacuerdo=idacuerdo))


@app.route('/download/<string:idacuerdo>/<string:name>')
def download_file(idacuerdo,name):
    path = os.path.join(app.config['UPLOAD_FOLDER'], idacuerdo)
    return send_from_directory(path,name)

@app.route('/borrar/download/<string:idacuerdo>/<string:name>')
def delete_download_file(idacuerdo,name):
    try:
        user= session['username']
        now = str(datetime.now())
        log = user + ' borro el archivo ' +  idacuerdo +"/" + name + ' Fecha:' + now + '.\n'
        path2 = os.path.join(app.root_path, 'log.txt')
        f = open(path2, 'a')
        f.write(log)
        path = os.path.join(app.config['UPLOAD_FOLDER'], idacuerdo,name)
        os.remove(path)
        return redirect(url_for('constancias', idacuerdo=idacuerdo))
    except Exception as e:
        print(e)
        return 'error :' + str(e)