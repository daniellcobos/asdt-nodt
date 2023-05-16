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
    return wrongs

def vrf_ventas_liberaciones():
    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    if session['pais'] == 'AR':
        msql1 = " select sum(total_venta) from dt_liberacion where corte ='Cierre' and idacuerdo in (select idacuerdo from dt_acuerdo where vigente = 1) and pais = 'AR'"
        msql2 = "select SUM(cantidad) from dt_ventas where idacuerdo in (select idacuerdo from dt_acuerdo where vigente = 1) and pais = 'AR' and producto <> 'LATISSE' and  producto <> '0'"
    elif session['pais'] == 'CO':
        msql1 = " select sum(total_venta) from dt_liberacion where corte ='Cierre' and idacuerdo in (select idacuerdo from dt_acuerdo where vigente = 1) and pais = 'CO'"
        msql2 = "select SUM(cantidad) from dt_ventas where idacuerdo in (select idacuerdo from dt_acuerdo where vigente = 1) and pais = 'CO' and producto <> 'LATISSE' and  producto <> 'BOTOX 50U' and  producto <> '0'"
    cur.execute(msql1)
    cont1 = cur.fetchone()[0]
    cur.execute(msql2)
    cont2 = cur.fetchone()[0]
    return cont1 - cont2

