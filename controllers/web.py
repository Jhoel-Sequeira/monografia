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

    # conn = conectar()
    # cursor = conn.cursor()
    # query = 'INSERT INTO credenciales (usuario,contrasena,Rol,cargo) VALUES (?,?,1,1)'
    # cursor.execute(query, ('JHOEL',generate_password_hash('123')))
    # conn.commit()
    # cursor.close()
    # conn.close()
    # conn = conectar()
    # cursor = conn.cursor()



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
        query = 'select  cod_producto,precio,Imagen,stock,nom_producto from producto where nom_producto like ?'
        cursor.execute(query,(producto + '%'))
        productos = cursor.fetchall()
        print(productos)
        return render_template('web/otros/buscador_productos.html', productos=productos)
        
    else:
        return "No"
    
    return render_template('web/buscador_productos.html')

# Fin buscador de la tienda
# Llamado detalle del producto
@bp.route('/detalleProducto', methods=['POST'])
def detalleProducto():

    if request.method == "POST":
        num = request.form['num']

        conn = conectar()
        cursor = conn.cursor()
        query = 'select  cod_producto,precio,Imagen,stock,stock_critico,nom_producto from producto where cod_producto = ?'
        cursor.execute(query,(num))
        datos = cursor.fetchall()
        print(datos)
        if datos:

            return render_template('web/modales/modal_compra.html', producto=datos)
        else:
            return "Sin Datos"
    else:
        return "No"
    
    return render_template('web/otros/buscador_productos.html')

# Fin buscador de la tienda


# RESTAR PRODUCTO DEL CARRITO
@bp.route('/restarProducto', methods=['POST'])
def restarProducto():

    if request.method == "POST":
        
        producto = request.form['producto']
        print(producto)

        conn = conectar()
        cursor = conn.cursor()
        query = 'select cantidad from carrito_compra where id_carrito = ?'
        cursor.execute(query,(producto))
        datos = cursor.fetchone()

        if datos[0] <= 1:
            return 'no'




        conn = conectar()
        cursor = conn.cursor()
        query = 'UPDATE carrito_compra set cantidad -= 1 where num_cliente = ? and id_carrito = ? and id_estado = 2'
        cursor.execute(query,(session['id'],producto))
        conn.commit()
        cursor.close()
        conn.close()

        conn = conectar()
        cursor = conn.cursor()
        query = 'select cantidad from carrito_compra where id_carrito = ?'
        cursor.execute(query,(producto))
        datos = cursor.fetchone()
        
        return str(datos[0])
    else:
        return "No"
    
    return render_template('web/otros/buscador_productos.html')

# Fin RESTA DE PRODUCTO

# RESTAR PRODUCTO DEL CARRITO
@bp.route('/sumarCantidad', methods=['POST'])
def sumarCantidad():

    if request.method == "POST":
        
        producto = request.form['producto']
        print(producto)
        conn = conectar()
        cursor = conn.cursor()
        query = 'UPDATE carrito_compra set cantidad += 1 where num_cliente = ? and id_carrito = ? and id_estado = 2'
        cursor.execute(query,(session['id'],producto))
        conn.commit()
        cursor.close()
        conn.close()

        conn = conectar()
        cursor = conn.cursor()
        query = 'select cantidad from carrito_compra where id_carrito = ?'
        cursor.execute(query,(producto))
        datos = cursor.fetchone()
        
        return str(datos[0])
    else:
        return "No"
    
    return render_template('web/otros/buscador_productos.html')
# Fin RESTA DE PRODUCTO


# RESTAR PRODUCTO DEL CARRITO
@bp.route('/borrarProducto', methods=['POST'])
def borrarProducto():

    if request.method == "POST":
        
        producto = request.form['producto']
        print(producto)

        conn = conectar()
        cursor = conn.cursor()
        query = 'delete from carrito_compra where id_carrito = ?'
        cursor.execute(query,(producto))
        conn.commit()
        cursor.close()
        conn.close()

        return 'hecho'
    else:
        return "No"
    
    return render_template('web/otros/buscador_productos.html')

# Fin RESTA DE PRODUCTO



# Llamado del Carrito total por Usuario
@bp.route('/carritoTotal', methods=['POST'])
def carritoTotal():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = 'SELECT cc.id_carrito,p.Imagen, p.nom_producto, cc.cantidad, p.precio, e.NombreEstado FROM carrito_compra AS cc INNER JOIN producto AS p ON cc.cod_producto = p.cod_producto INNER JOIN cliente AS c ON cc.num_cliente = c.num_cliente INNER JOIN estado AS e ON cc.id_estado = e.id_estado where cc.num_cliente = ? GROUP BY p.nom_producto, cc.id_carrito, cc.cantidad, p.precio, e.NombreEstado, p.Imagen;'
        cursor.execute(query,(session['id']))
        datos = cursor.fetchall()
        print(datos)
        if datos:

            return render_template('web/modales/modal_carrito.html', producto=datos)
        else:
            return "Sin Datos"
    else:
        return "No"
    
    return render_template('web/buscador_productos.html')


@bp.route('/carrito')
def carrito():


        return render_template('web/carrito.html')

@bp.route('/cargarProductosCarrito', methods=['POST'])
def cargarProductosCarrito():

        conn = conectar()
        cursor = conn.cursor()
        query = 'SELECT cc.id_carrito,p.Imagen, p.nom_producto, cc.cantidad, p.precio, e.NombreEstado FROM carrito_compra AS cc INNER JOIN producto AS p ON cc.cod_producto = p.cod_producto INNER JOIN cliente AS c ON cc.num_cliente = c.num_cliente INNER JOIN estado AS e ON cc.id_estado = e.id_estado where cc.num_cliente = ? GROUP BY p.nom_producto, cc.id_carrito, cc.cantidad, p.precio, e.NombreEstado, p.Imagen;'
        cursor.execute(query,(session['id']))
        datos = cursor.fetchall()
        print(datos)
        if not datos:
            datos = ''

        return render_template('web/otros/traer_productos.html', producto=datos)

@bp.route('/cantidadArticulos', methods=['POST'])
def cantidadArticulos():

        conn = conectar()
        cursor = conn.cursor()
        query = 'SELECT COUNT(DISTINCT p.cod_producto) AS total_productos FROM carrito_compra AS cc INNER JOIN producto AS p ON cc.cod_producto = p.cod_producto INNER JOIN cliente AS c ON cc.num_cliente = c.num_cliente INNER JOIN estado AS e ON cc.id_estado = e.id_estado WHERE cc.num_cliente = ?;'
        cursor.execute(query,(session['id']))
        datos = cursor.fetchone()
        print(datos)
        if not datos[0]:
            datos = 0
        else:
            datos = datos[0]
        return render_template('web/otros/cantidad_articulos.html', producto=datos)
    
    

# Fin buscador de la tienda

# Guardar carrito del cliente
@bp.route('/guardarCarrito', methods=['POST'])
def guardarCarrito():

    if request.method == "POST":
        if session:
            producto = request.form['producto']
            cantidad = request.form['cantidad']


            conn = conectar()
            cursor = conn.cursor()
            query = 'select * from carrito_compra where num_cliente = ? and cod_producto = ? and id_estado = 2'
            cursor.execute(query, (session['id'],producto))
            carrito = cursor.fetchone()
            cursor.close()
            conn.close()


            if carrito:
                conn = conectar()
                cursor = conn.cursor()
                query = 'UPDATE carrito_compra set cantidad += ? where id_carrito = ?'
                cursor.execute(query,(cantidad,carrito[0]))
                conn.commit()
                cursor.close()
                conn.close()
            else:
                
                conn = conectar()
                cursor = conn.cursor()
                query = 'INSERT INTO carrito_compra (cod_producto,num_cliente,cantidad,id_estado) VALUES (?,?,?,2)'
                cursor.execute(query,(producto,session['id'],cantidad))
                conn.commit()
                cursor.close()
                conn.close()
            
            return 'HECHO'
        else:
            return 'Sin Sesion'
    else:
        return "No"
    
    

# Fin guardar carrito de la tienda

@bp.route('/comprar', methods=['POST'])
def comprar():
    if request.method == "POST":
        usuario = request.form['usuario']
        contraseña = request.form['pass']

        if usuario == "" or contraseña == "":
            return render_template('login.html', errorlogin=1)
        else:
            conn = conectar()
            cursor = conn.cursor()
            query = 'select c.num_cliente,c.nombres_cliente,c.apellidos_cliente,c.correo_cliente,c.telefono,cred.contrasena,r.nombre_rol from credenciales as cred inner join cliente as c on cred.id_credencial = c.id_credencial inner join roles as r on cred.rol = r.cod_rol where cred.usuario = ? AND c.id_estado = 1'
            cursor.execute(query, usuario)
            rows = cursor.fetchone()
            cursor.close()
            conn.close()
            print(rows)
            if rows:
                if len(rows) == 0 or not check_password_hash(rows[5], contraseña):
                    return 'error'
                else:
                    #session['last_seen'] = datetime.now()
                    session['id'] = rows[0]
                    session['nombre'] = rows[1]
                    session["pass"] = contraseña
                    session['rol'] = rows[6]
                return 'exito'
            else:
               return 'error'
    return 'error'

# CargarCarrito Numero

@bp.route('/cargarCarrito', methods=['POST'])
def cargarCarrito():

    if request.method == "POST":
        if session:

            conn = conectar()
            cursor = conn.cursor()
            query = 'select count(*) from carrito_compra where num_cliente = ?'
            cursor.execute(query, session['id'])
            rows = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return str(rows[0])
        else:
            return 'Sin Sesion'
    else:
        return "No"

# TAbla de precios en el carrito de la persona
@bp.route('/cargarTabla', methods=["GET", "POST"])
def cargarTabla():

    conn = conectar()
    cursor = conn.cursor()
    query = 'SELECT cc.id_carrito,p.Imagen, p.nom_producto, cc.cantidad, p.precio, e.NombreEstado FROM carrito_compra AS cc INNER JOIN producto AS p ON cc.cod_producto = p.cod_producto INNER JOIN cliente AS c ON cc.num_cliente = c.num_cliente INNER JOIN estado AS e ON cc.id_estado = e.id_estado where cc.num_cliente = ? GROUP BY p.nom_producto, cc.id_carrito, cc.cantidad, p.precio, e.NombreEstado, p.Imagen;'
    cursor.execute(query,(session['id']))
    datos = cursor.fetchall()


    conn = conectar()
    cursor = conn.cursor()
    query = 'SELECT SUM(cc.cantidad * p.precio) AS total_factura FROM carrito_compra AS cc INNER JOIN producto AS p ON cc.cod_producto = p.cod_producto INNER JOIN cliente AS c ON cc.num_cliente = c.num_cliente WHERE cc.num_cliente = ?'
    cursor.execute(query,(session['id']))
    total = cursor.fetchone()
    
    return render_template('web/tablas/tabla_precios.html', productos = datos,total = total[0])


#FIN TABLA






# FIN DE LA TIENDA

@bp.route('/servicios')
def servicios():
    return render_template('web/servicios.html')

@bp.route('/clientes')
def clientes():
    return render_template('web/clientes.html')

