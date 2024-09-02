
from datetime import datetime, date, timedelta
import json

from flask import Flask, jsonify, redirect, render_template, request, send_file, session, url_for

from werkzeug.security import check_password_hash, generate_password_hash

import jinja2
from jinja2 import Environment


#IMPORTS PARA GENERAR EL EXCEL
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment,Font,Border,Side

from conexion import conectar


app = Flask(__name__)
app.secret_key = 'your secret key'

def capturarHora():
    hi = datetime.now()
    return hi


@app.route('/home')
def home():

    return render_template('sistema/home.html')

@app.route('/veterinaria')
def index():
    # conn = conectar()
    # cursor = conn.cursor()
    # query = 'INSERT INTO Usuarios (Nombreusuario,Usuario,Contraseña,NumRol,IdOdoo,NumEstado) VALUES (?,?,?,?,?,?)'
    # cursor.execute(query, ('ADMIN','admin',generate_password_hash('admin'),1,0,1))
    # conn.commit()
    # cursor.close()
    # conn.close()
    # conn = conectar()
    # cursor = conn.cursor()
    # query = 'INSERT INTO Usuarios (Nombre,Usuario,Contraseña,Rol,IdOdoo) VALUES (?,?,?,?,?)'
    # cursor.execute(query, ('Administrador','admin',generate_password_hash('admin'),'admin',0))
    # conn.commit()
    # cursor.close()
    # conn.close()
    # conn = conectar()
    # cursor = conn.cursor()

    # # # Realiza la inserción
    # query = 'Update Usuarios set Contraseña = ? where NumUsuario = ?'
    # cursor.execute(query, (generate_password_hash('admin'),1))
    # conn.commit()
    return render_template('web/index.html')

@app.route('/sistema')
def sistema():



    return render_template('sistema/login.html')

