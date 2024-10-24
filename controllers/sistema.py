# controllers/sistema.py
from datetime import datetime
import os
from fpdf import FPDF
from flask import Blueprint, jsonify, render_template, request,session,redirect,make_response
from functools import wraps
from conexion import conectar
import pandas as pd

from controllers.excel import GenerarExcel_3

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


@bp.route('/facturar', methods=['POST', 'GET'])
def facturar():
    num = request.args.get('id')

    conn = conectar()
    cursor = conn.cursor()

    # Consulta SQL para obtener los datos del ticket
    query = """
    	select v.cod_venta,v.fecha_venta,c.nombres_cliente + ' ' + c.apellidos_cliente as cliente, vendedor.nombres_cliente + ' ' +vendedor.apellidos_cliente as vendedor  from venta as v inner join cliente as c on v.num_cliente = c.num_cliente  INNER JOIN cliente as vendedor on vendedor.num_cliente = v.vendedor
    where v.cod_venta = ?
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
            	select v.cod_venta,v.fecha_venta, vendedor.nombres_cliente + ' ' +vendedor.apellidos_cliente as vendedor  from venta as v INNER JOIN cliente as vendedor on vendedor.num_cliente = v.vendedor
        where v.cod_venta = ?
        """


        cursor.execute(query, (num))
        ticket = cursor.fetchone()

    conn = conectar()
    cursor = conn.cursor()
    query = "select p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento from Det_venta as dv inner join producto as p on dv.cod_producto_1 = p.cod_producto where dv.cod_venta_1 = ?"
    cursor.execute(query,(num))
    detalle = cursor.fetchall()

    fecha_factura = ticket[1].strftime("%Y-%m-%d") if isinstance(ticket[1], datetime) else str(ticket[1])
    hora_factura = ticket[1].strftime("%I:%M:%S %p") if isinstance(ticket[1], datetime) else str(ticket[1])
    

    pdf = FPDF('P', 'mm',  (101.6, 175))
    pdf.set_margins(5.5, 5.5, 5.5)
    pdf.set_display_mode(zoom=100, layout='continuous')
    pdf.add_page()
    

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

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(15, 10, 'Hora: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(30, 10, hora_factura)  # Espacio suficiente para la hora

    pdf.ln(10)  
    
    if no_tiene ==1:

        pdf.set_font('Arial', 'B', 7.5)
        pdf.cell(25, 10, 'Cliente: ')
        pdf.set_font('Arial', 'B', 7.5)
        pdf.cell(20, 10, ticket[1])
        pdf.ln(6)
    
        
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Vendedor: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(25, 10, ticket[2].upper())
    pdf.ln(9)


    
        # Encabezados de la tabla
    pdf.cell(40, 10, 'Producto')
    pdf.cell(30, 10, 'Cantidad')
    pdf.cell(30, 10, 'Precio')
    pdf.cell(30, 10, 'Descuento')
    pdf.ln(9)  # Salto de línea

    # Iterar sobre los resultados y calcular el descuento
    for fila in detalle:
        nom_producto = str(fila[0]).upper()  # Nombre del producto en mayúsculas
        cantidad = float(fila[1])  # Cantidad comprada
        precio = float(fila[2])  # Precio unitario
        descuento_raw = float(fila[3])  # Descuento aplicado en porcentaje o monto

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
        pdf.set_font('Arial', '', 7.5)
        pdf.cell(40, 10, nom_producto)
        pdf.cell(30, 10, str(cantidad))
        pdf.cell(30, 10, f"C$ {precio:.2f}")  # Mostrar precio con dos decimales
        pdf.cell(30, 10, f"C$ {descuento_aplicado:.2f}")  # Mostrar descuento con dos decimales
        pdf.ln(9)  # Salto de línea entre filas
        
    pdf_output = pdf.output(dest='S').encode('latin1') 

    response = make_response(pdf_output)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=ticket.pdf'

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

# INICIO DE LA CARGA DE LA TABLA
@bp.route('/tablaCompras', methods=['POST'])
def tablaCompras():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = 'select v.cod_venta,c.nombres_cliente + ' ' + c.apellidos_cliente as cliente,v.fecha_venta,cred.usuario as vendedor,v.total,e.NombreEstado as estado from Det_venta as dv inner join venta as v on v.cod_venta = dv.cod_venta_1 inner join cliente as vendedor on v.vendedor = vendedor.num_cliente inner join credenciales as cred on vendedor.id_credencial = cred.id_credencial inner join cliente as c on v.num_cliente = c.num_cliente inner join producto  as p on dv.cod_producto_1 = p.cod_producto inner join estado as e on v.cod_estado = e.id_estado'
        cursor.execute(query)
        ventas = cursor.fetchall()

        return render_template('sistema/tablas/tabla_ventas.html', ventas=ventas)
        
    else:
        return "No"

#  FIN CARGA DE LA TABLA
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