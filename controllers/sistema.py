# controllers/sistema.py
from datetime import datetime, timedelta
import os
import locale
from fpdf import FPDF
from flask import Blueprint, jsonify, render_template, request,session,redirect,make_response,current_app,url_for
from functools import wraps
from conexion import conectar
from werkzeug.security import check_password_hash, generate_password_hash
import pandas as pd

from controllers.excel import GenerarExcel_3
from controllers.correo import enviar_correo, enviar_correo_receta, enviar_correo_registro

def capturarHora():
    hi = datetime.now()
    return hi

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:  # Verifica si el usuario está en la sesión
            return redirect('/')  # Redirige a la página de error si no está autenticado
        return f(*args, **kwargs)  # Si la sesión es válida, ejecuta la función original
    return decorated_function

bp = Blueprint('sistema', __name__)

@bp.route('/sistema')
@login_required
def sistema_route():
    
    return render_template('sistema/home.html')

@bp.route('/deslog')
def deslog():
    session.clear()
    return redirect(url_for('web.home'))

# MODULO: INVENTARIO



# INICIO DEL MODULO DE INVENTARIO
@bp.route('/inventario')
@login_required
def inventario():
    return render_template('sistema/inventario.html')

# INICIO DE LA CARGA DE LA TABLA DE PRODUCTOS
@bp.route('/tablaProductos', methods=['POST'])
def tablaProductos():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = 'select p.cod_producto,p.nom_producto,p.precio,p.stock,p.stock_critico,prov.nom_proveedor,t.tipos,u.nombre as unidad,e.NombreEstado as estado from producto as p inner join proveedor as prov on p.cod_proveedor = prov.cod_proveedor inner join tipo as t on p.tipo_producto = t.cod_tipo inner join unidades as u on p.unidad = u.cod_unidad inner join estado as e on p.id_estado = e.id_estado'
        cursor.execute(query)
        productos = cursor.fetchall()
        return render_template('sistema/tablas/tabla_inventario.html', productos=productos)
        
    else:
        return "No"

# FIN DE LA CARGA DE PRODUCTOS 

# INICIO DE LA CARGA DE LA TABLA DE PRODUCTOS
@bp.route('/modalAgregarProducto', methods=['POST'])
def modalAgregarProducto():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = 'select * from proveedor where id_estado = 1'
        cursor.execute(query)
        proveedores = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = 'select * from unidades '
        cursor.execute(query)
        unidades = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = 'select * from tipo '
        cursor.execute(query)
        categoria = cursor.fetchall()

        
        return render_template('sistema/modales/modal_agregar_producto.html', proveedores = proveedores,unidades = unidades,categorias = categoria)
        
    else:
        return "No"

# FIN DE LA CARGA DE PRODUCTOS 
@bp.route('/guardarProducto', methods=['POST'])
def guardarProducto():

    nombre = request.form['nombre']
    stock1 = request.form['stock']
    tienda = request.form['tienda']
    precio = request.form['precio']
    unidad = request.form['unidad']
    categoria = request.form['categoria']
    proveedor = request.form['proveedor']
    critico = request.form['critico']
    imagen = request.files['imagen']

    if tienda == 1:
        Tienda = 'Si'
    else:
        Tienda = 'No'

    if 'imagen' not in request.files:
        imagen = ''
    else:
        imagen = request.files['imagen']

   
    if imagen:
            ruta = 'static/web/img/productos/' + imagen.filename
            ruta_completa = os.path.join('static/web/img/productos/', imagen.filename)
            print(ruta)
            # Guardar la imagen en la ruta completa
            imagen.save(ruta_completa)

            conn = conectar()
            cursor = conn.cursor()
            # Realiza la inserción
            query = 'INSERT INTO producto (nom_producto,id_estado,cod_proveedor,tipo_producto,precio,stock_critico,stock,imagen,unidad,tienda) VALUES (?,?,?,?,?,?,?,?,?,?)'
            cursor.execute(query, (nombre, 1,proveedor,categoria,precio,critico,stock1,ruta,unidad,Tienda))
            conn.commit()
    else:
            ruta = 'static/web/img/productos/defecto.jpg'
            conn = conectar()
            cursor = conn.cursor()
            # Realiza la inserción
            query = 'INSERT INTO producto (nom_producto,id_estado,cod_proveedor,tipo_producto,precio,stock_critico,stock,imagen,unidad,tienda) VALUES (?,?,?,?,?,?,?,?,?,?)'
            cursor.execute(query, (nombre, 1,proveedor,categoria,precio,critico,stock1,ruta,unidad,Tienda))
            conn.commit()



    return 'Hecho'

# DETALLE DE LOS PRODUCTOS SELECCIONADOS
@bp.route('/mostrarDetalleProducto', methods=['POST'])
def mostrarDetalleProducto():

    num = request.form['num']

    conn = conectar()
    cursor = conn.cursor()
    query = 'select * from proveedor where id_estado = 1'
    cursor.execute(query)
    proveedores = cursor.fetchall()

    conn = conectar()
    cursor = conn.cursor()
    query = 'select * from unidades '
    cursor.execute(query)
    unidades = cursor.fetchall()

    conn = conectar()
    cursor = conn.cursor()
    query = 'select * from tipo '
    cursor.execute(query)
    categoria = cursor.fetchall()

    

    conn = conectar()
    cursor = conn.cursor()
    query = 'select p.cod_producto,p.nom_producto,p.precio,p.stock,p.stock_critico,prov.nom_proveedor,t.tipos,u.nombre as unidad,e.NombreEstado as estado,p.Imagen,p.tienda from producto as p inner join proveedor as prov on p.cod_proveedor = prov.cod_proveedor inner join tipo as t on p.tipo_producto = t.cod_tipo inner join unidades as u on p.unidad = u.cod_unidad inner join estado as e on p.id_estado = e.id_estado where p.cod_producto = ?'
    cursor.execute(query,(num))
    producto = cursor.fetchall()


    return render_template('sistema/modales/modal_editar_producto.html', proveedores = proveedores,unidades = unidades,categorias = categoria,producto = producto)

# EDITAR PRODUCTOS
@bp.route('/actualizarProducto', methods=['POST'])
def actualizarProducto():
    try:
        # Recoger datos del formulario
        nombre = request.form['nombre']
        num = request.form['num']
        stock1 = request.form['stock']
        tienda = request.form['tienda']
        precio = request.form['precio']
        unidad = request.form['unidad']
        categoria = request.form['categoria']
        proveedor = request.form['proveedor']
        critico = request.form['critico']
        
        # Recoger la imagen (si está disponible)
        imagen = request.files.get('imagen')  # Usar get para evitar errores si no existe

        # Determinar si es para la tienda
        Tienda = 'Si' if tienda == '1' else 'No'

        # Conectar a la base de datos
        conn = conectar()
        cursor = conn.cursor()

        # Verificar si se ha subido una nueva imagen
        if imagen and imagen.filename != '':
            # Crear la ruta completa para guardar la imagen
            ruta = os.path.join('static', 'web', 'img', 'productos', imagen.filename)
            imagen.save(ruta)
        else:
            # Si no se sube imagen, mantener la imagen anterior del producto
            cursor.execute("SELECT imagen FROM producto WHERE cod_producto = ?", (num,))
            ruta = cursor.fetchone()[0]  # Obtener la ruta de la imagen actual

        # Query de actualización del producto
        query = '''
        UPDATE producto
        SET nom_producto = ?, id_estado = ?, cod_proveedor = ?, tipo_producto = ?, 
            precio = ?, stock_critico = ?, stock = ?, imagen = ?, unidad = ?, tienda = ?
        WHERE cod_producto = ?
        '''
        
        # Ejecutar la consulta SQL
        cursor.execute(query, (nombre, 1, proveedor, categoria, precio, critico, stock1, ruta, unidad, Tienda, num))
        conn.commit()

        # Cerrar la conexión
        cursor.close()
        conn.close()

        return 'Producto actualizado correctamente'

    except Exception as e:
        # Manejo de errores
        print(f"Error al actualizar el producto: {e}")
        return 'Error al actualizar el producto', 500

# FIN DE EDITAR     

# EDITAR PRODUCTOS
@bp.route('/importarPrecios', methods=['GET','POST'])
def importarPrecios():
    return render_template('sistema/importarPrecio.html')


@bp.route('/actualizarPrecios', methods=['GET', 'POST'])
def actualizarPrecios():
    if request.method == 'POST':
        # Verificar si el archivo está en la solicitud
        if 'file' not in request.files:
            return 'No'

        file = request.files['file']

        # Verificar si se seleccionó algún archivo
        if file.filename == '':
            return 'No'

        if file and file.filename.endswith('.xlsx'):
            # Guardar el archivo en el servidor temporalmente
            filepath = os.path.join('static/sistema/reportes/', file.filename)
            file.save(filepath)

            # Procesar el archivo Excel
            try:
                df = pd.read_excel(filepath)  # Leer el archivo Excel con pandas

                # Lógica para actualizar los precios (ejemplo)
                for index, row in df.iterrows():
                    # Suponiendo que tienes columnas 'producto' y 'nuevo_precio' en el archivo
                    nombre = row['producto']
                    precio = row['precio']
                    num = row['id_producto']
                    
                    conn = conectar()
                    cursor = conn.cursor()

                    
                    # Query de actualización del producto
                    query = '''
                    UPDATE producto
                    SET nom_producto = ?, precio = ?
                    WHERE cod_producto = ?
                    '''
                    
                    # Ejecutar la consulta SQL
                    cursor.execute(query, (nombre, precio, num))
                    conn.commit()

                    # Cerrar la conexión
                    cursor.close()
                    conn.close()

                return 'Hecho'

            except Exception as e:
                return 'Error: {e}'

@bp.route('/descargarPLantilla', methods=['GET','POST'])
def descargarPLantilla():

    array_datos = []
    resultadosVar = []
    conn = conectar()
    cursor = conn.cursor()
    query = 'select cod_producto,nom_producto,precio,stock,stock_critico from Producto'
    cursor.execute(query)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    print('RESULTADOS ',resultados)

    resultadosVar += resultados
    print('arreglo con los datos: ',resultadosVar)
    array_datos.append(resultadosVar)
    if array_datos:
        retorno = GenerarExcel_3(array_datos)


        return jsonify({'url': ''+retorno})
    else:
            return 'NO'


# FIN DE EDITAR     

# FIN DEL MODULO DE INVENTARIO

# INICIO DEL MODULO DE VENTAS
@bp.route('/ventas')
@login_required
def ventas():
    return render_template('sistema/ventas.html')

@bp.route('/caja')
@login_required
def caja():

    conn = conectar()
    cursor = conn.cursor()
    query = "select c.num_cliente, c.nombres_cliente + ' '+ c.apellidos_cliente as Nombre from cliente as c inner join credenciales as cred on c.id_credencial = cred.id_credencial inner join roles as r on cred.rol = r.cod_rol where r.nombre_rol = 'CLIENTE'"
    cursor.execute(query)
    clientes = cursor.fetchall()


    return render_template('sistema/caja.html',clientes = clientes)

@bp.route('/traerId', methods=['POST'])
@login_required
def traerId():

    conn = conectar()
    cursor = conn.cursor()
    query = "select top 1 cod_venta from venta where cod_estado = 7 order by cod_venta desc "
    cursor.execute(query)
    ultimaventa = cursor.fetchone()
    if ultimaventa:
        print('ultimaventa : ',ultimaventa)
        return str(ultimaventa[0]+1)
    else:
        return str(1)
    


@bp.route('/cancelarFactura', methods=['POST'])
@login_required
def cancelarFactura():

    num = request.form['id']

    conn = conectar()
    cursor = conn.cursor()
                    # Query de actualización del producto
    query = '''
            UPDATE venta
            SET cod_estado = 9
            WHERE cod_venta = ?
    '''
                    
                    # Ejecutar la consulta SQL
    cursor.execute(query, (num))
    conn.commit()

                    # Cerrar la conexión
    cursor.close()
    conn.close()

    return 'Hecho'
    
    
@bp.route('/buscarProductoCaja', methods=['POST'])
def buscarProductoCaja():

    if request.method == "POST":
        producto = request.form['producto']

        conn = conectar()
        cursor = conn.cursor()
        query = "select cod_producto,precio,Imagen,stock,nom_producto from producto where nom_producto like ? and Tienda = 'Si'"
        cursor.execute(query,(producto + '%'))
        productos = cursor.fetchall()
        print(productos)
        return render_template('sistema/otros/buscador_caja.html', productos=productos)
        
    else:
        return "No"
    
@bp.route('/crearFactura', methods=['POST'])
def crearFactura():
    if request.method == "POST":
        FechaActual = capturarHora()
        cliente1 = request.form['cliente']
        num = request.form['num']

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from venta where cod_venta = ? "
        cursor.execute(query,(num))
        existe = cursor.fetchone()

        if existe:
            return 'ya'
        
        print(cliente1)
        if cliente1:
            conn = conectar()
            cursor = conn.cursor()
            query = 'INSERT INTO venta (fecha_venta,Total,num_cliente,vendedor,cod_estado) VALUES (?,?,?,?,8)'
            cursor.execute(query, (FechaActual,0,cliente1,session['id']))
            conn.commit()
            cursor.close()
            conn.close()
        else:
            conn = conectar()
            cursor = conn.cursor()
            query = 'INSERT INTO venta (fecha_venta,Total,vendedor,cod_estado) VALUES (?,?,?,8)'
            cursor.execute(query, (FechaActual,0,session['id']))
            conn.commit()
            cursor.close()
            conn.close()
        
        
       
       

    return 'hecho'
# SE INGRESA EL MEDICAMENTO A LA FACTURA CREADA
@bp.route('/comprobarStock', methods=['POST', 'GET'])
def comprobarStock():
    if request.method == "POST":
        medicamento = request.form['medicamento']
        cantidad = request.form['cantidad']

        conn = conectar()
        cursor = conn.cursor()
        query = "select stock from producto where cod_producto = ? "
        cursor.execute(query,(medicamento))
        stock = cursor.fetchone()

        if stock[0] >= int(cantidad):
            return 'si'
        else:
    
            return 'no'
        
@bp.route('/comprobarStockReceta', methods=['POST', 'GET'])
def comprobarStockReceta():
    if request.method == "POST":
        medicamento = request.form['medicamento']
        cantidad = request.form['cantidad']

        conn = conectar()
        cursor = conn.cursor()
        query = "select p.cod_producto,a.cantidad from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ?"
        cursor.execute(query,(receta))
        receta = cursor.fetchall()

        insert_query = """
        INSERT INTO Det_venta (cod_producto_1,cod_venta_1,Cantidad,precio_venta) VALUES (?,?,?,0)
        """

        for cod_producto, cantidad in receta:
            cursor.execute(insert_query, (cod_producto,num, cantidad))

        conn.commit()
        cursor.close()
        conn.close()



        conn = conectar()
        cursor = conn.cursor()
        query = "select stock from producto where cod_producto = ? "
        cursor.execute(query,(medicamento))
        stock = cursor.fetchone()

        if stock[0] >= int(cantidad):
            return 'si'
        else:
    
            return 'no'
        
@bp.route('/eliminarProductoCaja', methods=['POST', 'GET'])
def eliminarProductoCaja():
    if request.method == "POST":
        medicamento = request.form['num']
        venta = request.form['venta']


        conn = conectar()
        cursor = conn.cursor()
        query = "select cantidad,cod_producto_1 from Det_venta where cod_venta_1 = ? and cod_detalle = ? "
        cursor.execute(query,(venta,medicamento))
        cantidad = cursor.fetchone()

        conn = conectar()
        cursor = conn.cursor()
        query = "delete Det_venta where cod_venta_1 = ? AND cod_detalle = ? "
        cursor.execute(query,(venta,medicamento))
        conn.commit()
        cursor.close()
        conn.close()

        conn = conectar()
        cursor = conn.cursor()
        query = 'update producto set stock += ? where cod_producto = ?'
        cursor.execute(query, (cantidad[0],cantidad[1]))
        conn.commit()
        cursor.close()
        conn.close()
      

    return 'si'

@bp.route('/eliminarProductoCajaSin', methods=['POST', 'GET'])
def eliminarProductoCajaSin():
    if request.method == "POST":
        medicamento = request.form['num']
        venta = request.form['venta']


        conn = conectar()
        cursor = conn.cursor()
        query = "select cantidad,cod_producto_1 from Det_venta where cod_venta_1 = ? and cod_detalle = ? "
        cursor.execute(query,(venta,medicamento))
        cantidad = cursor.fetchone()

        conn = conectar()
        cursor = conn.cursor()
        query = "delete Det_venta where cod_venta_1 = ? AND cod_detalle = ? "
        cursor.execute(query,(venta,medicamento))
        conn.commit()
        cursor.close()
        conn.close()

      
      

    return 'si'

@bp.route('/limpiarCaja', methods=['POST', 'GET'])
def limpiarCaja():
    if request.method == "POST":
        venta = request.form['venta']

        conn = conectar()
        cursor = conn.cursor()
        query = "select cantidad,cod_producto_1 from Det_venta where cod_venta_1 = ? "
        cursor.execute(query,(venta))
        cantidad = cursor.fetchone()

        conn = conectar()
        cursor = conn.cursor()
        query = "delete Det_venta where cod_venta_1 = ? "
        cursor.execute(query,(venta))
        conn.commit()
        cursor.close()
        conn.close()

        conn = conectar()
        cursor = conn.cursor()
        query = 'update producto set stock += ? where cod_producto = ?'
        cursor.execute(query, (cantidad[0],cantidad[1]))
        conn.commit()
        cursor.close()
        conn.close()
      

    return 'si'
        
@bp.route('/limpiarCajaSinRetorno', methods=['POST', 'GET'])
def limpiarCajaSinRetorno():
    if request.method == "POST":
        venta = request.form['venta']

        conn = conectar()
        cursor = conn.cursor()
        query = "select cantidad,cod_producto_1 from Det_venta where cod_venta_1 = ? "
        cursor.execute(query,(venta))
        cantidad = cursor.fetchone()

        conn = conectar()
        cursor = conn.cursor()
        query = "delete Det_venta where cod_venta_1 = ? "
        cursor.execute(query,(venta))
        conn.commit()
        cursor.close()
        conn.close()

        
      

    return 'si'

@bp.route('/facturar', methods=['POST', 'GET'])
def facturar():
    num = request.args.get('id')

    conn = conectar()
    cursor = conn.cursor()

    # Consulta SQL para obtener los datos del ticket
    query = """
    	select v.cod_venta,v.fecha_venta,c.nombres_cliente + ' ' + c.apellidos_cliente as cliente, vendedor.nombres_cliente + ' ' +vendedor.apellidos_cliente as vendedor,SUM(dv.cantidad * p.precio - dv.precio_venta) AS total_venta  from venta as v inner join cliente as c on v.num_cliente = c.num_cliente  INNER JOIN cliente as vendedor on vendedor.num_cliente = v.vendedor
    INNER JOIN 
                    Det_venta AS dv ON v.cod_venta = dv.cod_venta_1
                INNER JOIN 
                    producto AS p ON dv.cod_producto_1 = p.cod_producto
                where v.cod_venta = ?
                GROUP BY 
                    v.cod_venta, 
                    v.fecha_venta, 
                    c.nombres_cliente,
                    c.apellidos_cliente,
                    vendedor.nombres_cliente, 
                    vendedor.apellidos_cliente
    """

    cursor.execute(query, (num))
    ticket = cursor.fetchone()
    no_tiene = 1
    if not ticket:
        no_tiene = 0
        conn = conectar()
        cursor = conn.cursor()

        # Consulta SQL para obtener los datos del ticket
        query = """
            	SELECT 
                    v.cod_venta, 
                    v.fecha_venta,
                    
                    vendedor.nombres_cliente + ' ' + vendedor.apellidos_cliente AS vendedor,
                    SUM(dv.cantidad * p.precio - dv.precio_venta) AS total_venta
                FROM 
                    venta AS v 
                INNER JOIN 
                    cliente AS vendedor ON vendedor.num_cliente = v.vendedor 
                INNER JOIN 
                    Det_venta AS dv ON v.cod_venta = dv.cod_venta_1
                INNER JOIN 
                    producto AS p ON dv.cod_producto_1 = p.cod_producto
                where v.cod_venta = ?
                GROUP BY 
                    v.cod_venta, 
                    v.fecha_venta, 
                    vendedor.nombres_cliente, 
                    vendedor.apellidos_cliente

        
        """


        cursor.execute(query, (num))
        ticket = cursor.fetchone()

    conn = conectar()
    cursor = conn.cursor()
    query = "select p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento,p.cod_producto from Det_venta as dv inner join producto as p on dv.cod_producto_1 = p.cod_producto where dv.cod_venta_1 = ?"
    cursor.execute(query,(num))
    detalle = cursor.fetchall()

    print(detalle)


    print(ticket)

    fecha_factura = ticket[1].strftime("%Y-%m-%d") if isinstance(ticket[1], datetime) else str(ticket[1])
    hora_factura = ticket[1].strftime("%I:%M %p") if isinstance(ticket[1], datetime) else str(ticket[1])
    

    pdf = FPDF('P', 'mm',  (101.6, 175))
    pdf.set_margins(5.5, 5.5, 5.5)
    pdf.set_display_mode(zoom=100, layout='continuous')
    pdf.add_page()
    
    x = 35
    y = 0
    width = 30
    height = 0 
    imagePath = 'static/sistema/images/logos/logo.png'

    pdf.image(imagePath, x, y, width, height)
    pdf.ln(20)
    pdf.set_font('Arial', 'B', 30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.multi_cell(0, 5, 'Veterinaria El Buen Productor', 0, "C")
    pdf.ln(1)
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Factura No: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(30, 10, str(ticket[0]))
    pdf.ln(6)
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Fecha: ')
    pdf.set_font('Arial', '', 7.5)  # Cambia a fuente normal si lo prefieres
    pdf.cell(30, 10, fecha_factura)  # Espacio suficiente para la fecha
    pdf.ln(6)

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Hora: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(30, 10, hora_factura)  # Espacio suficiente para la hora

    pdf.ln(5)  
    
    if no_tiene ==1:

        pdf.set_font('Arial', 'B', 7.5)
        pdf.cell(25, 10, 'Cliente: ')
        pdf.set_font('Arial', 'B', 7.5)
        pdf.cell(20, 10, ticket[2])
        pdf.ln(6)
    
        
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Vendedor: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(25, 10, str(ticket[3]).upper())
    pdf.ln(9)

    pdf.set_line_width(0.2) 
    pdf.set_font('Arial', 'B', 7.5)
    
        # Encabezados de la tabla
    pdf.cell(30, 10, 'Producto', 1)
    pdf.cell(15, 10, 'Cantidad', 1)
    pdf.cell(15, 10, 'Descuento', 1)
    pdf.cell(30, 10, 'Subtotal', 1)
    pdf.ln(10)  # Salto de línea

    # Iterar sobre los resultados y calcular el descuento
    for fila in detalle:

        nom_producto = str(fila[0]).upper()  # Nombre del producto en mayúsculas
        cantidad = float(fila[1])  # Cantidad comprada
        precio = float(fila[2])  # Precio unitario
        descuento_raw = float(fila[5])  # Descuento aplicado en porcentaje o monto

        conn = conectar()
        cursor = conn.cursor()

                        
                        # Query de actualización del producto
        query = '''
                UPDATE producto
                SET stock -= ?
                WHERE cod_producto = ?
        '''
                        
                        # Ejecutar la consulta SQL
        cursor.execute(query, (cantidad,fila[6]))
        conn.commit()

                        # Cerrar la conexión
        cursor.close()
        conn.close()









   

        # Calcular el descuento
        subtotal = cantidad * precio
        if descuento_raw == 0.0:
            descuento_aplicado = 0
        elif descuento_raw < 1:
            descuento_aplicado = subtotal * descuento_raw  # Aplicar descuento en porcentaje
        else:
            descuento_aplicado = descuento_raw  # Aplicar descuento directo

        total = subtotal - descuento_aplicado

        # Imprimir los datos en el PDF
        pdf.set_line_width(0.0)  # Establecer un borde más fino

        pdf.set_font('Arial', '', 7.5)

        # Fila de datos
        pdf.cell(30, 10, nom_producto, 1, 0)  # Borde para la celda de producto
        pdf.cell(15, 10, str(cantidad), 1, 0, 'C')  # Cantidad centrada con borde fino
        if descuento_aplicado == 0:

            pdf.cell(15, 10, "", 1, 0, 'C')  # Precio centrado con borde fino
        else:
            pdf.cell(15, 10, f"C$ {descuento_aplicado:.2f}", 1, 0, 'C')  # Precio centrado con borde fino
        pdf.cell(30, 10, f"C$ {total:.2f}", 1, 0, 'C')  # Descuento centrado con borde y nueva línea

        pdf.ln(10)  # Aumenta el espacio entre filas a 6 unidades

    if no_tiene ==1:
        pdf.set_font('Arial', 'B', 7.5)  # Título "Total"
        pdf.cell(25, 30, 'Total: ')
        pdf.set_font('Arial', '', 30)  # Aumentar el tamaño de la fuente para el valor
        pdf.cell(65, 30, 'C$ '+str(ticket[4]), 0, 1, 'R')  # Alinear a la derecha
        pdf.ln(9)  # Salto de línea
    else:
        pdf.set_font('Arial', 'B', 7.5)  # Título "Total"
        pdf.cell(25, 30, 'Total: ')
        pdf.set_font('Arial', '', 30)  # Aumentar el tamaño de la fuente para el valor
        pdf.cell(65, 30, 'C$ '+str(ticket[3]), 0, 1, 'R')  # Alinear a la derecha
        pdf.ln(9)  # Salto de línea 

        
    pdf_output = pdf.output(dest='S').encode('latin1') 

    response = make_response(pdf_output)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=ticket.pdf'


    conn = conectar()
    cursor = conn.cursor()

                    
                    # Query de actualización del producto
    query = '''
            UPDATE venta
            SET cod_estado = 7
            WHERE cod_venta = ?
    '''
                    
                    # Ejecutar la consulta SQL
    cursor.execute(query, (num))
    conn.commit()

                    # Cerrar la conexión
    cursor.close()
    conn.close()

    

    return response








@bp.route('/ingresarMedicamento', methods=['POST'])
def ingresarMedicamento():
    if request.method == "POST":
        venta = request.form['venta']
        medicamento = request.form['medicamento']
        cantidad = request.form['cantidad']
        descuento = request.form['descuento']

        print('aquiii')
        print(descuento)
        print(venta)
        print(medicamento)
        print(cantidad)

        # BUSCAMOS EL MEDICAMENTO ESTA EN LA FACTURA

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from Det_venta where cod_venta_1 = ? and cod_producto_1 = ? and precio_venta = ?"
        cursor.execute(query,(venta,medicamento,descuento))
        existe = cursor.fetchone()

        if existe:

            conn = conectar()
            cursor = conn.cursor()
            query = 'UPDATE Det_venta set cantidad += ? where cod_detalle = ?'
            cursor.execute(query, (cantidad,existe[0]))
            conn.commit()
            cursor.close()
            conn.close()
        else:

            conn = conectar()
            cursor = conn.cursor()
            query = 'INSERT INTO Det_venta (cod_producto_1,cod_venta_1,Cantidad,precio_venta) VALUES (?,?,?,?)'
            cursor.execute(query, (medicamento,venta,cantidad,descuento))
            conn.commit()
            cursor.close()
            conn.close()
        
        conn = conectar()
        cursor = conn.cursor()
        query = 'update producto set stock -= ? where cod_producto = ?'
        cursor.execute(query, (cantidad,medicamento))
        conn.commit()
        cursor.close()
        conn.close()
       

    return 'hecho'
# FIN DE LA INSERCION DE MEDICAMENTOS EN LA FACTURA

@bp.route('/totalCaja', methods=['POST'])
def totalCaja():

    num = request.form['num']

    print(num)
    conn = conectar()
    cursor = conn.cursor()
    query = "SELECT SUM(dv.cantidad * p.precio) AS total_venta FROM Det_venta AS dv INNER JOIN producto AS p ON dv.cod_producto_1 = p.cod_producto where dv.cod_venta_1 = ?"
    cursor.execute(query,(num))
    total = cursor.fetchone()
    print(total)
    if total[0]:
        return str(total[0])
    else:
        return '0'

@bp.route('/listadoProductosCaja', methods=['POST'])
def listadoProductosCaja():

    num = request.form['num']
    print(num)


    conn = conectar()
    cursor = conn.cursor()
    query = "select dv.cod_detalle,p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento from Det_venta as dv inner join producto as p on dv.cod_producto_1 = p.cod_producto where dv.cod_venta_1 = ?"
    cursor.execute(query,(num))
    medicamentos = cursor.fetchall()
    

    return render_template('sistema/tablas/tabla-caja.html',medicamentos = medicamentos)

@bp.route('/agregarReceta', methods=['POST'])
def agregarReceta():
    nohay = []
    hay = []

    num = request.form['num']
    cod_atencion = request.form['receta']

    print(num)

    conn = conectar()
    cursor = conn.cursor()

    # Obtener productos de la receta
    query = """SELECT p.cod_producto, a.cantidad, p.nom_producto, p.stock 
               FROM atencion_producto AS a 
               INNER JOIN producto AS p ON a.cod_producto = p.cod_producto 
               WHERE a.cod_atencion = ?"""
    cursor.execute(query, (cod_atencion,))
    receta_productos = cursor.fetchall()

    for cod_producto, cantidad, nom_producto, stock in receta_productos:
        if stock is not None and stock >= cantidad:
            hay.append((cod_producto, cantidad))  # Guardamos solo los productos con stock suficiente
        else:
            nohay.append(nom_producto)

    

    # Insertar solo los productos con stock suficiente en Det_venta
    insert_query = """INSERT INTO Det_venta (cod_producto_1, cod_venta_1, Cantidad, precio_venta) 
                      VALUES (?, ?, ?, 0)"""

    for cod_producto, cantidad in hay:
        cursor.execute(insert_query, (cod_producto, num, cantidad))

    conn.commit()
    cursor.close()
    conn.close()

    print(nohay)
    # Si no hay productos insertados, evitamos la consulta
    if not hay:
        return render_template('sistema/tablas/tabla-caja.html', medicamentos=[], otros=nohay)

    # Conectar de nuevo para obtener solo los productos que se insertaron en Det_venta
    conn = conectar()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(hay))  # Crear placeholders dinámicos según la cantidad de productos insertados
    query = """SELECT dv.cod_detalle, p.nom_producto, dv.cantidad, p.precio, 
                      p.stock, p.stock_critico, dv.precio_venta as descuento 
               FROM Det_venta AS dv 
               INNER JOIN producto AS p ON dv.cod_producto_1 = p.cod_producto 
               WHERE dv.cod_venta_1 = ? 
               AND dv.cod_producto_1 IN ({})""".format(placeholders)
    
    # Extraer solo los códigos de producto de los que se insertaron
    params = [num] + [prod[0] for prod in hay]  
    cursor.execute(query, params)
    medicamentos = cursor.fetchall()

    cursor.close()
    conn.close()

    print(nohay)
    print("Productos sin stock:", nohay)
    print("Productos con stock:", hay)

    return render_template('sistema/tablas/tabla-caja.html', medicamentos=medicamentos, otros = nohay)





@bp.route('/buscarReceta', methods=['POST'])
def buscarReceta():

    codigo = request.form['receta']
   

    print(codigo)
    conn = conectar()
    cursor = conn.cursor()
    query = "select p.cod_producto,a.cantidad from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ?"
    cursor.execute(query,(codigo))
    receta = cursor.fetchall()

    print(receta)
    if receta:
        return 'receta'
    else:
        conn = conectar()
        cursor = conn.cursor()
        query = "select * FROM venta where cod_estado = 15 and cod_venta = ?"
        cursor.execute(query,(codigo))
        orden = cursor.fetchall()

        if orden:
            return 'orden'
        else:

            return 'no'
    


@bp.route('/validarFactura', methods=['POST'])
def validarFactura():
    if request.method == "POST":
        num = request.form['num']
    
        conn = conectar()
        cursor = conn.cursor()
        query = "select *  from venta where cod_venta = ? and cod_estado = 8"
        cursor.execute(query,(num))
        tiene = cursor.fetchone()
        
        if tiene:
            return 'si'
        else:
            return 'no'
        
@bp.route('/validarProductos', methods=['POST'])
def validarProductos():
    if request.method == "POST":
        num = request.form['num']
    
        conn = conectar()
        cursor = conn.cursor()
        query = "select dv.cod_detalle,p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento from Det_venta as dv inner join producto as p on dv.cod_producto_1 = p.cod_producto where dv.cod_venta_1 = ?"
        cursor.execute(query,(num))
        tiene = cursor.fetchone()
        
        if tiene:
            return 'si'
        else:
            return 'no'

# INICIO DE LA CARGA DE LA TABLA
@bp.route('/tablaCompras', methods=['POST'])
def tablaCompras():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = "SELECT v.cod_venta, CONVERT(DATE, v.fecha_venta) AS fecha,FORMAT(v.fecha_venta, 'HH:mm') AS hora, cred.usuario AS vendedor, SUM(dv.cantidad * p.precio - dv.precio_venta) AS total_venta, e.NombreEstado AS estado FROM venta AS v INNER JOIN cliente AS vendedor ON vendedor.num_cliente = v.vendedor INNER JOIN Det_venta AS dv ON v.cod_venta = dv.cod_venta_1 INNER JOIN producto AS p ON dv.cod_producto_1 = p.cod_producto INNER JOIN estado AS e ON v.cod_estado = e.id_estado INNER JOIN credenciales as cred on vendedor.id_credencial = cred.id_credencial GROUP BY v.cod_venta, CONVERT(DATE, v.fecha_venta), FORMAT(v.fecha_venta, 'HH:mm'), vendedor.nombres_cliente, vendedor.apellidos_cliente, e.NombreEstado, cred.usuario;"
        cursor.execute(query)
        ventas = cursor.fetchall()

        return render_template('sistema/tablas/tabla_ventas.html', ventas=ventas)
        
    else:
        return "No"

#  FIN CARGA DE LA TABLA

# DETALLE DE LA FACTURA
@bp.route('/detalleFactura', methods=['POST'])
def detalleFactura():

    if request.method == "POST":

        num = request.form['num']

        conn = conectar()
        cursor = conn.cursor()
        query = "select p.nom_producto,d.cantidad,d.precio_venta as descuento,p.precio from Det_venta as d  inner join producto as p on d.cod_producto_1 = p.cod_producto where d.cod_venta_1 = ?"
        cursor.execute(query,(num))
        detalle = cursor.fetchall()


        conn = conectar()
        cursor = conn.cursor()
        query = "SELECT v.cod_venta, CONVERT(DATE, v.fecha_venta) AS fecha,FORMAT(v.fecha_venta, 'HH:mm') AS hora,c.nombres_cliente + ' ' + c.apellidos_cliente AS cliente, cred.usuario AS vendedor, SUM(dv.cantidad * p.precio - dv.precio_venta) AS total_venta, e.NombreEstado AS estado FROM venta AS v INNER JOIN cliente AS vendedor ON vendedor.num_cliente = v.vendedor INNER JOIN Det_venta AS dv ON v.cod_venta = dv.cod_venta_1 INNER JOIN producto AS p ON dv.cod_producto_1 = p.cod_producto INNER JOIN estado AS e ON v.cod_estado = e.id_estado INNER JOIN cliente AS c on v.num_cliente = c.num_cliente INNER JOIN credenciales as cred on vendedor.id_credencial = cred.id_credencial where cod_venta = ? GROUP BY v.cod_venta, CONVERT(DATE, v.fecha_venta), FORMAT(v.fecha_venta, 'HH:mm'),c.nombres_cliente,c.apellidos_cliente, vendedor.nombres_cliente, vendedor.apellidos_cliente, e.NombreEstado,cred.usuario ;"
        cursor.execute(query,(num))
        general = cursor.fetchall()

        return render_template('sistema/modales/modal_detalle_factura.html', detalle=detalle, general = general)
        
    else:
        return "No"

# FIN DETALLE DE LA FACTURA

# INICIO DEL MODAL DE REGISTRAR UNA VENTA
@bp.route('/modalAgregarVenta', methods=['POST'])
def modalAgregarVenta():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = 'select * from proveedor where id_estado = 1'
        cursor.execute(query)
        proveedores = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = 'select * from unidades '
        cursor.execute(query)
        unidades = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = 'select * from tipo '
        cursor.execute(query)
        categoria = cursor.fetchall()

        
        return render_template('sistema/modales/modal_agregar_venta.html', proveedores = proveedores,unidades = unidades,categorias = categoria)
        
    else:
        return "No"
# FIN DEL AGREGAR VENTA
# FIN MODULO DE VENTAS

# INICIO DEL MODULO DE CONSULTAS
@bp.route('/nuevaConsulta')
@login_required
def nuevaConsulta():
    return render_template('sistema/agendar_consulta.html')


@bp.route('/traerCitas')
def traerCitas():
    
    conn = conectar()
    cursor = conn.cursor()
    query = "select a.cod_atencion,c.nombres_cliente,a.fecha_atencion,e.NombreEstado from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente INNER JOIN estado as e on a.id_estado = e.id_estado where e.NombreEstado = 'AGENDADO'"
    cursor.execute(query)
    agendas = cursor.fetchall()
    agenda= []
    for fila in agendas:
        fecha_inicio = fila[2]
        fecha_fin = fecha_inicio + timedelta(minutes=30)  # Suma 30 minutos a la hora de inicio

        agendas = {
            'numero': fila[0],
            'cliente': fila[1],
            'estado': fila[3],
            'fecha': fecha_inicio.strftime('%Y-%m-%d %H:%M:%S'),  
            'fechafin': fecha_fin.strftime('%Y-%m-%d %H:%M:%S') 
        }
        agenda.append(agendas)

    return ''+str(agenda)


@bp.route('/modalAgendar', methods=['POST'])
@login_required
def modalAgendar():
    fecha = request.form['fecha']

    conn = conectar()
    cursor = conn.cursor()
    query = "select num_cliente,nombres_cliente + ' ' + apellidos_cliente as Nombre from cliente "
    cursor.execute(query)
    clientes = cursor.fetchall()

    conn = conectar()
    cursor = conn.cursor()
    query = "select cod_tipo,tipo from tipo_atencion "
    cursor.execute(query)
    atencion = cursor.fetchall()

    

    return render_template('sistema/modales/programar_cita.html', fecha = fecha,clientes = clientes,atencion = atencion)


@bp.route('/modalDetalleCita', methods=['POST'])
@login_required
def modalDetalleCita():
    num = request.form['num']

    

    conn = conectar()
    cursor = conn.cursor()
    query = "SELECT a.cod_atencion,m.idMascota,CONVERT(DATE, a.fecha_atencion) AS fecha_atencion, CONVERT(TIME, a.fecha_atencion) AS hora_atencion,c.num_cliente,c.nombres_cliente + ' ' + c.apellidos_cliente AS Nombre,e.NombreEstado,m.Nombre_mascota,es.nom_especie,t.tipo,a.peso,a.altura,a.temperatura,a.descripcion FROM atencion AS a INNER JOIN cliente AS c ON a.num_cliente = c.num_cliente INNER JOIN estado AS e ON a.id_estado = e.id_estado INNER JOIN mascota AS m ON a.idMascota = m.idMascota INNER JOIN tipo_atencion AS t ON a.tipo_atencion = t.cod_tipo INNER JOIN raza AS r ON m.id_raza = r.id_raza INNER JOIN especie AS es ON r.id_especie = es.id_especie where a.cod_atencion = ?"
    cursor.execute(query,(num))
    datos = cursor.fetchall()

    conn = conectar()
    cursor = conn.cursor()
    query = "select id_raza,nombre_raza from raza"
    cursor.execute(query)
    raza = cursor.fetchall()

    conn = conectar()
    cursor = conn.cursor()
    query = "select cod_tipo,tipo from tipo_atencion"
    cursor.execute(query)
    tipo = cursor.fetchall()

    conn = conectar()
    cursor = conn.cursor()
    query = "select id_especie,nom_especie from especie"
    cursor.execute(query)
    especies = cursor.fetchall()

    

    return render_template('sistema/modales/modal_detalle_cita.html',datos = datos,razas = raza,especies = especies,tipos = tipo)



@bp.route('/horasDisponibles', methods=['POST', 'GET'])
@login_required
def horasDisponibles():
    fecha = request.form['fecha']  # Fecha en formato 'YYYY-MM-DD'

    conn = conectar()
    cursor = conn.cursor()
    
    # Obtener las horas ocupadas en el día seleccionado
    query = """
        SELECT CONVERT(varchar(5), fecha_atencion, 108) AS hora_atencion 
        FROM atencion 
        WHERE CONVERT(date, fecha_atencion) = ?;
    """
    cursor.execute(query, (fecha,))
    ocupadas = cursor.fetchall()

    # Convertir a una lista de horas ocupadas en formato datetime
    horas_ocupadas = [datetime.strptime(hora[0], '%H:%M') for hora in ocupadas]

    # Definir los intervalos de horario de apertura
    horarios = [
        ('08:00', '12:00'),  # Bloque de la mañana
        ('13:00', '17:00')   # Bloque de la tarde
    ]

    # Generar lista de horas posibles en intervalos de 45 minutos en formato de 12 horas
    intervalos_disponibles = []
    for inicio, fin in horarios:
        hora_actual = datetime.strptime(inicio, '%H:%M')
        hora_fin = datetime.strptime(fin, '%H:%M')

        while hora_actual + timedelta(minutes=45) <= hora_fin:
            # Verificar si el intervalo está ocupado
            intervalo_ocupado = any(
                ocupada <= hora_actual < ocupada + timedelta(minutes=45)
                for ocupada in horas_ocupadas
            )
            if not intervalo_ocupado:
                # Convertir a formato de 12 horas con AM/PM
                intervalos_disponibles.append(hora_actual.strftime('%I:%M %p'))
            hora_actual += timedelta(minutes=45)

    # Cerrar la conexión
    cursor.close()
    conn.close()

    return jsonify({"horas_disponibles": intervalos_disponibles})



@bp.route('/traerMascotas', methods=['POST', 'GET'])
@login_required
def traerMascotas():
    cliente = request.form['cliente']  # Fecha en formato 'YYYY-MM-DD'

    conn = conectar()
    cursor = conn.cursor()
    
    # Obtener las horas ocupadas en el día seleccionado
    query = """
        select cod_clienteM,m.idMascota,m.Nombre_mascota from cliente_mascota as cm inner join mascota as m on cm.cod_mascota = m.idMascota 
        WHERE cm.cod_cliente = ?;
    """
    cursor.execute(query, (cliente,))
    mascotas = cursor.fetchall()

    mascotas_list = [{"cod_clienteM": row[0], "idMascota": row[1], "Nombre_mascota": row[2]} for row in mascotas]


    cursor.close()
    conn.close()

    return jsonify({"mascotas": mascotas_list})

@bp.route('/traerRazas', methods=['POST', 'GET'])
@login_required
def traerRazas():
    especie = request.form['especie']  # Fecha en formato 'YYYY-MM-DD'

    conn = conectar()
    cursor = conn.cursor()
    
    # Obtener las horas ocupadas en el día seleccionado
    query = """
        select * from raza where id_especie = ? 
    """
    cursor.execute(query, (especie))
    mascotas = cursor.fetchall()

    mascotas_list = [{"num": row[0], "especie": row[1]} for row in mascotas]


    cursor.close()
    conn.close()

    return jsonify({"razas": mascotas_list})



@bp.route('/agendarCita', methods=['POST'])
def agendarCita():

    cliente = request.form['cliente']
    mascota = request.form['mascota']
    peso = request.form['peso']
    altura = request.form['altura']
    observacion = request.form['observacion']
    hora = request.form['hora']
    fecha = request.form['fecha']
    atencion = request.form['atencion']
    temperatura = request.form['temperatura']

   

    fecha_hora_str = f"{fecha} {hora}"
    fecha_hora = datetime.strptime(fecha_hora_str, "%Y-%m-%d %I:%M %p")

    # Separar el día y el mes
    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    dia = fecha_obj.strftime("%d")  # Día con ceros a la izquierda
    locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8')  # Español de México
    mes = fecha_obj.strftime("%B").capitalize()

    print(mes)

    conn = conectar()
    cursor = conn.cursor()
            # Realiza la inserción
    query = 'INSERT INTO atencion (fecha_atencion,num_cliente,id_estado,num_veterinario,idMascota,tipo_atencion,peso,altura,temperatura,descripcion,costo) VALUES (?,?,?,?,?,?,?,?,?,?,?)'
    cursor.execute(query, (fecha_hora, cliente,10,6,mascota,atencion,peso,altura,temperatura,observacion,0))
    conn.commit()


    conn = conectar()
    cursor = conn.cursor()
    query = "select correo_cliente from cliente where num_cliente = ?"
    cursor.execute(query,(cliente))
    correo = cursor.fetchone()

    # MANDAR EL CORREO CON LA CITA AGENDADA
    enviar_correo(current_app,"Usted tiene una nueva cita",correo[0],'agendar',dia,mes,hora)
    

    return 'done'

@bp.route('/cancelarCita', methods=['POST', 'GET'])
@login_required
def cancelarCita():
    num = request.form['num']  

    conn = conectar()
    cursor = conn.cursor()
            # Realiza la inserción
    query = 'UPDATE atencion set id_estado = 9 where cod_atencion = ?'
    cursor.execute(query, ( num))
    conn.commit()

   

    cursor.close()
    conn.close()

    return 'HECHO'

@bp.route('/reAgendar', methods=['POST'])
def reAgendar():

    num = request.form['id']
    hora = request.form['hora']
    fecha = request.form['fecha']

      # Español de España
    


    fecha_hora_str = f"{fecha} {hora}"
    fecha_hora = datetime.strptime(fecha_hora_str, "%Y-%m-%d %I:%M %p")

    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    dia = fecha_obj.strftime("%d")  # Día con ceros a la izquierda
    locale.setlocale(locale.LC_TIME, 'es') 
    mes = fecha_obj.strftime("%B").capitalize()

    print(dia)

    print(fecha_hora)
    conn = conectar()
    cursor = conn.cursor()
            # Realiza la inserción
    query = 'UPDATE atencion set fecha_atencion = ? where cod_atencion = ?'
    cursor.execute(query, (fecha_hora, num))
    conn.commit()

    conn = conectar()
    cursor = conn.cursor()
    query = "select c.correo_cliente from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente where a.cod_atencion = ?"
    cursor.execute(query,(num))
    correo = cursor.fetchone()

    enviar_correo(current_app,"Usted tiene una nueva cita",correo[0],'agendar',dia,mes,hora)

    return 'done'

@bp.route('/actualizarCita', methods=['POST'])
def actualizarCita():

    num = request.form['num']
    mascota = request.form['mascota']
    peso = request.form['peso']
    altura = request.form['altura']
    observacion = request.form['observacion']
    hora = request.form['hora']
    fecha = request.form['fecha']
    atencion = request.form['atencion']
    temperatura = request.form['temperatura']

   

    fecha_hora_str = f"{fecha} {hora}"

    # Convertir fecha y hora con el formato correcto de 24 horas
    fecha_hora = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M:%S")

    # Separar el día y el mes
    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    dia = fecha_obj.strftime("%d")  # Día con ceros a la izquierda

    # Configurar el idioma para obtener el nombre del mes en español
    locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8')
    mes = fecha_obj.strftime("%B").capitalize()

    conn = conectar()
    cursor = conn.cursor()
            # Realiza la inserción
    query = 'UPDATE atencion set fecha_atencion = ?, idMascota = ?, tipo_atencion = ?, peso = ?,altura = ?, temperatura = ?,descripcion = ? where cod_atencion = ?'
    cursor.execute(query, (fecha_hora, mascota,atencion,peso,altura,temperatura,observacion, num))
    conn.commit()


    return 'done'


@bp.route('/agregarMascota', methods=['POST'])
def agregarMascota():

   
    nombre = request.form['nombre']
    cliente = request.form['cliente']
    raza = request.form['raza']
    sexo = request.form['sexo']
    color = request.form['color']
    edad = request.form['edad']
    fechaHoraIngreso = capturarHora()
   
    conn = conectar()
    cursor = conn.cursor()
            # Realiza la inserción
    query = 'INSERT INTO mascota (Nombre_mascota,id_raza,num_cliente,sexo,color,fecha_ingreso,fecha_nac_mascota,edad,id_estado) VALUES (?,?,?,?,?,?,?,?,1)'
    cursor.execute(query, (nombre, raza,cliente,sexo,color,fechaHoraIngreso,fechaHoraIngreso,edad))
    conn.commit()

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT TOP 1 idMascota FROM mascota ORDER BY idMascota DESC;')
    mascota = cursor.fetchone()
    cursor.close()
    conn.close()

   
    
    return str(mascota[0])
    

    return 'done'


@bp.route('/historialConsultas')
@login_required
def historialConsultas():
    return render_template('sistema/consultas.html')

# TABLA DE CONSULTAS
@bp.route('/tablaConsultas', methods=['POST'])
def tablaConsultas():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_atencion,a.fecha_atencion,c.nombres_cliente + ' ' + c.apellidos_cliente as Nombre,e.NombreEstado,m.Nombre_mascota,es.nom_especie,ta.tipo,a.peso,a.altura,a.temperatura from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente inner join estado as e on a.id_estado = e.id_estado inner join mascota as m on a.idMascota = m.idMascota inner join tipo_atencion as ta on a.tipo_atencion = ta.cod_tipo inner join raza as r on m.id_raza = r.id_raza inner join especie as es on r.id_especie = es.id_especie order by a.cod_atencion ASC"
        cursor.execute(query)
        consultas = cursor.fetchall()

        print(consultas)

        return render_template('sistema/tablas/tabla_consultas.html', consultas=consultas)
        
    else:
        return "No"
    

@bp.route('/detalleConsulta', methods=['POST'])
def detalleConsulta():

    if request.method == "POST":

        num = request.form['num']

        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_atencion,a.fecha_atencion,c.nombres_cliente + ' ' + c.apellidos_cliente as Nombre,e.NombreEstado,m.Nombre_mascota,es.nom_especie,ta.tipo,a.peso,a.altura,a.temperatura,a.descripcion,a.diagnostico from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente inner join estado as e on a.id_estado = e.id_estado inner join mascota as m on a.idMascota = m.idMascota inner join tipo_atencion as ta on a.tipo_atencion = ta.cod_tipo inner join raza as r on m.id_raza = r.id_raza inner join especie as es on r.id_especie = es.id_especie where a.cod_atencion = ? order by a.cod_atencion DESC"
        cursor.execute(query,(num))
        detalle = cursor.fetchall()


        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_detalle,p.nom_producto,p.precio,a.cantidad,a.orientacion from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ?"
        cursor.execute(query,(num))
        consultas = cursor.fetchall()


        print(detalle)
        return render_template('sistema/modales/modal_detalle_consulta.html', detalle=detalle,consultas = consultas)
    else:
        return "No"
    

@bp.route('/atencionDiaria')
def atencionDiaria():
    return render_template('sistema/atencionDiaria.html')

@bp.route('/tablaConsultasDiarias', methods=['POST'])
def tablaConsultasDiarias():

    if request.method == "POST":

        fechaActual = capturarHora()
        print(fechaActual.date())
        print(session['id'])
        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_atencion,a.fecha_atencion,c.nombres_cliente + ' ' + c.apellidos_cliente as Nombre,e.NombreEstado,m.Nombre_mascota,es.nom_especie,ta.tipo,a.peso,a.altura,a.temperatura  from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente inner join estado as e on a.id_estado = e.id_estado inner join mascota as m on a.idMascota = m.idMascota inner join tipo_atencion as ta on a.tipo_atencion = ta.cod_tipo inner join raza as r on m.id_raza = r.id_raza inner join especie as es on r.id_especie = es.id_especie inner join cliente as vet on a.num_veterinario = vet.num_cliente inner join credenciales as cred on cred.id_credencial = vet.id_credencial where a.id_estado = 10 AND CONVERT(DATE, a.fecha_atencion) = ? and vet.num_cliente  = ? order by a.cod_atencion DESC"
        cursor.execute(query,(fechaActual.date(),session['id']))
        consultas = cursor.fetchall()

        print(consultas)
        print('diarias')

        return render_template('sistema/tablas/tabla_consultas_diarias.html', consultas=consultas)
        
    else:
        return "No"
    
@bp.route('/detalleConsultaDiaria', methods=['POST'])
def detalleConsultaDiaria():

    if request.method == "POST":

        num = request.form['num']

        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_atencion,a.fecha_atencion,c.nombres_cliente + ' ' + c.apellidos_cliente as Nombre,e.NombreEstado,m.Nombre_mascota,es.nom_especie,ta.tipo,a.peso,a.altura,a.temperatura,a.descripcion from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente inner join estado as e on a.id_estado = e.id_estado inner join mascota as m on a.idMascota = m.idMascota inner join tipo_atencion as ta on a.tipo_atencion = ta.cod_tipo inner join raza as r on m.id_raza = r.id_raza inner join especie as es on r.id_especie = es.id_especie where a.cod_atencion = ? order by a.cod_atencion DESC"
        cursor.execute(query,(num))
        detalle = cursor.fetchall()

        print(detalle)
        return render_template('sistema/modales/modal_detalle_consulta_diaria.html', detalle=detalle,)
    else:
        return "No"
    
@bp.route('/buscarProductoReceta', methods=['POST'])
def buscarProductoReceta  ():

    if request.method == "POST":
        producto = request.form['producto']

        conn = conectar()
        cursor = conn.cursor()
        query = "select cod_producto,precio,Imagen,stock,nom_producto from producto where nom_producto like ? and Tienda = 'Si'"
        cursor.execute(query,(producto + '%'))
        productos = cursor.fetchall()
        print(productos)
        return render_template('sistema/otros/buscador_productos.html', productos=productos)
        
    else:
        return "No"
    

    

@bp.route('/tablaConsultasProductos', methods=['POST'])
def tablaConsultasProductos():

    if request.method == "POST":
        atencion = request.form['atencion']
        
        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_detalle,p.nom_producto,p.precio,a.cantidad,a.orientacion from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ?"
        cursor.execute(query,(atencion))
        consultas = cursor.fetchall()

        

        return render_template('sistema/tablas/tabla_receta.html', consultas=consultas)
        
    else:
        return "No"
    
@bp.route('/agregarProductosAtencion', methods=['POST'])
def agregarProductosAtencion():

    if request.method == "POST":
        producto = request.form['producto']
        cantidad = request.form['cantidad']
        atencion = request.form['atencion']



        conn = conectar()
        cursor = conn.cursor()
        query = 'INSERT INTO atencion_producto (cod_atencion,cod_producto,cantidad,precio) VALUES (?,?,?,0)'
        cursor.execute(query, (atencion,producto,cantidad))
        conn.commit()
        cursor.close()
        conn.close()
        return 'HECHO'
        
    else:
        return "No"
    
@bp.route('/orientaciones', methods=['POST'])
def orientaciones():

    if request.method == "POST":
        detalle = request.form['detalle']
        orientacion = request.form['orientacion']

        print(detalle)
        print(orientacion)


        conn = conectar()
        cursor = conn.cursor()
        query = 'UPDATE atencion_producto set orientacion = ? where cod_detalle = ?'
        cursor.execute(query, (orientacion,detalle))
        conn.commit()
        cursor.close()
        conn.close()
        return 'HECHO'
        
    else:
        return "No"
    
@bp.route('/eliminarMedicamentoReceta', methods=['POST'])
def eliminarMedicamentoReceta():

    if request.method == "POST":
        detalle = request.form['detalle']



        conn = conectar()
        cursor = conn.cursor()
        query = 'DELETE atencion_producto where cod_detalle = ?'
        cursor.execute(query, (detalle))
        conn.commit()
        cursor.close()
        conn.close()
        return 'HECHO'
        
    else:
        return "No"
    
@bp.route('/recetar', methods=['POST'])
def recetar():

    if request.method == "POST":
        detalle = request.form['atencion']
        diagnostico = request.form['diagnostico']


        conn = conectar()
        cursor = conn.cursor()
        query = 'UPDATE atencion set id_estado = 14, diagnostico = ? where cod_atencion = ?'
        cursor.execute(query, (diagnostico,detalle))
        conn.commit()
        cursor.close()
        conn.close()

        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_detalle,p.nom_producto,p.precio,a.cantidad,a.orientacion from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ?"
        cursor.execute(query,(detalle))
        consultas = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = "select c.correo_cliente  from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente where a.cod_atencion = ?"
        cursor.execute(query,(detalle))
        correo = cursor.fetchone()

        conn = conectar()
        cursor = conn.cursor()
        query = "select diagnostico,cod_atencion from atencion where cod_atencion = ?"
        cursor.execute(query,(detalle))
        diagnostico = cursor.fetchall()

        print(diagnostico)


        enviar_correo_receta(current_app,"Usted tiene una nueva receta",correo[0],'recetar',consultas,diagnostico)


        return 'HECHO'
        
    else:
        return "No"
    
@bp.route('/reenviarReceta', methods=['POST'])
def reenviarReceta():

    if request.method == "POST":
        detalle = request.form['atencion']



        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_detalle,p.nom_producto,p.precio,a.cantidad,a.orientacion from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ?"
        cursor.execute(query,(detalle))
        consultas = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = "select c.correo_cliente  from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente where a.cod_atencion = ?"
        cursor.execute(query,(detalle))
        correo = cursor.fetchone()

        conn = conectar()
        cursor = conn.cursor()
        query = "select diagnostico,cod_atencion from atencion where cod_atencion = ?"
        cursor.execute(query,(detalle))
        diagnostico = cursor.fetchall()

        print(diagnostico)


        enviar_correo_receta(current_app,"Usted tiene una nueva receta",correo[0],'recetar',consultas,diagnostico)


        return 'HECHO'
        
    else:
        return "No"

    
@bp.route('/printReceta', methods=['POST', 'GET'])
def printReceta():
    num = request.args.get('id')

    conn = conectar()
    cursor = conn.cursor()
    query = "select a.cod_atencion,a.fecha_atencion,c.nombres_cliente + ' ' + c.apellidos_cliente as Nombre,e.NombreEstado,m.Nombre_mascota,es.nom_especie,ta.tipo,a.peso,a.altura,a.temperatura,a.descripcion,a.diagnostico from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente inner join estado as e on a.id_estado = e.id_estado inner join mascota as m on a.idMascota = m.idMascota inner join tipo_atencion as ta on a.tipo_atencion = ta.cod_tipo inner join raza as r on m.id_raza = r.id_raza inner join especie as es on r.id_especie = es.id_especie where a.cod_atencion = ? order by a.cod_atencion DESC"
    cursor.execute(query,(num))
    ticket = cursor.fetchone()

    conn = conectar()
    cursor = conn.cursor()
    query = "select a.cod_detalle,p.nom_producto,p.precio,a.cantidad,a.orientacion from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ?"
    cursor.execute(query,(num))
    detalle = cursor.fetchall()

    print(ticket)
    print(detalle)

    fecha_factura = ticket[1].strftime("%Y-%m-%d") if isinstance(ticket[1], datetime) else str(ticket[1])
    hora_factura = ticket[1].strftime("%I:%M %p") if isinstance(ticket[1], datetime) else str(ticket[1])
    

    pdf = FPDF('P', 'mm',  (140, 215.9))
    pdf.set_margins(5.5, 5.5, 5.5)
    pdf.set_display_mode(zoom=100, layout='continuous')
    pdf.add_page()
    
    x = 0
    y = 0
    width = 30
    height = 0 
    imagePath = 'static/sistema/images/logos/logo.png'

    pdf.image(imagePath, x, y, width, height)
    
    pdf.set_font('Arial', 'B', 30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.multi_cell(0, 5, 'Veterinaria El Buen Productor', 0, "C")
    pdf.ln(20)
    
    

    # Configura el tamaño y las posiciones de los elementos en una línea
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 10, 'Consulta No: ', ln=0)  # Sin salto de línea
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 10, str(ticket[0]), ln=0)
    pdf.ln(8)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 5, 'Cliente: ')
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 5, ticket[2].upper())
    pdf.ln(6)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(20, 5, 'Fecha: ', ln=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 5, fecha_factura, ln=0)
    

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(10, 5, 'Hora: ', ln=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(10, 5, hora_factura, ln=1)  # Salto de línea al final

    
    
    

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(18, 5, 'Mascota: ')
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 5, ticket[4].upper())
    

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(15, 5, 'Especie: ')
    pdf.set_font('Arial', '', 10)
    pdf.cell(25, 5, ticket[5].upper())


    pdf.set_font('Arial', 'B', 10)
    pdf.cell(15, 5, 'Tipo: ')
    pdf.set_font('Arial', '', 10)
    pdf.cell(25, 5, ticket[6].upper())
    pdf.ln(6)

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(15, 5, 'Peso: ')
    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 5, str(ticket[7])+'lb')


    pdf.set_font('Arial', 'B', 10)
    pdf.cell(15, 5, 'Altura: ')
    pdf.set_font('Arial', '', 10)
    pdf.cell(20, 5, str(ticket[8])+'cm')

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 5, 'Temperatura: ')
    pdf.set_font('Arial', '', 10)
    pdf.cell(20, 5, str(ticket[9])+'°C')
    pdf.ln(10)

    pdf.set_line_width(0.2) 
    pdf.set_font('Arial', 'B', 10)
    
        # Encabezados de la tabla
    pdf.cell(50, 10, 'Producto', 1)
    pdf.cell(30, 10, 'Cantidad', 1)
    pdf.cell(50, 10, 'Orientaciones', 1)
    pdf.ln(10)  # Salto de línea

    # Iterar sobre los resultados y calcular el descuento
    for fila in detalle:
        nom_producto = str(fila[1]).upper()  # Nombre del producto en mayúsculas
        cantidad = str(fila[3])  # Cantidad comprada
        descuento_raw = str(fila[4])  # Descuento aplicado en porcentaje o monto

        

        # Imprimir los datos en el PDF
        pdf.set_line_width(0.0)  # Establecer un borde más fino

        pdf.set_font('Arial', '', 10)

        # Fila de datos
        pdf.cell(50, 10, nom_producto, 1, 0)  # Borde para la celda de producto
        pdf.cell(30, 10, str(cantidad), 1, 0, 'C')  # Cantidad centrada con borde fino
        
        pdf.cell(50, 10, str(descuento_raw), 1, 0, 'C')  # Descuento centrado con borde y nueva línea

        pdf.ln(10)  # Aumenta el espacio entre filas a 6 unidades

   
    pdf.ln(9)  # Salto de línea

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 10, 'Diagnóstico: ')
    pdf.ln(5)
    pdf.set_font('Arial', '', 10)
    pdf.cell(25, 10, str(ticket[11].upper()))
    pdf.ln(1)

        
    pdf_output = pdf.output(dest='S').encode('latin1') 

    response = make_response(pdf_output)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=ticket.pdf'


    conn = conectar()
    cursor = conn.cursor()

                    
                    # Query de actualización del producto
    query = '''
            UPDATE venta
            SET cod_estado = 7
            WHERE cod_venta = ?
    '''
                    
                    # Ejecutar la consulta SQL
    cursor.execute(query, (num))
    conn.commit()

                    # Cerrar la conexión
    cursor.close()
    conn.close()


    return response

# FIN DEL MODULO DE CONSULTAS


# MODULO DE ADMINISTRACIÓN
@bp.route('/usuarios')
@login_required
def usuarios():
    return render_template('sistema/usuarios.html')

@bp.route('/tablaUsuarios', methods=['POST'])
def tablaUsuarios():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = "select c.num_cliente,c.nombres_cliente + '  ' + c.apellidos_cliente as Nombre,cred.usuario,r.nombre_rol,e.NombreEstado from cliente as c inner join credenciales as cred on cred.id_credencial = c.id_credencial inner join estado as e on c.id_estado = e.id_estado inner join roles as r on cred.rol = r.cod_rol"
        cursor.execute(query)
        productos = cursor.fetchall()
        return render_template('sistema/tablas/tabla_usuarios.html', productos=productos)
        
    else:
        return "No"
    

@bp.route('/detalleUsuarios', methods=['POST'])
def detalleUsuarios():

    if request.method == "POST":

        num = request.form['num']

        conn = conectar()
        cursor = conn.cursor()
        query = "select c.num_cliente,c.nombres_cliente as nombre, c.apellidos_cliente as apellido,cred.usuario,r.nombre_rol,e.NombreEstado,c.correo_cliente,c.direccion_cliente,c.telefono,car.cargo from cliente as c inner join credenciales as cred on cred.id_credencial = c.id_credencial inner join estado as e on c.id_estado = e.id_estado inner join roles as r on cred.rol = r.cod_rol inner join cargo as car on cred.cargo = car.cod_cargo where c.num_cliente = ?"
        cursor.execute(query,(num))
        usuario = cursor.fetchall()


        conn = conectar()
        cursor = conn.cursor()
        query = "select * from roles"
        cursor.execute(query)
        roles = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from cargo"
        cursor.execute(query)
        cargos = cursor.fetchall()



        conn = conectar()
        cursor = conn.cursor()
        query = "select * from estado where NombreEstado = 'Activo' or NombreEstado = 'INACTIVO'"
        cursor.execute(query)
        estados = cursor.fetchall()


        return render_template('sistema/modales/modal_detalle_usuario.html',cargos = cargos, usuario=usuario,roles = roles,estados = estados)
        
@bp.route('/editUsuario',methods = ['GET','POST'])
def editUsuario():
    nombre = request.form['nombre']
    usuario = request.form['usuario']
    contra = request.form['password']
    rol = request.form['rol']
    estado = request.form['estado']
    cargo = request.form['cargo']
    id = request.form['id']
    direccion = request.form['direccion']
    correo = request.form['correo']
    apellidos = request.form['apellido']
    telefono = request.form['telefono']


    conn = conectar()
    cursor = conn.cursor()
    query = "select id_credencial from cliente where num_cliente = ?"
    cursor.execute(query,(id))
    credencial = cursor.fetchone()

    if contra:


        conn = conectar()
        cursor = conn.cursor()

            # Realiza la inserción
        query = 'Update cliente set nombres_cliente = ?,apellidos_cliente = ?,direccion_cliente = ?,correo_cliente = ?,telefono = ?,id_estado = ? where id_credencial = ?'
        cursor.execute(query, (nombre,apellidos,direccion,correo,telefono,estado,id))
        conn.commit()

        conn = conectar()
        cursor = conn.cursor()

            # Realiza la inserción
        query = 'Update credenciales set usuario = ?,contrasena = ?,rol = ?,cargo = ? where id_credencial = ?'
        cursor.execute(query, (usuario,generate_password_hash(contra),rol,cargo,credencial[0]))
        conn.commit()
    else:

        conn = conectar()
        cursor = conn.cursor()

            # Realiza la inserción
        query = 'Update cliente set nombres_cliente = ?,apellidos_cliente = ?,direccion_cliente = ?,correo_cliente = ?,telefono = ?,id_estado = ? where id_credencial = ?'
        cursor.execute(query, (nombre,apellidos,direccion,correo,telefono,estado,id))
        conn.commit()

        conn = conectar()
        cursor = conn.cursor()

            # Realiza la inserción
        query = 'Update credenciales set usuario = ?,rol = ?,cargo = ? where id_credencial = ?'
        cursor.execute(query, (usuario,rol,cargo,credencial[0]))
        conn.commit()

    return 'HECHO'



# PARTE DE LOS PERMISOS

# @bp.route('/detallePermisos', methods=['POST'])
# def detallePermisos():

#     if request.method == "POST":

#         num = request.form['num']

#         conn = conectar()
#         cursor = conn.cursor()
#         query = "select c.num_cliente,c.nombres_cliente as nombre, c.apellidos_cliente as apellido,cred.usuario,r.nombre_rol,e.NombreEstado,c.correo_cliente,c.direccion_cliente,c.telefono,car.cargo from cliente as c inner join credenciales as cred on cred.id_credencial = c.id_credencial inner join estado as e on c.id_estado = e.id_estado inner join roles as r on cred.rol = r.cod_rol inner join cargo as car on cred.cargo = car.cod_cargo where c.num_cliente = ?"
#         cursor.execute(query,(num))
#         usuario = cursor.fetchall()


#         conn = conectar()
#         cursor = conn.cursor()
#         query = "select * from roles"
#         cursor.execute(query)
#         roles = cursor.fetchall()

#         conn = conectar()
#         cursor = conn.cursor()
#         query = "select * from cargo"
#         cursor.execute(query)
#         cargos = cursor.fetchall()



#         conn = conectar()
#         cursor = conn.cursor()
#         query = "select * from estado where NombreEstado = 'Activo' or NombreEstado = 'INACTIVO'"
#         cursor.execute(query)
#         estados = cursor.fetchall()


#         return render_template('sistema/modales/modal_permiso.html',cargos = cargos, usuario=usuario,roles = roles,estados = estados)
        

@bp.route('/modalAgregarUsuario', methods=['POST'])
def modalAgregarUsuario():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from roles"
        cursor.execute(query)
        roles = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from cargo"
        cursor.execute(query)
        cargos = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from estado where NombreEstado = 'Activo' or NombreEstado = 'INACTIVO'"
        cursor.execute(query)
        estados = cursor.fetchall()

        
        return render_template('sistema/modales/modal_agregar_usuario.html', cargos = cargos,roles = roles,estados = estados)
        
    else:
        return "No"



@bp.route('/nuevoUsuario',methods = ['GET','POST'])
def nuevoUsuario():
    nombre = request.form['nombre']
    usuario = request.form['usuario']
    contra = request.form['password']
    rol = request.form['rol']
    estado = request.form['estado']
    cargo = request.form['cargo']
    direccion = request.form['direccion']
    correo = request.form['correo']
    apellidos = request.form['apellido']
    telefono = request.form['telefono']



    conn = conectar()
    cursor = conn.cursor()
    query = 'INSERT INTO credenciales (usuario,contrasena,Rol,cargo) VALUES (?,?,?,?)'
    cursor.execute(query, (usuario,generate_password_hash(contra),rol,cargo))
    conn.commit()
    cursor.close()
    conn.close()
    conn = conectar()
    cursor = conn.cursor()


    conn = conectar()
    cursor = conn.cursor()
    query = "select top 1 id_credencial from credenciales order by id_credencial desc"
    cursor.execute(query)
    idcredencial = cursor.fetchone()


    conn = conectar()
    cursor = conn.cursor()
    query = 'INSERT INTO cliente (nombres_cliente,apellidos_cliente,id_estado,direccion_cliente,correo_cliente,id_credencial,telefono) VALUES (?,?,?,?,?,?,?)'
    cursor.execute(query, (nombre,apellidos,estado,direccion,correo,idcredencial[0],telefono))
    conn.commit()
    cursor.close()
    conn.close()
    conn = conectar()
    cursor = conn.cursor()

    enviar_correo_registro(current_app,"Usuario creado!!!",correo,'registro',usuario,contra)
    
    

    return 'HECHO'


# FIN MODULO DE ADMINISTRACIÓN

#INICIO DEL MODULO HOSPITALIZACION
@bp.route('/hospitalizacion')
def hospitalizacion():
    return render_template('sistema/hospitalizacion.html')


@bp.route('/tablaHospitalizacion', methods=['POST'])
def tablaHospitalizacion():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = "select h.id_hosp,m.Nombre_mascota,e.nom_especie,ha.habitacion,h.descripcion,h.fecha_hosp,es.NombreEstado from hospitalizacion as h inner join habitaciones as ha on h.id_cuarto = ha.id_habitacion inner join mascota as m on h.idMascota = m.idMascota inner join raza as r on m.id_raza = r.id_raza inner join especie as e on e.id_especie = r.id_especie inner join estado as es on h.id_estado = es.id_estado"
        cursor.execute(query)
        hospitalizacion = cursor.fetchall()
        return render_template('sistema/tablas/tabla_hospitalizacion.html', hospitalizacion=hospitalizacion)
        
    else:
        return "No"
    

@bp.route('/detalleHospitalizacion', methods=['POST'])
def detalleHospitalizacion():

    if request.method == "POST":

        num = request.form['num']

        conn = conectar()
        cursor = conn.cursor()
        query = "select h.id_hosp,m.Nombre_mascota,e.nom_especie,ha.habitacion,h.descripcion,CONVERT(DATE, h.fecha_hosp) AS fecha_hosp,CONVERT(DATE, h.fecha_salida) AS fecha_salida,h.total,es.NombreEstado,c.nombres_cliente + ' '+ apellidos_cliente as nombre from hospitalizacion as h inner join habitaciones as ha on h.id_cuarto = ha.id_habitacion inner join mascota as m on h.idMascota = m.idMascota inner join raza as r on m.id_raza = r.id_raza inner join especie as e on e.id_especie = r.id_especie inner join estado as es on h.id_estado = es.id_estado inner join cliente as c on c.num_cliente = m.num_cliente where h.id_hosp = ?"
        cursor.execute(query,(num))
        hospitalizacion = cursor.fetchall()

        

        return render_template('sistema/modales/modal_detalle_hospitalizacion.html',datos = hospitalizacion)


@bp.route('/modalAgregarHospitalizacion', methods=['POST'])
def modalAgregarHospitalizacion():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from habitaciones"
        cursor.execute(query)
        habitaciones = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = "select idMascota from mascota"
        cursor.execute(query)
        mascotas = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = "select num_cliente, nombres_cliente + ' ' + apellidos_cliente as Nombre  from cliente"
        cursor.execute(query)
        cliente = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from estado where NombreEstado = 'Activo' or NombreEstado = 'INACTIVO'"
        cursor.execute(query)
        estados = cursor.fetchall()

        conn = conectar()
        cursor = conn.cursor()
        query = "select habitaciones.id_habitacion,habitaciones.habitacion from habitaciones inner join estado as e on habitaciones.id_estado = e.id_estado where e.NombreEstado = 'DISPONIBLE' "
        cursor.execute(query)
        cuarto = cursor.fetchall()

        
        return render_template('sistema/modales/modal_agregar_hospitalizacion.html', habitaciones = cuarto,mascotas = mascotas,estados = estados,clientes = cliente)
        
    else:
        return "No"
    

@bp.route('/hospitalizar',methods = ['GET','POST'])
def hospitalizar():
    cliente = request.form['cliente']
    mascota = request.form['mascota']
    cuarto = request.form['cuarto']
    observacion = request.form['observacion']
    fechaSalida = request.form['fechaSalida']

    fechaActual = capturarHora()



    conn = conectar()
    cursor = conn.cursor()
    query = "select costo from habitaciones where id_habitacion = ?"
    cursor.execute(query,(cuarto))
    cuartoPrice = cursor.fetchone()

    #total = valor por noche de la habitacion * cantidad de dias
    fecha_objetivo = datetime.strptime(fechaSalida, '%Y-%m-%d')
    
    # Obtener la fecha y hora actual
    fecha_actual = datetime.now()
    
    # Calcular la diferencia
    diferencia = fecha_objetivo - fecha_actual
    dias_totales = diferencia.days
    total = dias_totales * cuartoPrice[0]

    print(total)
    print(fechaSalida)

    conn = conectar()
    cursor = conn.cursor()
    query = 'INSERT INTO hospitalizacion (fecha_hosp,id_estado,idMascota,fecha_salida,descripcion,total,valor_consulta,id_cuarto) VALUES (?,1,?,?,?,?,?,?)'
    cursor.execute(query, (fechaActual,mascota,fechaSalida,observacion,total,0,cuarto))
    conn.commit()
    cursor.close()
    conn.close()


    conn = conectar()
    cursor = conn.cursor()

            # Realiza la inserción
    query = 'Update habitaciones set id_estado = 13 where id_habitacion = ?'
    cursor.execute(query, (cuarto))
    conn.commit()
    

    return 'HECHO'


@bp.route('/salidaHospitalizacion',methods = ['GET','POST'])
def salidaHospitalizacion():
    id = request.form['id']
    observacion = request.form['observacion']

    fechaActual = capturarHora()

    conn = conectar()
    cursor = conn.cursor()
    query = "select id_cuarto from hospitalizacion where id_hosp = ?"
    cursor.execute(query,(id))
    cuarto = cursor.fetchone()

    conn = conectar()
    cursor = conn.cursor()

            # Realiza la inserción
    query = 'Update hospitalizacion set id_estado = 14,fecha_salida = ? where id_hosp = ?'
    cursor.execute(query, (fechaActual,id))
    conn.commit()


    conn = conectar()
    cursor = conn.cursor()

            # Realiza la inserción
    query = 'Update habitaciones set id_estado = 12 where id_habitacion = ?'
    cursor.execute(query, (cuarto[0]))
    conn.commit()
    

    return 'HECHO'

@bp.route('/hospFact')
def hospFact():
    num = request.args.get('id')

    # Simula la consulta a la base de datos
    conn = conectar()
    cursor = conn.cursor()
    query = """
    select h.id_hosp,m.Nombre_mascota,e.nom_especie,ha.habitacion,h.descripcion,CONVERT(DATETIME, h.fecha_hosp) AS fecha_hosp,CONVERT(DATETIME, h.fecha_salida) AS fecha_salida,h.total,es.NombreEstado,c.nombres_cliente + ' '+ apellidos_cliente as nombre,DATEDIFF(DAY, h.fecha_hosp, h.fecha_salida) AS dias_hospedaje,ha.costo  from hospitalizacion as h 
    inner join habitaciones as ha on h.id_cuarto = ha.id_habitacion inner join mascota as m on h.idMascota = m.idMascota inner join raza as r on m.id_raza = r.id_raza 
    inner join especie as e on e.id_especie = r.id_especie inner join estado as es on h.id_estado = es.id_estado 
    inner join cliente as c on c.num_cliente = m.num_cliente 
    where h.id_hosp = ?
    """
    
    cursor.execute(query, num)
    ticket = cursor.fetchone()

    if not ticket:
        return "Ticket no encontrado", 404

    fecha_factura_ingreso = ticket[5].strftime("%Y-%m-%d") if isinstance(ticket[5], datetime) else str(ticket[5])
    hora_factura_ingreso = ticket[5].strftime("%I:%M %p") if isinstance(ticket[5], datetime) else str(ticket[5])
    
    fecha_factura_salida = ticket[6].strftime("%Y-%m-%d") if isinstance(ticket[6], datetime) else str(ticket[6])
    hora_factura_salida = ticket[6].strftime("%I:%M %p") if isinstance(ticket[6], datetime) else str(ticket[6])

    pdf = FPDF('P', 'mm',  (101.6, 175))
    pdf.set_margins(5.5, 5.5, 5.5)
    pdf.set_display_mode(zoom=100, layout='continuous')
    pdf.add_page()
    
    x = 35
    y = 0
    width = 30
    height = 0 
    imagePath = 'static/sistema/images/logos/logo.png'

    pdf.image(imagePath, x, y, width, height)
    pdf.ln(20)
    pdf.set_font('Arial', 'B', 30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.multi_cell(0, 5, 'Veterinaria El Buen Productor', 0, "C")
    pdf.ln(1)
    pdf.set_font('Arial', 'B', 10)
    pdf.multi_cell(0, 5, 'FACTURA DE HOSPITALIZACIÓN', 0, "C")
    pdf.ln(1)
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Factura No: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(30, 10, str(ticket[0]))
    pdf.ln(6)
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Fecha Ingreso: ')
    pdf.set_font('Arial', '', 7.5)  # Cambia a fuente normal si lo prefieres
    pdf.cell(30, 10, fecha_factura_ingreso)  # Espacio suficiente para la fecha
    pdf.ln(6)

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Hora Ingreso: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(30, 10, hora_factura_ingreso)  # Espacio suficiente para la hora

    pdf.ln(5)  
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Fecha Salida: ')
    pdf.set_font('Arial', '', 7.5)  # Cambia a fuente normal si lo prefieres
    pdf.cell(30, 10, fecha_factura_salida)  # Espacio suficiente para la fecha
    pdf.ln(6)

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Hora Salida: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(30, 10, hora_factura_salida)  # Espacio suficiente para la hora

    pdf.ln(5)  
    

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Cliente: ')
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(20, 10, ticket[9].upper())
    pdf.ln(6)


    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Mascota: ')
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(20, 10, ticket[1].upper())
    pdf.ln(6)
    pdf.ln(10)
    
        
    
    # pdf.set_font('Arial', 'B', 7.5)
    # pdf.cell(25, 10, 'Habitación: ')
    # pdf.set_font('Arial', '', 7.5)
    # pdf.cell(25, 10, ticket[4])
    # pdf.ln(9)

    pdf.set_line_width(0.2) 
    pdf.set_font('Arial', 'B', 7.5)
    
        # Encabezados de la tabla
    pdf.cell(30, 10, 'Habitación', 1)
    pdf.cell(15, 10, 'Dias', 1)
    pdf.cell(15, 10, '', 1)
    pdf.cell(30, 10, 'Subtotal', 1)
    pdf.ln(10)  # Salto de línea

    # Iterar sobre los resultados y calcular el descuento
    
    nom_producto = str(ticket[3]).upper()  # Nombre del producto en mayúsculas
    cantidad = float(ticket[10])  # Cantidad comprada
    precio = float(ticket[11])  # Precio unitario
   

        # Imprimir los datos en el PDF
    pdf.set_line_width(0.0)  # Establecer un borde más fino

    pdf.set_font('Arial', '', 7.5)
    
        # Fila de datos
    pdf.cell(30, 10, nom_producto, 1, 0)  # Borde para la celda de producto
    pdf.cell(15, 10, str(cantidad), 1, 0, 'C')  # Cantidad centrada con borde fino
    pdf.cell(15, 10, '', 1)
    pdf.cell(30, 10, str(precio), 1)
    pdf.ln(10)  # Aumenta el espacio entre filas a 6 unidades

    pdf.set_font('Arial', 'B', 7.5)  # Título "Total"
    pdf.cell(25, 30, 'Total: ')
    pdf.set_font('Arial', '', 30)  # Aumentar el tamaño de la fuente para el valor
    pdf.cell(65, 30, 'C$ '+str(ticket[7]), 0, 1, 'R')  # Alinear a la derecha
    pdf.ln(9)  # Salto de línea

        
    pdf_output = pdf.output(dest='S').encode('latin1') 

    response = make_response(pdf_output)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=ticket.pdf'

    return response






#FIN DEL MODULO DE HOSPITALIZACION