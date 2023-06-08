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

def vrf_acuerdos_multiples():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "select idcliente,count(listcliente.idcliente) from (select idcliente from dt_acuerdo where vigente = 1 " \
           "union all select idcliente from dt_cliente_multiple where vigente = 1) as listcliente group by idcliente having count(listcliente.idcliente) > 1"
    cur.execute(msql)
    wrongs = len(cur.fetchall())
    print(wrongs)
    conn.close()
    return wrongs

def vrf_ventas_liberaciones():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    if session['pais'] == 'AR':
        msql1 = " select sum(total_venta) from dt_liberacion where corte <>'Cierre' and idacuerdo in (select idacuerdo from dt_acuerdo where vigente = 1) and pais = 'AR'"
        msql2 = "select SUM(cantidad) from dt_ventas where idacuerdo in (select idacuerdo from dt_acuerdo where vigente = 1) and pais = 'AR' and producto <> 'LATISSE' and  producto <> '0'"
    elif session['pais'] == 'CO':
        msql1 = " select sum(total_venta) from dt_liberacion where corte <> 'Cierre' and idacuerdo in (select idacuerdo from dt_acuerdo where vigente = 1) and pais = 'CO'"
        msql2 = "select SUM(cantidad) from dt_ventas where idacuerdo in (select idacuerdo from dt_acuerdo where vigente = 1) and pais = 'CO' and producto <> 'LATISSE' and  producto <> 'BOTOX 50U' and  producto <> '0'"
    cur.execute(msql1)
    print(msql1)
    cont1 = cur.fetchone()[0]
    cur.execute(msql2)
    cont2 = cur.fetchone()[0]
    print(cont1,cont2)
    conn.close()
    return cont1 - cont2


def cst_acuerdos():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "select count(idacuerdo) from dt_acuerdo where pais = %s"
    cur.execute(msql, (session['pais'], ))
    cont = cur.fetchone()[0]
    conn.close()
    return cont


def cst_acuerdos_vigentes():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "select count(idacuerdo) from dt_acuerdo where vigente = 1 and pais = %s"
    cur.execute(msql, (session['pais'],))
    cont = cur.fetchone()[0]
    conn.close()
    return cont

def cst_liberaciones():
        conn = psycopg2.connect(db_connection_string)
        cur = conn.cursor()
        msql = "select count(*) from dt_liberacion where pais = %s;"
        cur.execute(msql, (session['pais'],))
        cont = cur.fetchone()[0]
        conn.close()
        return cont


def cst_liberaciones_vigentes():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "select count(*) from dt_liberacion where pais = %s and idacuerdo in (select dt_acuerdo.idacuerdo  from dt_acuerdo where vigente = 1);"
    cur.execute(msql, (session['pais'],))
    cont = cur.fetchone()[0]
    conn.close()
    return cont

@app.route('/verificaciones', methods=['GET'])
def verificaciones():
    cst_a = cst_acuerdos()
    cst_av = cst_acuerdos_vigentes()
    lb = cst_liberaciones()
    lb_vgt = cst_liberaciones_vigentes()
    vrf_am = vrf_acuerdos_multiples()
    vrf_vl = vrf_ventas_liberaciones()
    print(vrf_am)
    return render_template('parametros/verificaciones.html', vrf_am=vrf_am, vrf_vl=vrf_vl, cst_a=cst_a, cst_av=cst_av, lb=lb, lb_vgt=lb_vgt)

@app.route('/checkventas', methods=['GET','POST'])
def checkventas():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql = "select count(idventas) from dt_ventas where pais ='AR'"
    cur.execute(msql)
    ventasactuales = cur.fetchone()[0]
    dif = ventasactuales - session["ventasIniciales"]
    return str(dif)+"/"+str(session["currentUpload"])