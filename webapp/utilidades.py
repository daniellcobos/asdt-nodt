from flask import Flask, flash, jsonify, redirect, url_for, session, send_file, g
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
import logging

app.config.from_object('configuraciones.local')
db_connection_string = app.config["POSTGRESQL_CONNECTION"]

locale.setlocale(locale.LC_ALL, 'es_CO.utf8')

def setup_logger(name, log_file, level=logging.INFO):


    handler = logging.FileHandler(log_file)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

logger2 = setup_logger('util', 'util.log')


def acuerdos_sin_vigencia():
    #Deja sin vigencia los acuerdos vencidos
    now = datetime.now()
    año = now.year

    cyear = now.year
    mes = now.month
    if mes == 1:
        año = año - 1
        mes = 12
    else:
        año = año
        mes = mes - 1

    conn = psycopg2.connect(db_connection_string)
    cur = conn.cursor()
    # Updates both last month and last year
    msql = "update dt_acuerdo set vigente = 0 where (ano_fin = (%s) and mes_fin <= (%s)) or ano_fin < (%s)"
    cur.execute(msql,(str(año),str(mes),str(cyear)))
    logger2.info(msql,str(año),str(mes),str(cyear))
    conn.commit()
    msql = "update dt_cliente_multiple set vigente = 0 from dt_acuerdo where dt_cliente_multiple.idacuerdo in(select dt_acuerdo.idacuerdo where dt_acuerdo.vigente = 0  );"
    logger2.info(msql)
    cur.execute(msql)

    conn.commit()
    cur.close()
    conn.close()  
    return "ok"

logging.basicConfig(filename='mainlog.log', level=logging.DEBUG)


