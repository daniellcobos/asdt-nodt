# Programa de Acuerdos
from flask import Flask,  flash, jsonify, redirect, url_for, session, send_file, g
import psycopg2
from flask import render_template
from flask import request
import numpy as np
import pandas as pd
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import locale
import os
import sys
from xlsxwriter import Workbook
import smtplib, ssl
from email.mime.text import MIMEText
from webapp import app
from flask_cors import CORS
app.config.from_object('configuraciones.local')
db_connection_string = app.config["POSTGRESQL_CONNECTION"]

locale.setlocale(locale.LC_ALL, 'es_CO.utf8')
CORS(app, origins=["http://your-trusted-domain.com"])
from .utilidades import *

# Variable donde se activa la auditoria
# para hacer pruebas locales 0=No 1=Si
miauditoria = 0


@app.route('/misacuerdos', methods=['GET'])
def misacuerdos():
    # Verifica que los acuerdos esten vencidos
    acuerdos_sin_vigencia()
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Busca los usuarios y establece su nivel de seguridad
    msql = ""
    nivel = {
        -2: "SELECT * FROM dt_usuarios",
        -1: "SELECT * FROM dt_usuarios WHERE pais ='" + session['pais'] + "' and nivel = 1",
        10: "SELECT * FROM dt_usuarios WHERE pais ='" + session['pais'] + "' and nivel = 1",
        11: "SELECT * FROM dt_usuarios WHERE pais ='" + session['pais'] + "' and nivel = 1",
        12: "SELECT * FROM dt_usuarios WHERE pais ='" + session['pais'] + "' and nivel = 1",        
        1: "SELECT * FROM dt_usuarios WHERE idusuario = '" + session['idconsultor'] + "'" ,        
        2: "SELECT * FROM dt_usuarios WHERE pais ='" + session['pais'] + "' and nivel = 1"}        
    msql = nivel.get(session['nivel'], "Invalido")         
    cur.execute(msql)
    rows = cur.fetchall() 
    data = []         
    for row in rows:
        # Para cada usuario busca los acuerdos
        msql =  " SELECT count(idacuerdo) FROM 	dt_acuerdo INNER JOIN dt_usuarios ON idconsultor = idusuario WHERE idusuario = '" + row[0] + "';"
        cur.execute(msql)
        nacuerdos = cur.fetchone() 
        nacuerdos = nacuerdos[0]
        a0 = row[0]
        a1 = row[1]
        a2 = row[5]
        a3 = nacuerdos
        t = (a0,a1,a2,a3)
        data.append(t)   
    cur.close()
    conn.close()
    return render_template('acuerdos/misacuerdos.html', data = data)

@app.route('/acuerdosdetalle/<string:idconsultor>/<string:usuario>/<string:pais>', methods=['GET'])
def acuerdosdetalle(idconsultor, usuario, pais):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Obtiene fecha de hoy
    today = datetime.today()
    currentyear = today.year
    limityear = currentyear - 3
    print(limityear)
    # Busca acuerdos del usuario
    msql =  "SELECT * FROM dt_acuerdo where idconsultor = '" + idconsultor + "'  and date_part('year',fecha_creacion) > " + str(limityear)
    cur.execute(msql)
    data = cur.fetchall()   

    mdata = []
    for row in data:
        # Para cada acuerdo busca los clientes multiples
        msql = "SELECT COUNT(idcliente) from dt_cliente_multiple where idacuerdo = '" + row[0] + "'"
        cur.execute(msql)
        nclientes = cur.fetchone() 
        t1 = nclientes[0] 
        # Convierte a una lista y agrega la columna como nuevo elemento, aqui se guarda la suma de clientes adicionales x acuerdo
        row2 = list(row)
        row2.append(t1)
        # Para cada aucerdo busca Liberacion Detalle
        msql = "Select sum(total_fgs) from dt_liberacion where idacuerdo = '" + row[0] + "' and corte = '1'"
        cur.execute(msql)
        nliberacion = cur.fetchone() 
        t2 = nliberacion[0]
        # Para cada aucerdo busca Liberacion Cierre
        t3 = t2
        row2.append(t2)
        row2.append(t3)
        mdata.append(row2)

    cur.close()
    conn.close()
    return render_template('acuerdos/acuerdosdetalle.html', data = mdata, idconsultor = idconsultor ,usuario = usuario , pais = pais)

@app.route('/acuerdosdetalleantiguos/<string:idconsultor>/<string:usuario>/<string:pais>', methods=['GET'])
def acuerdosdetalleantiguos(idconsultor, usuario, pais):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Obtiene fecha de hoy
    today = datetime.today()
    currentyear = today.year
    limityear = currentyear - 3
    print(limityear)
    # Busca acuerdos del usuario
    msql =  "SELECT * FROM dt_acuerdo where idconsultor = '" + idconsultor + "'  and date_part('year',fecha_creacion) <= " + str(limityear)
    cur.execute(msql)
    data = cur.fetchall()

    mdata = []
    for row in data:
        # Para cada acuerdo busca los clientes multiples
        msql = "SELECT COUNT(idcliente) from dt_cliente_multiple where idacuerdo = '" + row[0] + "'"
        #cur.execute(msql)
        nclientes = cur.fetchone()
        t1 = 'nd'
        # Convierte a una lista y agrega la columna como nuevo elemento, aqui se guarda la suma de clientes adicionales x acuerdo
        row2 = list(row)
        row2.append(t1)
        # Para cada aucerdo busca Liberacion Detalle
        #msql = "Select sum(total_fgs) from dt_liberacion where idacuerdo = '" + row[0] + "' and corte = '1'"
        #cur.execute(msql)
        nliberacion = cur.fetchone()
        t2 = 'nd'
        # Para cada aucerdo busca Liberacion Cierre
        t3 = t2
        row2.append(t2)
        row2.append(t3)
        mdata.append(row2)

    cur.close()
    conn.close()
    return render_template('acuerdos/acuerdosdetalle.html', data = mdata, idconsultor = idconsultor ,usuario = usuario , pais = pais)






@app.route('/acuerdosdetalle_exportar/<string:idconsultor>', methods=['GET'])
def acuerdosdetalle_exportar(idconsultor):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "SELECT * FROM dt_acuerdo where idconsultor = '" + idconsultor + "'"
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
    mnombre = 'Acuerdos_'  + date_time  + '.xlsx'
    archivo = os.path.join(app.root_path, 'static/downloads/' , '', mnombre)
    sql_data = pd.DataFrame(arr)
    sql_data.columns =results
    sql_data.to_excel (archivo, index = False, header=True)

    cur.close()
    conn.close()

    return mnombre


@app.route('/acuerdossubdetalle/<string:idacuerdo>', methods=['GET'])
def acuerdossubdetalle(idacuerdo):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()




    msql = "select max(idperiodo) from dt_ventas where pais = '" + session['pais'] + "'"
    cur.execute(msql)
    mperiodo = cur.fetchone()
    mperiodo = mperiodo[0]
    msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux,dl.harmonyca, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, dl.banda, dl.banda_min, dl.banda_max, dl.cantidad_periodo, dl.periodo ,  da.porc_descuento , '' as cumplimiento from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where da.idacuerdo = '" + idacuerdo + "' order by dl.idacuerdo,dl.corte"
    cur.execute(msql)
    data = cur.fetchall()
    arr = []

    for t in data:
        arr.append(t)

    arr = np.array(arr)

    for t in arr:
        for i, x in enumerate(t):
            if x == None:
                t[i] = ''
        t[36] = float(t[36])
        p = str(t[35])
        p = p[0:6]
        p = int(p)

        if (int(t[4]) < 4) or (t[5] == 'Cierre'):
            t[34] = ""
        elif (p > mperiodo):
            t[34] = ""
        elif (int(t[32]) * 3) > int(t[12]):
            t[34] = "Incumple"
        elif (int(t[32]) * 3) <= int(t[12]) and (int(t[12]) <= int(t[33]) * 3):
            t[34] = "Cumple"
        elif (int(t[12]) > int(t[33]) * 3):
            t[34] = "Excede"

    altarr = []
    for row in arr:
        reorderedRoW = [row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[33], row[9],
                        row[12], row[10]
            , row[11], row[22], round(row[36] * 100, 2), row[13], row[14], row[15], row[16], row[17], row[18], row[19],
                        row[20], row[21], row[23], row[24]
            , row[25], row[26], row[27], row[28], row[29], row[30], row[31], row[32], row[33], row[34]]

        altarr.append(reorderedRoW)

    cur.close()
    conn.close()
    return render_template('reportes/liberaciones_total.html', data1 = altarr)


@app.route('/acuerdos_add/<string:idconsultor>/<string:usuario>/<string:pais>', methods=['GET'])
def acuerdos_add(idconsultor, usuario, pais):
    # Verifica que los acuerdos esten vencidos
    acuerdos_sin_vigencia()
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Busca los clientes del consultor
    # msql =  "SELECT * FROM dt_cliente where id_consultor = '" + idconsultor + "'"
    msql =  "SELECT * FROM dt_cliente where pais = '" + pais + "'"
    cur.execute(msql)
    clientes = cur.fetchall() 
    # Busca los maximos id de acuerdos por año para incrementarlo
    #msql = "select ano_ini, MAX(SUBSTR(cast (idacuerdo as text), 4,9)) as registro   from dt_acuerdo where pais = '" + pais + "' GROUP BY ano_ini  order by registro desc"
    msql = "select MAX(SUBSTR(cast (idacuerdo as text), 4,9)) as registro   from dt_acuerdo where pais = '" + pais + "' order by registro desc"
    print(msql)
    cur.execute(msql)
    id_max = cur.fetchall() 
    # Envia la tabla maestra de acuerdos

    # Envia la tabla maestra de acuerdos segun nivel
    if session["nivel"] == -1:
        msql = "select distinct plazo, idplazo from dt_freegood where pais = '" + pais + "'  and usar = 1 order by idplazo"
        cur.execute(msql)
        plazos = cur.fetchall()
        msql = "select * from dt_freegood where pais = '" + pais + "' and usar = 1 order by idbanda "
        cur.execute(msql)
        freegoods = cur.fetchall()
        # range of freegoods
        idrange =str(tuple(["246"]+[ str(x) for x in range(274,286)]  + ["296","297","335"] + [ str(x) for x in range(336,351)] ))
        msql = "select distinct plazo, idplazo from dt_freegood where pais = '" + pais + "'  and idfreegood in " + idrange + " order by idplazo"
        cur.execute(msql)
        plazos2 = cur.fetchall()
        plazos = plazos + plazos2
        msql = "select * from dt_freegood where pais = '" + pais + "' and idfreegood in " + idrange + " order by idplazo,banda"
        print(msql)
        cur.execute(msql)
        freegoods2 = cur.fetchall()
        freegoods = freegoods + freegoods2

    else:
        msql = "select distinct plazo, idplazo from dt_freegood where pais = '" + pais + "'  and usar = 1 order by idplazo"
        cur.execute(msql)
        plazos = cur.fetchall()
        msql = "select * from dt_freegood where pais = '" + pais + "' and usar = 1 order by idbanda "
        cur.execute(msql)
        freegoods = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('acuerdos/acuerdos_add.html', idconsultor = idconsultor, usuario = usuario, pais = pais, clientes = clientes, id_max = id_max, freegoods = freegoods, plazos = plazos)


@app.route('/acuerdos_guardar', methods=['POST'])
def acuerdos_guardar():
    idacuerdo = request.form.getlist('row[idacuerdo]')
    idconsultor= request.form.getlist('row[idconsultor]')
    consultor= request.form.getlist('row[consultor]')
    idcliente= request.form.getlist('row[idcliente]')
    cliente= request.form.getlist('row[cliente]')
    mes_ini= request.form.getlist('row[mes_ini]')
    ano_ini= request.form.getlist('row[ano_ini]')
    tipo_acuerdo= request.form.getlist('row[tipo_acuerdo]')
    cantidad_periodo= request.form.getlist('row[cantidad_periodo]')
    duracion= request.form.getlist('row[duracion]')
    unidades_total= request.form.getlist('row[unidades_total]')
    banda= request.form.getlist('row[banda]')
    freegoods= request.form.getlist('row[freegoods]')
    mes_fin= request.form.getlist('row[mes_fin]')
    ano_fin= request.form.getlist('row[ano_fin]')
    vigente= request.form.getlist('row[vigente]')
    pais= request.form.getlist('row[pais]')
    fecha_creacion= request.form.getlist('row[fecha_creacion]')
    num_entregas= request.form.getlist('row[num_entregas]')
    num_entregas_cierre= request.form.getlist('row[num_entregas_cierre]')
    anulado= request.form.getlist('row[anulado]')
    entrega_x_porcentaje= request.form.getlist('row[entrega_x_porcentaje]')
    porc_piso_entrega= request.form.getlist('row[porc_piso_entrega]')
    porc_cumplimiento= request.form.getlist('row[porc_cumplimiento]')
    fgs_sobre_cien= request.form.getlist('row[fgs_sobre_cien]')
    porc_descuento= request.form.getlist('row[porc_descuento]')
    aprobado= request.form.getlist('row[aprobado]')

    mensaje = ""
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()    

    # Regla de verificacion de acuerdos vigentes / Activos

    msql = " select idcliente, idacuerdo from dt_acuerdo"
    msql = msql + " union all "
    msql = msql + " select idcliente, idacuerdo from dt_cliente_multiple"
    msql = msql + " order by idacuerdo asc"
    cur.execute(msql)
    df = cur.fetchall()
    #revisa acuerdos vigentes en la tabla de acuerdos
    msql = "SELECT idcliente, idacuerdo FROM dt_acuerdo where idcliente = %s and vigente = 1 union " \
           "select idcliente, idacuerdo from dt_acuerdo where idacuerdo in (select idacuerdo from dt_cliente_multiple where idcliente = %s) and vigente = 1 order by idacuerdo asc"
    cur.execute(msql, (idcliente[0], idcliente[0]))
    result=cur.fetchone()

    if result != None:
        mensaje = "Este cliente ya tiene acuerdos vigentes:" + str(result)
        print(mensaje)
        return mensaje

    msql = "INSERT INTO dt_acuerdo "
    msql = msql + "(idacuerdo, idconsultor, consultor, idcliente, cliente, mes_ini, ano_ini, tipo_acuerdo, cantidad_periodo, duracion, unidades_total, banda, freegoods, mes_fin, ano_fin, vigente, pais, num_entregas, num_entregas_cierre, anulado, entrega_x_porcentaje, porc_piso_entrega, porc_cumplimiento, fgs_sobre_cien, porc_descuento, aprobado)"
    msql = msql + " VALUES ('"
    msql = msql +  (idacuerdo[0]) + "','"  + (idconsultor[0]) + "','"  + (consultor[0]) + "','"  + (idcliente[0]) + "','"  + (cliente[0]) + "','"  + (mes_ini[0]) + "','"  + (ano_ini[0]) + "','"  + (tipo_acuerdo[0]) + "','"  + (cantidad_periodo[0]) + "','"  + (duracion[0]) + "','"  + (unidades_total[0]) + "','"  + (banda[0]) + "','"  + (freegoods[0]) + "','"  + (mes_fin[0]) + "','"  + (ano_fin[0]) + "','"  + (vigente[0]) + "','"  + (pais[0]) + "','"  + (num_entregas[0]) + "','"  + (num_entregas_cierre[0]) + "','"  + (anulado[0]) + "','"  + (entrega_x_porcentaje[0]) + "','"  + (porc_piso_entrega[0]) + "','"  + (porc_cumplimiento[0]) + "','"  + (fgs_sobre_cien[0]) + "',"  + (porc_descuento[0]) + ",'"  + (aprobado[0]) + "')"
    print(msql)
    try:   
        cur.execute(msql)
        conn.commit()
        mensaje = 'Acuerdo Guardado'
        # Envia el correo de aprobacion al nivel 10 = Gerente de Ventas del pais
        msql = "select * from dt_usuarios where nivel = 10 and pais ='"  + session['pais'] + "'"
        cur.execute(msql)
        registro = cur.fetchone()
        if miauditoria == 1:
            enviar_correo("Acuerdo Creado. Solicitud de Aprobacion de nivel 1", idacuerdo[0],consultor[0],cliente[0], registro[2])
        crear_liberacion(idacuerdo[0], idconsultor[0], consultor[0], idcliente[0], cliente[0], mes_ini[0], ano_ini[0], tipo_acuerdo[0], cantidad_periodo[0], duracion[0], unidades_total[0], banda[0], freegoods[0], mes_fin[0], ano_fin[0], vigente[0], pais[0], num_entregas[0], num_entregas_cierre[0], anulado[0], entrega_x_porcentaje[0], porc_piso_entrega[0], porc_cumplimiento[0], fgs_sobre_cien[0], porc_descuento[0], aprobado[0])
    except Exception as e:
         mensaje = 'Error al guardar ' + str(e)
    cur.close()
    conn.close()    

    return mensaje

@app.route('/acuerdos_editar/<string:idacuerdo>', methods=['GET','POST'])
def acuerdos_editar(idacuerdo):
    pais = session['pais']
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Busca los clientes del consultor
    # msql =  "SELECT * FROM dt_cliente where id_consultor = '" + idconsultor + "'"
    msql =  "SELECT * FROM dt_cliente where pais = '" + session['pais'] + "'"
    cur.execute(msql)
    clientes = cur.fetchall() 
    # Busca los consultores
    msql =  "SELECT idusuario,usuario FROM dt_usuarios where nivel = 1 and pais = '" + session['pais'] + "'"
    cur.execute(msql)
    consultores = cur.fetchall()

    # Busca el registro a editar
    msql = "select *  from dt_acuerdo where idacuerdo = '" + idacuerdo + "'"
    cur.execute(msql)
    registro = cur.fetchone()
    if session["nivel"] == -1:
        msql = "select distinct plazo, idplazo from dt_freegood where pais = '" + pais + "'  and usar = 1 order by idplazo"
        cur.execute(msql)
        plazos = cur.fetchall()
        msql = "select * from dt_freegood where pais = '" + pais + "' and usar = 1 order by idbanda "
        cur.execute(msql)
        freegoods = cur.fetchall()
        # range of freegoods
        idrange = str(tuple(
            ["246"] + [str(x) for x in range(274, 286)] + ["296", "297", "335"] + [str(x) for x in range(336, 351)]))
        msql = "select distinct plazo, idplazo from dt_freegood where pais = '" + pais + "'  and idfreegood in " + idrange + " order by idplazo"
        cur.execute(msql)
        plazos2 = cur.fetchall()
        plazos = plazos + plazos2
        msql = "select * from dt_freegood where pais = '" + pais + "' and idfreegood in " + idrange + " order by idplazo,banda"
        print(msql)
        cur.execute(msql)
        freegoods2 = cur.fetchall()
        freegoods = freegoods + freegoods2

    else:
        msql = "select distinct plazo, idplazo from dt_freegood where pais = '" + pais + "'  and usar = 1 order by idplazo"
        cur.execute(msql)
        plazos = cur.fetchall()
        msql = "select * from dt_freegood where pais = '" + pais + "' and usar = 1 order by idbanda "
        cur.execute(msql)
        freegoods = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('acuerdos/acuerdos_edit.html',  consultores = consultores, clientes = clientes, registro = registro, freegoods = freegoods, plazos = plazos)


@app.route('/acuerdos_editar_salvar', methods=['POST'])
def acuerdos_editar_salvar():
    idacuerdo = request.form.getlist('row[idacuerdo]')
    idconsultor= request.form.getlist('row[idconsultor]')
    consultor= request.form.getlist('row[consultor]')
    idcliente= request.form.getlist('row[idcliente]')
    cliente= request.form.getlist('row[cliente]')
    mes_ini= request.form.getlist('row[mes_ini]')
    ano_ini= request.form.getlist('row[ano_ini]')
    tipo_acuerdo= request.form.getlist('row[tipo_acuerdo]')
    cantidad_periodo= request.form.getlist('row[cantidad_periodo]')
    duracion= request.form.getlist('row[duracion]')
    unidades_total= request.form.getlist('row[unidades_total]')
    banda= request.form.getlist('row[banda]')
    freegoods= request.form.getlist('row[freegoods]')
    mes_fin= request.form.getlist('row[mes_fin]')
    ano_fin= request.form.getlist('row[ano_fin]')
    vigente= request.form.getlist('row[vigente]')
    pais= request.form.getlist('row[pais]')
    fecha_creacion= request.form.getlist('row[fecha_creacion]')
    num_entregas= request.form.getlist('row[num_entregas]')
    num_entregas_cierre= request.form.getlist('row[num_entregas_cierre]')
    anulado= request.form.getlist('row[anulado]')
    entrega_x_porcentaje= request.form.getlist('row[entrega_x_porcentaje]')
    porc_piso_entrega= request.form.getlist('row[porc_piso_entrega]')
    porc_cumplimiento= request.form.getlist('row[porc_cumplimiento]')
    fgs_sobre_cien= request.form.getlist('row[fgs_sobre_cien]')
    porc_descuento= request.form.getlist('row[porc_descuento]')
    aprobado= request.form.getlist('row[aprobado]')

    aprobacion10= request.form.getlist('row[aprobacion10]')
    aprobacion11= request.form.getlist('row[aprobacion11]')
    aprobacion12= request.form.getlist('row[aprobacion12]')

    msql = "UPDATE dt_acuerdo SET "
    #vigente, pais, num_entregas, num_entregas_cierre, anulado, entrega_x_porcentaje, porc_piso_entrega, porc_cumplimiento, fgs_sobre_cien, porc_descuento, aprobado)"
    msql = msql + "idconsultor = '" + idconsultor[0] + "', consultor ='" + consultor[0] + "', "
    msql = msql + "idcliente = '" + idcliente[0] + "', cliente = '" + cliente[0] + "', mes_ini = " + mes_ini[0] + ", ano_ini = " + ano_ini [0] + ",  cantidad_periodo = " + cantidad_periodo [0] + ", duracion = " + duracion[0] + ", unidades_total = " + unidades_total[0] + ", banda =" + banda[0] + ", freegoods = "  + freegoods[0] + ", mes_fin = "  + mes_fin[0] + ", ano_fin = " + ano_fin[0] + " , porc_descuento = " + porc_descuento[0] + " , fgs_sobre_cien = " + fgs_sobre_cien[0] + " , apro1 = '" + aprobacion10[0] + "', apro2 = '" + aprobacion11[0] + "', apro3 = '"  + aprobacion12[0] + "'"
    msql = msql + " where idacuerdo = '" + idacuerdo[0] + "'"

    mensaje = ""
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Acuerdo Guardado'
        # Crea las liberaciones nuevamente
        crear_liberacion(idacuerdo[0], idconsultor[0], consultor[0], idcliente[0], cliente[0], mes_ini[0], ano_ini[0], tipo_acuerdo[0], cantidad_periodo[0], duracion[0], unidades_total[0], banda[0], freegoods[0], mes_fin[0], ano_fin[0], vigente[0], pais[0], num_entregas[0], num_entregas_cierre[0], anulado[0], entrega_x_porcentaje[0], porc_piso_entrega[0], porc_cumplimiento[0], fgs_sobre_cien[0], porc_descuento[0], aprobado[0])        
        # Extrae los aprobadores por pais y nivel
        msql = "select * from dt_usuarios where nivel = 10 and pais ='"  + session['pais'] + "'"
        cur.execute(msql)
        aprobador1 = cur.fetchone()        
        msql = "select * from dt_usuarios where nivel = 11 and pais ='"  + session['pais'] + "'"
        cur.execute(msql)
        aprobador2 = cur.fetchone()
        msql = "select * from dt_usuarios where nivel = 12 and pais ='"  + session['pais'] + "'"
        cur.execute(msql)
        aprobador3 = cur.fetchone()


        if (aprobacion10[0] == '1'):
            # Envia el correo de aprobacion al nivel 11 = Gerente de Ventas del pais
            if miauditoria == 1:
                enviar_correo("Acuerdo Editado. Solicitud de Aprobacion de nivel 2 ", idacuerdo[0],consultor[0],cliente[0], aprobador2[2])

        if (aprobacion10[0] == '1' and aprobacion11[0] == '1'):
            # Envia el correo de aprobacion al nivel 12 = Area de Finanzas
            if miauditoria == 1:
                enviar_correo("Acuerdo Editado. Solicitud de Aprobacion de nivel 3 ", idacuerdo[0],consultor[0],cliente[0], aprobador3[2])   
        # Si el acuerdo cumple el flujo queda aprobado
        if (aprobacion10[0] == '1' and aprobacion11[0] == '1' and aprobacion12[0] == '1'):
            msql = "UPDATE dt_acuerdo SET aprobado = 1 "
            msql = msql + " where idacuerdo = '" + idacuerdo[0] + "'"
            cur.execute(msql)
            conn.commit()
        # Si el acuerdo no cumple no es aprobado
        if (aprobacion10[0] == '2' or aprobacion11[0] == '2' or aprobacion12[0] == '2'):
            msql = "UPDATE dt_acuerdo SET aprobado = 2 "
            msql = msql + " where idacuerdo = '" + idacuerdo[0] + "'"
            cur.execute(msql)
            conn.commit()
            # Envia el correo a todos los aprobadores
            if miauditoria == 1:
                enviar_correo("Acuerdo Editado. Correo informativo de Acuerdo Rechazado ", idacuerdo[0],consultor[0],cliente[0], aprobador1[2])
                enviar_correo("Acuerdo Editado. Correo informativo de Acuerdo Rechazado ", idacuerdo[0],consultor[0],cliente[0], aprobador2[2])
                enviar_correo("Acuerdo Editado. Correo informativo de Acuerdo Rechazado ", idacuerdo[0],consultor[0],cliente[0], aprobador3[2])


    except Exception as e:
         mensaje = 'Error al guardar ' + str(e)
    cur.close()
    conn.close()    

    return mensaje


@app.route('/acuerdos_borrar/<string:idconsultor>/<string:usuario>/<string:pais>/<string:idacuerdo>', methods=['GET','POST'])
def acuerdos_borrar(idconsultor, usuario, pais,idacuerdo):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Borra el acuerdo
    msql = "DELETE from dt_acuerdo where idacuerdo = '" + idacuerdo + "'"
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Acuerdo Borrado'
    except Exception as e:
         mensaje = 'Error al borrar ' + str(e)
    # Borra los clientes multimples
    msql = "DELETE from dt_cliente_multiple where idacuerdo = '" + idacuerdo + "'"
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Acuerdo Borrado'
    except Exception as e:
         mensaje = 'Error al borrar ' + str(e)
    # Borra las liberaciones
    msql = "DELETE from dt_liberacion where idacuerdo = '" + idacuerdo + "'"
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Acuerdo Borrado'
    except Exception as e:
         mensaje = 'Error al borrar ' + str(e)


    cur.close()
    conn.close()  
    usuario = usuario.replace(" ", "%20")
    path = '/acuerdosdetalle/' + idconsultor + '/' + usuario + '/' + pais
    return redirect(path)
    
@app.route('/cliente_adicional/<string:idconsultor>/<string:usuario>/<string:pais>/<string:idacuerdo>', methods=['GET','POST'])
def cliente_adicional(idconsultor, usuario, pais,idacuerdo):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Busca los clientes actuales del acuerdo
    msql =  "SELECT idcliente, cliente FROM dt_acuerdo where idacuerdo = '" + idacuerdo + "'"
    cur.execute(msql)
    acuerdo_clientes = cur.fetchall() 
    msql =  "SELECT idcliente, cliente, fecha FROM dt_cliente_multiple where idacuerdo = '" + idacuerdo + "'"
    cur.execute(msql)    
    acuerdo_clientes_add = cur.fetchall() 
    # Busca los clientes del consultor
    # msql =  "SELECT * FROM dt_cliente where id_consultor = '" + idconsultor + "'"
    msql =  "SELECT * FROM dt_cliente where pais = '" + pais + "'"
    cur.execute(msql)
    clientes = cur.fetchall() 
    cur.close()
    conn.close()    
    return render_template('acuerdos/cliente_adicional.html', idconsultor = idconsultor, usuario = usuario, pais = pais, idacuerdo = idacuerdo , acuerdo_clientes =acuerdo_clientes , clientes = clientes, acuerdo_clientes_add = acuerdo_clientes_add)

@app.route('/cliente_adicional_guardar/<string:idconsultor>/<string:usuario>/<string:pais>/<string:idacuerdo>/<string:idcliente>/<string:cliente>', methods=['POST'])
def cliente_adicional_guardar(idconsultor, usuario, pais,idacuerdo,idcliente,cliente):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "SELECT idcliente, idacuerdo FROM dt_acuerdo where idcliente = %s and vigente = 1 union " \
           "select idcliente, idacuerdo from dt_acuerdo where idacuerdo in (select idacuerdo from dt_cliente_multiple where idcliente = %s) and vigente = 1 order by idacuerdo asc"
    cur.execute(msql,(idcliente,idcliente))
    result=cur.fetchone()
    if result != None:
        mensaje = "Este cliente ya tiene acuerdos vigentes: " + str(result[1])
        return mensaje

    print('sigio')

    msql = "INSERT INTO dt_cliente_multiple(idacuerdo, cliente, idcliente,vigente) 	VALUES ('" + idacuerdo + "','" + cliente + "','" + idcliente + "','" + str(1) +"')"
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'cliente Guardado'
    except Exception as e:
         mensaje = 'Error al guardar ' + str(e)
    cur.close()
    conn.close()      
    return mensaje

@app.route('/clientem_borrar/<string:idconsultor>/<string:usuario>/<string:pais>/<string:idacuerdo>/<string:idcliente>', methods=['GET','POST'])
def clientem_borrar(idconsultor,usuario,pais,idacuerdo,idcliente):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "DELETE from dt_cliente_multiple where idacuerdo = '" + idacuerdo + "' and idcliente = '" + idcliente + "'"
    try:    
        cur.execute(msql)
        conn.commit()
        mensaje = 'Cliente eliminado'
    except Exception as e:
         mensaje = 'Error al borrar ' + str(e)
    cur.close()
    conn.close()       
    path = '/cliente_adicional/' + idconsultor + '/' + usuario + '/' + pais + '/' + idacuerdo
    return redirect(path)


@app.route('/todosacuerdos/', methods=['GET'])
@app.route('/todosacuerdos/1', methods=['GET'])
def todosacuerdos():
    # Verifica que los acuerdos esten vencidos
    acuerdos_sin_vigencia()
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Busca acuerdos del usuario
    if session['nivel'] == 1:
        msql =  "SELECT * FROM dt_acuerdo where pais = '" + session['pais'] + "' and idconsultor = '" + session['idconsultor'] + "'"
    else:
        msql =  "SELECT * FROM dt_acuerdo where pais = '" + session['pais'] + "'"
        #msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, da.cantidad_periodo from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = '" +  session['pais']  + "' order by dl.idacuerdo,dl.corte"
    cur.execute(msql)
    data = cur.fetchall()
    archivequantity = []
    for r in data:
        path = os.path.join(app.config['UPLOAD_FOLDER'], r[0])
        try:
            archivequantity.append(len(os.listdir(path)))
        except:
            archivequantity.append(0)
    # precios
    msql = "SELECT * FROM dt_precios where pais = %s order by periodo desc"
    cur.execute(msql, (session['pais'],))
    precios = []
    for e in cur.fetchall():
        precios.append(list(e))
    msql = "Select distinct producto from dt_precios where pais = %s"
    cur.execute(msql, (session['pais'],))
    nombres = []
    for e in cur.fetchall():
        nombres.append(list(e))
    cur.close()
    conn.close()

    return render_template('acuerdos/todosacuerdos.html', data=data, precios=precios, nombres=nombres,
                           aq=archivequantity)


@app.route('/todosacuerdos_edit/', methods=['POST'])
def todosacuerdos_edit():    
    x = request.form.getlist('mregs[]')
    y = request.form.getlist('mapro')
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    for row in x:
        msql = "UPDATE dt_acuerdo SET aprobado = " + y[0] + " where idacuerdo = '" + row + "'"
        print(msql)
        try:    
            cur.execute(msql)     
            if (y[0] == str(3)):
                msql = "UPDATE dt_acuerdo SET vigente = 0 where idacuerdo = '" + row + "'"
                cur.execute(msql)  
        except Exception as e:
            mensaje = 'Error al actualizar ' + str(e)
    conn.commit()
    cur.close()
    conn.close()       
    return "Acuerdos Actualizados"

@app.route('/exportara/', methods=['GET']) 
def exportara():
    file1 = open("myfile.txt","w")
    L = ["This is Delhi \n","This is Paris \n","This is London \n"] 
    file1.write("Hello \n")
    file1.writelines(L)
    file1.close() #to change file access modes
    i = 1

    return "ok"


@app.route('/todosacuerdos_exportar/', methods=['GET'])
def todosacuerdos_exportar():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    cur.execute("Select * from dt_acuerdo where pais = '" + session['pais'] + "'")
    df = cur.fetchall()
    arr = []
    # Recodifica la salida
    for d in df:
        t = list(d)
        t[26] = fnt_aprobado(t[26] )
        t[27] = fnt_aprobado(t[27] )
        t[28] = fnt_aprobado(t[28] )
        t[29] = fnt_aprobado(t[29] )
        print(t)
        arr.append(t)

    results = {}
    column = 0
    for d in cur.description:
        results[d[0]] = column
        column = column + 1

    now = datetime.now()
    date_time = now.strftime("%Y_%m_%d_%H_%M_%S")
    # Put it all to a data frame
    mnombre = 'Acuerdos_'  + date_time  + '.xlsx'
    archivo = os.path.join(app.root_path, 'static/downloads/' , '', mnombre)
    sql_data = pd.DataFrame(arr)
    sql_data.columns =results
    sql_data.to_excel (archivo, index = False, header=True)

    cur.close()
    conn.close()

    return mnombre


def enviar_correo(mestado,idacuerdo,consultor,cliente,mquien):

    # Si es el administrador no envia los correos
    if session['nivel'] < 0:
        return

    # Evniar a:
    receiver_email = mquien
    # creates SMTP session
    s = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
    # start TLS for security
    s.starttls()
    # Authentication
    s.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    # message to be sent
    message = '<html><body> <b>Hay un Acuerdo para su aprobacion: <a href="https://allergan.easynet.me/acuerdos_editar/' + idacuerdo + '">' + str(idacuerdo) + '</a> ' + str(mestado) + '</b> </body></html>' 
    #message = '<html><body> <b>Hay un Acuerdo para su aprobacion: <a href="http://localhost:5000/acuerdos_editar/' + idacuerdo + '">' + str(idacuerdo) + '</a> ' + str(mestado) + '</b> </body></html>' 

    my_email = MIMEText(message, "html")
    my_email["Subject"] = "Accion requerida para Acuerdos Allergan.easynet.me "
    # sending the mail
    # No envia el correo.
    s.sendmail(app.config['MAIL_USERNAME'], receiver_email, my_email.as_string())
    # terminating the session
    s.quit()

    return "ok"       


def fnt_sino(valor):
    t = 'ND'
    if valor == 1:
        t = "Si"
    if valor == 2:
        t = "No"
    return t

def fnt_aprobado(valor):
    t = 'ND'
    if valor == 1:
        t = "Aprobado"
    if valor == 2:
        t = "Rechazado"
    return t   
def crear_liberacion(idacuerdo, idconsultor, consultor, idcliente, cliente, mes_ini, ano_ini, tipo_acuerdo, cantidad_periodo, duracion, unidades_total, banda, freegoods, mes_fin, ano_fin, vigente, pais, num_entregas, num_entregas_cierre, anulado, entrega_x_porcentaje, porc_piso_entrega, porc_cumplimiento, fgs_sobre_cien, porc_descuento, aprobado):
    
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    pais = session['pais'] 
    fgs_sobre_cien = float(fgs_sobre_cien)
    duracion = float(duracion)
    ano_ini = int(ano_ini)
    mes_ini = int(mes_ini)
    ano_fin = int(ano_fin)
    mes_fin = int(mes_fin)  
    cantidad_periodo = int(cantidad_periodo)


    # Borra la anterior liberacion si existe para no crear duplicados
    msql =  "DELETE from dt_liberacion where idacuerdo = '" + str(idacuerdo) + "'"

    cur.execute(msql)
    conn.commit()

    periodo = '0'
    porcentaje = fgs_sobre_cien / 100

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

    # Calcula los cortes si duracion = 1
    if duracion == 1:
        f1 = date(ano_ini, mes_ini, 1)
        f2 = date(ano_fin, mes_fin, 1)
        f3 = f2  + relativedelta(months=1)
        v = [0,0,0,0,0,0,0,0,0]
        periodo = f1.strftime("%Y") + f1.strftime("%m") + f2.strftime("%Y") + f2.strftime("%m")
        ano_entrega = f3.year
        t = [f1.strftime("%B") + "-" + f2.strftime("%B"), f3.strftime("%B"), ano_entrega, v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8]]  
        meta = cantidad_periodo * duracion
        teorico = (meta) * (fgs_sobre_cien / 100)
        cumplimiento = 0
        insertar_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion,  "1", t[0], t[1], t[2], meta , fgs_sobre_cien, teorico, cumplimiento,  t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3])
        insertar_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion,  "Cierre", t[0], t[1], t[2], meta , fgs_sobre_cien, teorico, cumplimiento,  t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3])


    # Calcula los cortes si duracion = 2
    if duracion == 2:
        f1 = date(ano_ini, mes_ini, 1)
        f2 = date(ano_fin, mes_fin, 1)
        f3 = f2  + relativedelta(months=1)
        print(f1,f2,f3,"E")
        v = [0,0,0,0,0,0,0,0,0]
        periodo = f1.strftime("%Y") + f1.strftime("%m") + f2.strftime("%Y") + f2.strftime("%m")
        ano_entrega = f3.year            
        t = [f1.strftime("%B") + "-" + f2.strftime("%B"), f3.strftime("%B"), ano_entrega, v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8]]  
        meta = cantidad_periodo * duracion
        teorico = (meta) * (fgs_sobre_cien / 100)
        cumplimiento = 0
        insertar_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion,  "1", t[0], t[1], t[2], meta , fgs_sobre_cien, teorico, cumplimiento,  t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3])
        insertar_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion,  "Cierre", t[0], t[1], t[2], meta , fgs_sobre_cien, teorico, cumplimiento,  t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3])

    if duracion == 4:
        f1 = date(ano_ini, mes_ini, 1)
        f2 = date(ano_fin, mes_fin, 1)
        f3 = f1 + relativedelta(months=1)
        f4 = f2 - relativedelta(months=1)
        f5 = f2 + relativedelta(months=1)
        v = [0,0,0,0,0,0,0,0,0]
        periodo = f1.strftime("%Y") + f1.strftime("%m") + f3.strftime("%Y") + f3.strftime("%m")
        periodo2 =  f4.strftime("%Y") + f4.strftime("%m") + f2.strftime("%Y") + f2.strftime("%m")
        periodo3 =  f1.strftime("%Y") + f1.strftime("%m") + f2.strftime("%Y") + f2.strftime("%m")
        ano_entrega1 = f3.year
        ano_entrega2 = f5.year
        t = [f1.strftime("%B") + "-" + f3.strftime("%B"), f4.strftime("%B"), ano_entrega1, v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8]]
        t2 = [f4.strftime("%B") + "-" + f2.strftime("%B"), f5.strftime("%B"), ano_entrega2, v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8]]
        t3 = [f1.strftime("%B") + "-" + f2.strftime("%B"), f5.strftime("%B"), ano_entrega2, v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8]]
        meta = cantidad_periodo * duracion
        teorico = (meta) * (fgs_sobre_cien / 100)
        cumplimiento = 0
        insertar_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion,  "1", t[0], t[1], t[2], meta , fgs_sobre_cien, teorico, cumplimiento,  t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3])
        insertar_liberacion(periodo2, pais, idacuerdo, consultor, idcliente, cliente, duracion, "2", t2[0], t2[1], t2[2],meta, fgs_sobre_cien, teorico, cumplimiento, t2[3], t2[4], t2[5], t2[6], t2[7], t2[8], t2[9],t2[10], t2[11], idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3])
        insertar_liberacion(periodo3, pais, idacuerdo, consultor, idcliente, cliente, duracion,  "Cierre", t3[0], t3[1], t3[2], meta , fgs_sobre_cien, teorico, cumplimiento,  t3[3], t3[4], t3[5], t3[6], t3[7], t3[8], t3[9], t3[10], t3[11], idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3])

        


    # Calcula los cortes si duracion > 2
    elif duracion > 2:
        # Calcula los cortes
        filas = round(duracion / 3) 
        # Calcula los meses de los cortes
        arr = []
        
        inicio = date(ano_ini, mes_ini, 1)
        for i in range(0, filas ):            
            f1 = inicio  
            f2 = f1  + relativedelta(months=2)
            f3 = f2  + relativedelta(months=1)
            ano_entrega = f3.year            
            inicio = f3            
            v = [0,0,0,0,0,0,0,0,0]   
            periodo = f1.strftime("%Y") + f1.strftime("%m") + f2.strftime("%Y") + f2.strftime("%m")         
            t = [f1.strftime("%B") + "-" + f2.strftime("%B"), f3.strftime("%B"), ano_entrega, v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8], periodo]
            arr.append(t)


        for i in range(0, filas):
            meta = cantidad_periodo * 3
            teorico = (cantidad_periodo * 3) * (fgs_sobre_cien / 100)
            cumplimiento = 0
            periodo = arr[i][12]
            insertar_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion, i+1, arr[i][0], arr[i][1], arr[i][2], meta , fgs_sobre_cien, teorico, cumplimiento, arr[i][3], arr[i][4], arr[i][5], arr[i][6], arr[i][7], arr[i][8], arr[i][9], arr[i][10], arr[i][11], idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3])

        # Calcula el cierre del acuerdo
        f1 = date(ano_ini, mes_ini, 1)
        f2 = date(ano_fin, mes_fin, 1)
        f3 = f2  + relativedelta(months=1)
        v = [0,0,0,0,0,0,0,0,0]
        periodo = f1.strftime("%Y") + f1.strftime("%m") + f2.strftime("%Y") + f2.strftime("%m")
        ano_entrega = f3.year            
        t = [f1.strftime("%B") + "-" + f2.strftime("%B"), f3.strftime("%B"), ano_entrega, v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8]]  
        meta = cantidad_periodo * duracion
        teorico = (meta) * (fgs_sobre_cien / 100)
        cumplimiento = 0
        insertar_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion,  "Cierre", t[0], t[1], t[2], meta , fgs_sobre_cien, teorico, cumplimiento,  t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], idc[0], cl[0], idc[1], cl[1], idc[2], cl[2], idc[3], cl[3])

    cur.close()
    conn.close() 

    print("Termino", idacuerdo)

    return 'ok'

def insertar_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion , corte, detalle_periodo , mes_entrega , ano_entrega, meta_corte, fgs_sobre_cien, fgs_teoricos, total_venta, botox, ultra, ultra_plus, volbella, volift, volite, voluma, volux, total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "INSERT INTO dt_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion , corte, detalle_periodo, mes_entrega, ano_entrega, meta_corte, fgs_sobre_cien, fgs_teoricos, total_venta, botox, ultra, ultra_plus, volbella, volift, volite, voluma, volux, total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4) "
    msql = msql + " VALUES (" + str(periodo) + ", '" + str(pais) + "'"
    msql = msql + ", '" + str(idacuerdo) +"', '" + str(consultor) +"', '" + str(idcliente) +"', '" + str(cliente) +"', " + str(duracion) +", '" + str(corte) + "','" + str(detalle_periodo) + "', '" + str(mes_entrega) + "', " + str(ano_entrega) + ", " + str(meta_corte) + ", " + str(fgs_sobre_cien) + ", " + str(fgs_teoricos)
    msql = msql + ", "  + str(total_venta) +", "+ str(botox) +", "+ str(ultra) +", "+ str(ultra_plus) +", "+ str(volbella) +", "+ str(volift) +", "+ str(volite) +", "+ str(voluma) +", "+ str(volux) +", "+ str(total_fgs)
    msql = msql + ", '" + str(idcliente1) +"', '"+ str(cliente1) +"', '"+ str(idcliente2) +"', '"+ str(cliente2) +"', '"+ str(idcliente3) + "', '"+ str(cliente3) +"', '"+ str(idcliente4) + "', '"+ str(cliente4) +"'); "
    print(msql)
    cur.execute(msql)
    conn.commit()
    cur.close()
    conn.close()    
    return "ok"     

@app.route('/Recalcular_Sistema/', methods=['GET'])
def Recalcular_Sistema():
    #mensaje = borrar_liberaciones()
    #mensaje = crear_liberaciones()    
    #mensaje = ventasxacuerdos()
    mensaje = consolidar()
    return mensaje

@app.route('/borrar_liberaciones/', methods=['POST'])
def borrar_liberaciones():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "Delete FROM dt_liberacion where pais = %s and dt_liberacion.idacuerdo in (select dt_acuerdo.idacuerdo from dt_acuerdo where vigente=1)"
    #msql = "Delete FROM dt_liberacion where pais = %s and idacuerdo =  'CO-20220249'"
    cur.execute(msql,(session['pais'],))
    conn.commit()
    cur.close()
    conn.close()    
    return "Liberaciones actuales borradas."


@app.route('/borrar_liberaciones_totales/', methods=['POST'])
def borrar_liberaciones_totales():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "DELETE FROM dt_liberacion where pais = '" +  session['pais'] + "'"
    cur.execute(msql)
    conn.commit()
    cur.close()
    conn.close()
    return "Liberaciones actuales borradas."

def borrar_liberaciones_acuerdo(idacuerdor):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "Delete FROM dt_liberacion where pais = %s and idacuerdo =  '"+idacuerdor+"'"
    cur.execute(msql,(session['pais'],))
    conn.commit()
    cur.close()
    conn.close()



@app.route('/crear_liberaciones/', methods=['POST'])
def crear_liberaciones():

    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()  
    msql =  "SELECT * from dt_acuerdo where pais = '" +  session['pais']  + "' and vigente = 1 "
    #msql = "SELECT * from dt_acuerdo where pais = '" +  session['pais']  + "' and idacuerdo = 'CO-20220249'"
    rows = pd.read_sql_query(msql,conn)
    for i in rows.index:      
        idacuerdo = rows['idacuerdo'][i]
        crear_liberacion(rows['idacuerdo'][i], rows['idconsultor'][i] , rows['consultor'][i], rows['idcliente'][i], rows['cliente'][i], rows['mes_ini'][i], rows['ano_ini'][i], rows['tipo_acuerdo'][i], rows['cantidad_periodo'][i], rows['duracion'][i], rows['unidades_total'][i], rows['banda'][i], rows['freegoods'][i], rows['mes_fin'][i], rows['ano_fin'][i], rows['vigente'][i], rows['pais'][i], rows['num_entregas'][i], rows['num_entregas_cierre'][i], rows['anulado'][i], rows['entrega_x_porcentaje'][i], rows['porc_piso_entrega'][i] , rows['porc_cumplimiento'][i] , rows['fgs_sobre_cien'][i]  , rows['porc_descuento'][i] , rows['aprobado'][i])

    cur.close()
    conn.close() 

    return "Liberaciones actuales creadas."


@app.route('/crear_liberaciones_totales/', methods=['POST'])
def crear_liberaciones_totales():

    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "SELECT * from dt_acuerdo where pais = '" +  session['pais']  + "'"
    rows = pd.read_sql_query(msql,conn)
    for i in rows.index:
        idacuerdo = rows['idacuerdo'][i]
        crear_liberacion(rows['idacuerdo'][i], rows['idconsultor'][i] , rows['consultor'][i], rows['idcliente'][i], rows['cliente'][i], rows['mes_ini'][i], rows['ano_ini'][i], rows['tipo_acuerdo'][i], rows['cantidad_periodo'][i], rows['duracion'][i], rows['unidades_total'][i], rows['banda'][i], rows['freegoods'][i], rows['mes_fin'][i], rows['ano_fin'][i], rows['vigente'][i], rows['pais'][i], rows['num_entregas'][i], rows['num_entregas_cierre'][i], rows['anulado'][i], rows['entrega_x_porcentaje'][i], rows['porc_piso_entrega'][i] , rows['porc_cumplimiento'][i] , rows['fgs_sobre_cien'][i]  , rows['porc_descuento'][i] , rows['aprobado'][i])

    cur.close()
    conn.close()

    return "Liberaciones actuales creadas."

def crear_liberaciones_acuerdo(idacuerdor):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "SELECT * from dt_acuerdo where pais = '" +  session['pais']  + "' and idacuerdo = '"+idacuerdor+"'"
    print(msql)
    rows = pd.read_sql_query(msql,conn)
    for i in rows.index:
        idacuerdo = rows['idacuerdo'][i]
        crear_liberacion(rows['idacuerdo'][i], rows['idconsultor'][i] , rows['consultor'][i], rows['idcliente'][i], rows['cliente'][i], rows['mes_ini'][i], rows['ano_ini'][i], rows['tipo_acuerdo'][i], rows['cantidad_periodo'][i], rows['duracion'][i], rows['unidades_total'][i], rows['banda'][i], rows['freegoods'][i], rows['mes_fin'][i], rows['ano_fin'][i], rows['vigente'][i], rows['pais'][i], rows['num_entregas'][i], rows['num_entregas_cierre'][i], rows['anulado'][i], rows['entrega_x_porcentaje'][i], rows['porc_piso_entrega'][i] , rows['porc_cumplimiento'][i] , rows['fgs_sobre_cien'][i]  , rows['porc_descuento'][i] , rows['aprobado'][i])

    cur.close()
    conn.close()






def insertar_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion , corte, detalle_periodo , mes_entrega , ano_entrega, meta_corte, fgs_sobre_cien, fgs_teoricos, cumplimiento, botox, ultra, ultra_plus, volbella, volift, volite, voluma, volux, total_venta, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "INSERT INTO dt_liberacion(periodo, pais, idacuerdo, consultor, idcliente, cliente, duracion , corte, detalle_periodo, mes_entrega, ano_entrega, meta_corte, fgs_sobre_cien, fgs_teoricos, total_venta, botox, ultra, ultra_plus, volbella, volift, volite, voluma, volux, total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4) "
    msql = msql + " VALUES (" + str(periodo) + ", '" + str(pais) + "'"
    msql = msql + ", '" + str(idacuerdo) +"', '" + str(consultor) +"', '" + str(idcliente) +"', '" + str(cliente) +"', " + str(duracion) +", '" + str(corte) + "','" + str(detalle_periodo) + "', '" + str(mes_entrega) + "', " + str(ano_entrega) + ", " + str(meta_corte) + ", " + str(fgs_sobre_cien) + ", " + str(fgs_teoricos)
    msql = msql + ", "  + str(cumplimiento) +", "+ str(botox) +", "+ str(ultra) +", "+ str(ultra_plus) +", "+ str(volbella) +", "+ str(volift) +", "+ str(volite) +", "+ str(voluma) +", "+ str(volux) +", "+ str(total_venta)
    msql = msql + ", '" + str(idcliente1) +"', '"+ str(cliente1) +"', '"+ str(idcliente2) +"', '"+ str(cliente2) +"', '"+ str(idcliente3) + "', '"+ str(cliente3) +"', '"+ str(idcliente4) + "', '"+ str(cliente4) +"'); "
    #print(msql)
    cur.execute(msql)
    conn.commit()
    cur.close()
    conn.close()    
    return "ok" 


@app.route('/reprocesar/', methods=['POST'])
def reprocesar_acuerdo():
    idacuerdo = request.form['idacuerdo']
    borrar_liberaciones_acuerdo(idacuerdo)
    crear_liberaciones_acuerdo(idacuerdo)
    consolidar_acuerdo(idacuerdo)
    return redirect("/liberaciones_total")


@app.route('/ventasxacuerdos/', methods=['GET'])
def ventasxacuerdos():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = " select idcliente, idacuerdo from dt_acuerdo"
    msql = msql + " union all "
    msql = msql + " select upper(idcliente), idacuerdo from dt_cliente_multiple"
    msql = msql + " order by idacuerdo asc"
    print(msql)

    #msql = "select periodo,substring(cast(periodo as varchar),1,6) as ini, substring(cast(periodo as varchar),7,12) as fin,idacuerdo,corte, idcliente from dt_liberacion where idacuerdo = 'AR-20210001' order by idacuerdo,corte"

    # Para el idcliente
    msql = "select periodo,substring(cast(periodo as varchar),1,6) as ini, substring(cast(periodo as varchar),7,12) as fin,idacuerdo,corte, idcliente from dt_liberacion order by idacuerdo,corte"
    cur.execute(msql)    
    df = cur.fetchall()

    # acuerdo en col 3 y cliente en col 5
    i = 0
    for row in df:
        msql = "UPDATE dt_ventas SET idacuerdo = '" + row[3] + "'  where sap_id = '" + row[5].upper() + "' and idperiodo >=" + row[1] + " and idperiodo <= "+ row[2]
        cur.execute(msql)
        i = i + 1

    # Para el idcliente1
    msql = "select periodo,substring(cast(periodo as varchar),1,6) as ini, substring(cast(periodo as varchar),7,12) as fin,idacuerdo,corte, idcliente1 from dt_liberacion where idcliente1 <> '' order by idacuerdo,corte"
    cur.execute(msql)    
    df = cur.fetchall()

    # acuerdo en col 3 y cliente en col 5
    i = 0
    for row in df:
        msql = "UPDATE dt_ventas SET idacuerdo = '" + row[3] + "'  where sap_id = '" + row[5].upper() + "' and idperiodo >=" + row[1] + " and idperiodo <= "+ row[2]
        cur.execute(msql)
        i = i + 1

    # Para el idcliente2
    msql = "select periodo,substring(cast(periodo as varchar),1,6) as ini, substring(cast(periodo as varchar),7,12) as fin,idacuerdo,corte, idcliente2 from dt_liberacion where idcliente2 <> '' order by idacuerdo,corte"
    cur.execute(msql)    
    df = cur.fetchall()

    # acuerdo en col 3 y cliente en col 5
    i = 0
    for row in df:
        msql = "UPDATE dt_ventas SET idacuerdo = '" + row[3] + "'  where sap_id = '" + row[5].upper() + "' and idperiodo >=" + row[1] + " and idperiodo <= "+ row[2]
        cur.execute(msql)
        i = i + 1

    # Para el idcliente3
    msql = "select periodo,substring(cast(periodo as varchar),1,6) as ini, substring(cast(periodo as varchar),7,12) as fin,idacuerdo,corte, idcliente3 from dt_liberacion where idcliente3 <> '' order by idacuerdo,corte"
    cur.execute(msql)    
    df = cur.fetchall()

    # acuerdo en col 3 y cliente en col 5
    i = 0
    for row in df:
        msql = "UPDATE dt_ventas SET idacuerdo = '" + row[3] + "'  where sap_id = '" + row[5].upper() + "' and idperiodo >=" + row[1] + " and idperiodo <= "+ row[2]
        cur.execute(msql)
        i = i + 1

    # Para el idcliente4
    msql = "select periodo,substring(cast(periodo as varchar),1,6) as ini, substring(cast(periodo as varchar),7,12) as fin,idacuerdo,corte, idcliente4 from dt_liberacion where idcliente4 <> '' order by idacuerdo,corte"
    cur.execute(msql)    
    df = cur.fetchall()

    # acuerdo en col 3 y cliente en col 5
    i = 0
    for row in df:
        msql = "UPDATE dt_ventas SET idacuerdo = '" + row[3] + "'  where sap_id = '" + row[5].upper() + "' and idperiodo >=" + row[1] + " and idperiodo <= "+ row[2]
        cur.execute(msql)
        i = i + 1




    conn.commit()
    cur.close()
    conn.close()   
    return "Clientes por Acuerdos por Ventas"    

# Esta es la rutina que asigna los fg 2022.06.01
@app.route('/consolidar/', methods=['GET','POST'])
def consolidar():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()

    #ventasxacuerdos()

    # Extrae los acuerdos que tienen ventas y estan vigentes
    pais =  session['pais']    
    msql = "SELECT DISTINCT dt_ventas.idacuerdo from dt_ventas  WHERE PAIS = %s and dt_ventas.idacuerdo <> ''" \
          " and dt_ventas.idacuerdo in (select dt_acuerdo.idacuerdo from dt_acuerdo where vigente = 1)"
    #msql = "SELECT DISTINCT idacuerdo from dt_ventas WHERE PAIS = '"+ pais +"' and idacuerdo =  'CO-20220008' "
    cur.execute(msql, (pais,))
    df = cur.fetchall()
    print(df)
    i = 0
    for row in df:
        msql = "SELECT * from dt_acuerdo where idacuerdo = '" + str(row[0]) + "' and PAIS = '"+ pais +"' order by idacuerdo"
        #msql = "SELECT * from dt_acuerdo where idacuerdo = '" + str(row[0]) + "' and PAIS = '"+ pais +"' and idacuerdo =  'CO-20220249' order by idacuerdo"
        cur.execute(msql)
        print(msql)
        dt = cur.fetchone()
        idacuerdo = row[0]
        i = i + 1
        totalizar_ventas(idacuerdo)  
    cur.close()
    conn.close()     
    return 'Consolidacion completa!!!'  

def consolidar_acuerdo(idacuerdor):
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()

    #ventasxacuerdos()

    # Extrae los acuerdos que tienen ventas y estan vigentes
    pais =  session['pais']
    msql = "SELECT DISTINCT idacuerdo from dt_ventas WHERE PAIS = '" + pais +"' and idacuerdo =  '"+ idacuerdor+"' "
    cur.execute(msql, (pais,))
    df = cur.fetchall()
    print(df)
    i = 0
    for row in df:
        msql = "SELECT * from dt_acuerdo where idacuerdo = '" + str(row[0]) + "' and PAIS = '"+ pais +"' order by idacuerdo"
        #msql = "SELECT * from dt_acuerdo where idacuerdo = '" + str(row[0]) + "' and PAIS = '"+ pais +"' and idacuerdo =  'CO-20220249' order by idacuerdo"
        cur.execute(msql)
        print(msql)
        dt = cur.fetchone()
        idacuerdo = row[0]
        i = i + 1
        totalizar_ventas(idacuerdo)
    cur.close()
    conn.close()


@app.route('/consolidar_total/', methods=['GET','POST'])
def consolidar_total():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()

    #ventasxacuerdos()

    # Extrae los acuerdos que tienen ventas
    pais =  session['pais']
    msql = "SELECT DISTINCT idacuerdo from dt_ventas WHERE PAIS = '"+ pais +"' and idacuerdo <> ''"
    cur.execute(msql)
    df = cur.fetchall()
    #print(df)
    i = 0
    for row in df:
        msql = "SELECT * from dt_acuerdo where idacuerdo = '" + str(row[0]) + "' and PAIS = '"+ pais +"' order by idacuerdo"
        cur.execute(msql)
        dt = cur.fetchone()
        idacuerdo = row[0]
        i = i + 1
        totalizar_ventas(idacuerdo)
    cur.close()
    conn.close()
    return 'Consolidacion completa!!!'


@app.route('/totalizar_ventas/<string:idacuerdo>', methods=['GET','POST'])
def totalizar_ventas(idacuerdo):
    archivolog = os.path.join(app.root_path, 'static/', "uploadlog.txt")
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()    
    # Trae los datos de liberacion
    msql = "SELECT * from dt_liberacion where idacuerdo = '" + idacuerdo + "' order by corte "
    #print(msql)
    cur.execute(msql)
    cortes = cur.fetchall()
    # Ultimo corte
    lastcorte = len(cortes) - 1
    mtotal = 0
    # Acomulado por corte
    mtotalac= 0
    # Totaliza por cada corte pero el cierre es la sumatoria de los cortes precedentes
    for row in cortes:

        periodo = str(row[1])
        porcentaje = row[13] / 100
        #print(porcentaje)
        f1 = periodo[0:6]
        f2 = periodo[6:12]
        bigger = 0
        corte = row[8]
        if (corte != 'Cierre'):
            # Calcula las ventas del periodo
            msql = "SELECT producto, sum(cantidad) from dt_ventas WHERE idperiodo BETWEEN " + str(f1) + " AND " + str(f2) + " AND idacuerdo = '" + idacuerdo + "' and PRODUCTO <> 'LATISSE' and PRODUCTO <> 'LATISSE 3ML' GROUP BY producto;"
            #print(msql)
            cur.execute(msql)
            productos = cur.fetchall()
            q1 = 0
            q2 = 0
            q3 = 0
            q4 = 0
            q5 = 0
            q6 = 0
            q7 = 0
            q8 = 0
            q9 = 0
            p1 = 0
            p2 = 0
            p3 = 0
            p4 = 0
            p5 = 0
            p6 = 0
            p7 = 0
            p8 = 0
            p9 = 0
            mtotal = 0
            #checkeo de total
            checkeo = 0
            for p in productos:
                if p[0] != "BOTOX 50U" or p[0] != "0":
                    checkeo = checkeo + p[1]

                #if p[0] == "BOTOX" or p[0] == "BOTOX 100U" or p[0] == "BOTOX 50U" or p[0] == "BOTOX 1 Vial (100 Units) A":
                if p[0] == "BOTOX" or p[0] == "BOTOX 100U" or p[0] == "BOTOX 1 Vial (100 Units) A":
                    q1 = q1 + round(p[1])
                if p[0] == "ULTRA":
                    q2 = round(p[1])
                if p[0] == "ULTRA PLUS":
                    q3 = round(p[1])
                if p[0] == "VOLBELLA":
                    q4 = round(p[1])
                if p[0] == "VOLIFT":
                    q5 = round(p[1])
                if p[0] == "VOLITE":
                    q6 = round(p[1])
                if p[0] == "VOLUMA":
                    q7 = round(p[1])
                if p[0] == "VOLUX":
                    q8 = round(p[1])
                if p[0] == "HARMONYCA":
                    q9 = round(p[1])
            
            mventa = round((q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8+q9))
            #print("cierre q",q1 , q2 , q3 , q4 , q5 , q6 , q7 , q8,q9)
            #
            if mventa != checkeo:
                print("mventa vs checkeo",mventa, checkeo)
                with open(archivolog, "a+") as log:

                    log.write("Revisar "+ idacuerdo+" corte: "+corte+"\n")
            mtotal = round((q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8+q9)*porcentaje)
            #print("porcentaje",porcentaje,"mventa",mventa,"mtotal",mtotal)


            mtotalac = mtotalac + ((q1 + q2 + q3 + q4 + q5 + q6 + q7 + q8+q9) * porcentaje)
            if mventa > 0:
                pventas = {"botox": (q1 / mventa) * mtotal, "ultra": (q2 / mventa) * mtotal,
                           "ultra_plus": (q3 / mventa) * mtotal, "volbella": (q4 / mventa) * mtotal,
                           "volift": (q5 / mventa) * mtotal, "volite": (q6 / mventa) * mtotal,
                           "voluma": (q7 / mventa) * mtotal, "volux": (q8 / mventa) * mtotal,
                           "harmonyca": (q9 / mventa) * mtotal
                           }

                pventas = sorted(pventas.items(), key=lambda item: item[1])
                bigtest = sorted(pventas, key=lambda item: item[1], reverse=True)





                p1 = round(((q1/mventa)* mtotal) + 0.01)
                p2 = round(((q2/mventa)*mtotal) + 0.01)
                p3 = round(((q3/mventa)*mtotal) + 0.01)
                p4 = round(((q4/mventa)*mtotal) + 0.01)
                p5 = round(((q5/mventa)*mtotal) + 0.01)
                p6 = round(((q6/mventa)*mtotal) + 0.01)
                p7 = round(((q7/mventa)*mtotal) + 0.01)
                p8 = round(((q8/mventa)*mtotal) + 0.01)
                p9 = round(((q9/mventa) * mtotal) + 0.01)

                #caso especial, 1 freegood pero ningun producto per se tiene mas de una unidad
                if mtotal == 1:
                    proporciones = [(i / mventa) * mtotal for i in [q1, q2, q3, q4, q5, q6, q7, q8, q9]]
                    proporcional = any(i > 0.5 for i in proporciones)
                    if not proporcional:
                        product = bigtest[0][0]
                        if product == "botox":
                            p1 = 1
                        if product == "ultra":
                            p2 = 1
                        if product == "ultra_plus":
                            p3 = 1
                        if product == "volbella":
                            p4 = 1
                        if product == "volift":
                            p5 = 1
                        if product == "volite":
                            p6 = 1
                        if product == "voluma":
                            p7 = 1
                        if product == "volux":
                            p8 = 1
                        if product == "harmonyca":
                            p9 = 1


                #print("bigtest",bigtest)
                #print("ventas",pventas)
                for venta in pventas:
                    if venta[1] < 0.5:
                        pass
                    else:
                        lower = venta[0]
                        break
                mtotal2 = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
                #print("freep",p1, p2, p3, p4, p5, p6, p7, p8, p9)
                #print("mtotal",mtotal,"mtotal2",mtotal2)




                if (mtotal < mtotal2):
                    if lower == "botox":
                        p1 = p1 - 1
                    if lower == "ultra":
                        p2 = p2 - 1
                    if lower == "ultra_plus":
                        p3 = p3 - 1
                    if lower == "volbella":
                        p4 = p4 - 1
                    if lower == "volift":
                        p5 = p5 - 1
                    if lower == "volite":
                        p6 = p6 - 1
                    if lower == "voluma":
                        p7 = p7 - 1
                    if lower == "volux":
                        p8 = p8 - 1
                    if lower == "harmonyca":
                        p9 = p9 - 1
                    mtotal = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
                else:
                    mtotal = mtotal2
                    #print(p1, p2, p3, p4, p5, p6, p7, p8)
            else:
                p1 = 0
                p2 = 0
                p3 = 0
                p4 = 0
                p5 = 0
                p6 = 0
                p7 = 0
                p8 = 0
                p9 = 0



            #print(porcentaje)



            if p1 <0:
                p1 = 0
            if p2 <0:
                p2 = 0
            if p3 <0:
                p3 = 0
            if p4 <0:
                p4 = 0
            if p5 <0:
                p5 = 0
            if p6 <0:
                p6 = 0
            if p7 <0:
                p7 = 0
            if p8 <0:
                p8 = 0
            if p9 <0:
                p9 = 0
            print("free",p1, p2, p3, p4, p5, p6, p7, p8, p9)


            msql = "UPDATE dt_liberacion SET total_venta = " + str(mventa)  + ", botox= " + str(p1) + ", ultra= " + str(p2) + ", ultra_plus= " + str(p3) + ", volbella= " + str(p4) + ", volift= " + str(p5) + ", volite= " + str(p6) + ", voluma= " + str(p7) + ", volux= " + str(p8) + ",harmonyca= " + str(p9) + ", total_fgs= " + str(mtotal) + " WHERE idacuerdo = '" +  idacuerdo + "' and periodo = " + str(periodo)
            #print(msql)
            cur.execute(msql)
            conn.commit()
        else:
            # Aqui se hace el cierre como la suma de todo el acuerdo
            msql = "select sum(fgs_teoricos),sum(total_venta),sum(botox),sum(ultra),sum(ultra_plus),sum(volbella),sum(volift),sum(volite),sum(voluma),sum(volux),sum(harmonyca),sum(total_fgs) from dt_liberacion where idacuerdo = '" + idacuerdo + "' and corte <> 'Cierre'"
            #print(msql)
            cur.execute(msql)
            cierre = cur.fetchone()

            mteoricos = cierre[0]
            mventa = cierre[1]
            p1 = cierre[2]
            p2 = cierre[3]
            p3 = cierre[4]
            p4 = cierre[5]
            p5 = cierre[6]
            p6 = cierre[7]
            p7 = cierre[8]
            p8 = cierre[9]
            p9 = cierre[10]
            if p9 == None:
                p9 = 0

            mtotal = p1 + p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            #print("totalc",p1,p2,p3,p4,p5,p6,p7,p8,p9)
            #print("mtotal",mtotal)
            #Obtiene el producto mas vendido
            bigger = {"botox": p1, "ultra": p2 ,"ultra_plus": p3, "volbella": p4, "volift": p5, "volite": p6, "voluma": p7, "volux": p8, "harmonyca": p9}
            print("BIGGER",bigger)
            biggerone = max(bigger, key=bigger.get)
            print(biggerone)
            msql = "UPDATE dt_liberacion SET fgs_teoricos = " + str(mteoricos) +  ", total_venta = " + str(mventa)  + ", botox= " + str(p1) + ", ultra= " + str(p2) + ", ultra_plus= " + str(p3) + ", volbella= " + str(p4) + ", volift= " + str(p5) + ", volite= " + str(p6) + ", voluma= " + str(p7) + ", volux= " + str(p8) + ", harmonyca= " + str(p9) + ", total_fgs= " + str(mtotal) + " WHERE idacuerdo = '" +  idacuerdo + "' and corte = 'Cierre' "

            #print(msql)
            #log temporal

            cur.execute(msql)
            conn.commit()
        
    mtotalac = round(mtotalac)
    print("mtotalac",mtotalac)
    #Redondeo vs Suma en cierre
    if mtotalac > mtotal:
        msql = "UPDATE dt_liberacion set total_fgs= total_fgs+1 WHERE idacuerdo = %s and corte = %s"
        cur.execute(msql, ( idacuerdo, str(lastcorte)))
        msql = "UPDATE dt_liberacion set {field}= {field}+1 WHERE idacuerdo = %s and corte = %s".format(field=biggerone)
        #print(msql,idacuerdo,lastcorte)
        cur.execute(msql, (idacuerdo, str(lastcorte)))
        conn.commit()
        # El Cierre tambien quedaba incompleto
        msql = "UPDATE dt_liberacion set total_fgs= total_fgs+1 WHERE idacuerdo = %s and corte = %s"
        #print(msql,idacuerdo,cierre)
        cur.execute(msql, (idacuerdo, 'Cierre'))
        msql = "UPDATE dt_liberacion set {field}= {field}+1 WHERE idacuerdo = %s and corte = %s".format(field=biggerone)
        #print(msql, idacuerdo, lastcorte)
        cur.execute(msql, (idacuerdo, 'Cierre'))
        conn.commit()

    cur.close()
    conn.close()       
    return "Liberacion Actualizada!!!"

@app.route('/endpoint/acuerdos/<string:pais>', methods=['GET'])
def api_acuerdos(pais):
    # Verifica que los acuerdos esten vencidos
    print(request.environ)
    if request.environ['REMOTE_ADDR'] == '127.0.0.1':
        acuerdos_sin_vigencia()
        conn = psycopg2.connect(db_connection_string)
        cur = conn.cursor()
        # Busca acuerdos del usuario
        if session['nivel'] == 1:
            return jsonify({'mensaje':'no autorizado'})
        else:
            msql = "SELECT * FROM dt_acuerdo where pais = '" + pais + "'"
            # msql =  "SELECT dl.idacuerdo, dl.consultor, dl.idcliente, dl.cliente, dl.duracion , dl.corte, dl.detalle_periodo, dl.mes_entrega, dl.ano_entrega, dl.meta_corte, dl.fgs_sobre_cien, dl.fgs_teoricos, dl.total_venta, dl.botox, dl.ultra, dl.ultra_plus, dl.volbella, dl.volift, dl.volite, dl.voluma, dl.volux, dl.total_fgs, idcliente1, cliente1, idcliente2, cliente2, idcliente3, cliente3, idcliente4, cliente4, da.cantidad_periodo from dt_liberacion dl inner join dt_acuerdo da  ON dl.idacuerdo = da.idacuerdo where dl.pais = '" +  session['pais']  + "' order by dl.idacuerdo,dl.corte"
        cur.execute(msql)
        data = cur.fetchall()
        dataarr = []
        for d in data:
            datadict = {
                "idacuerdo" : d[0],
                "idconsultor": d[1],
                "consultor": d[2],
                "idcliente": d[3],
                "cliente": d[4],
                "mesini":d[5],
                "anoini":d[6],
                "tipoacuerdo":d[7],
                "cantidad_periodo":d[8],
                "duracion": d[9],
                "unidades_total": d[10],
                "banda": d[11],
                "freegoods":d[12],
                "mes_fin":d[13],
                "ano_fin":d[14],
                "vigente":d[15],
                "pais":d[16],
                "fecha_creacion":d[17],
            }
            dataarr.append(datadict)
        print(datadict)
        archivequantity = []
        for r in data:
            path = os.path.join(app.config['UPLOAD_FOLDER'], r[0])
            try:
                archivequantity.append(len(os.listdir(path)))
            except:
                archivequantity.append(0)
        # precios
        msql = "SELECT * FROM dt_precios where pais = %s order by periodo desc"
        cur.execute(msql, (session['pais'],))
        precios = []
        for e in cur.fetchall():
            precios.append(list(e))
        msql = "Select distinct producto from dt_precios where pais = %s"
        cur.execute(msql, (session['pais'],))
        nombres = []
        for e in cur.fetchall():
            nombres.append(list(e))
        cur.close()
        conn.close()

        return jsonify(dataarr)
    else:
        return jsonify({'mensaje': 'no autorizado'})