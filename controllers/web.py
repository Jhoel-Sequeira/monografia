# controllers/web.py
from flask import Blueprint

from datetime import datetime, date, timedelta
import json
from conexion import conectar

from flask import Flask, jsonify, redirect, render_template, request, send_file, session, url_for

from werkzeug.security import check_password_hash, generate_password_hash

import jinja2
from jinja2 import Environment

#IMPORTS PARA GENERAR EL EXCEL
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment,Font,Border,Side

bp = Blueprint('web', __name__)

@bp.route('/')
def home():
    return render_template('web/index.html')

# INICIO DE LA TIENDA
@bp.route('/tienda')
def tienda():
    return render_template('web/tienda.html')

# Buscador de la tienda
@bp.route('/buscarProducto', methods=['POST'])
def buscarProducto():

    if request.method == "POST":
        producto = request.form['producto']

        conn = conectar()
        cursor = conn.cursor()
        query = 'select top 5 cod_producto,precio,Imagen,stock,nom_producto from producto where nom_producto like ?'
        cursor.execute(query,(producto + '%'))
        productos = cursor.fetchall()
        print(productos)
        if productos:

            return render_template('web/otros/buscador_productos.html', productos=productos)
        else:
            return "Sin Datos"
    else:
        return "No"
    
    return render_template('web/buscador_productos.html')

# Fin buscador de la tienda

# FIN DE LA TIENDA

@bp.route('/servicios')
def servicios():
    return render_template('web/servicios.html')

@bp.route('/clientes')
def clientes():
    return render_template('web/clientes.html')

