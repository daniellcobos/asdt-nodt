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
app.config.from_object('configuraciones.local')
db_connection_string = app.config["POSTGRESQL_CONNECTION"]

locale.setlocale(locale.LC_ALL, 'es_CO.utf8')



def acuerdos_sin_vigencia():
    #Deja sin vigencia los acuerdos vencidos
    now = datetime.now()
    año = now.year
    mes = now.month
    if mes == 1:
        año = año - 1
        mes = 12
    else:
        año = año
        mes = mes - 1

    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    msql =  "update dt_acuerdo set vigente = 0 where ano_fin = (%s) and mes_fin = (%s)" 
    cur.execute(msql,(str(año),str(mes)))
    msql = "update dt_cliente_multiple set vigente = 0 from dt_acuerdo where dt_cliente_multiple.idacuerdo in(select dt_acuerdo.idacuerdo where dt_acuerdo.ano_fin = (%s) and dt_acuerdo.mes_fin = (%s) );"
    print(msql)
    cur.execute(msql,(str(año),str(mes)))

    conn.commit()
    cur.close()
    conn.close()  
    return "ok"    