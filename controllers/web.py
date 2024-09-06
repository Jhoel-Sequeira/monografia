# controllers/web.py
from flask import Blueprint

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

bp = Blueprint('web', __name__)

@bp.route('/')
def home():
    return render_template('web/index.html')


@bp.route('/tienda')
def tienda():
    return render_template('web/tienda.html')

@bp.route('/servicios')
def servicios():
    return render_template('web/servicios.html')

@bp.route('/clientes')
def clientes():
    return render_template('web/clientes.html')

