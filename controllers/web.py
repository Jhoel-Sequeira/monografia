# controllers/web.py
from flask import Blueprint

from datetime import datetime, date, timedelta
import json
from conexion import conectar

from flask import Flask, jsonify, redirect, render_template, request, send_file, session, url_for

from werkzeug.security import check_password_hash, generate_password_hash

import jinja2
from jinja2 import Environment



from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF
import smtplib

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


# LOGIN 

@bp.route('/login', methods=['POST'])
def login():
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
                    session['id'] = rows[0]
                    session['nombre'] = rows[1]
                    session["pass"] = contraseña
                    session['rol'] = rows[6]

                    if session['rol'] == 'administrador' or session['rol'] != 'usuario':
                         return redirect('/sistema')  # Cambia esto por la ruta correcta de sistema.py
                    else:
                        #session['last_seen'] = datetime.now()
                        
                        return 'exito'

                    
            else:
               return 'error'
    return 'error'



# FIN LOGIN

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
    
    

# Fin buscador de la tienda


# RESTAR PRODUCTO DEL CARRITO
@bp.route('/restarProducto', methods=['POST'])
def restarProducto():

    if request.method == "POST":
        
        producto = request.form['producto']
        print(producto)

        conn = conectar()
        cursor = conn.cursor()
        query = 'select cod_producto,cantidad from detalle_carrito where cod_detalle = ?'
        cursor.execute(query,(producto))
        datos = cursor.fetchone()

        if datos[0] <= 1:
            return 'no'



        conn = conectar()
        cursor = conn.cursor()
        query = 'UPDATE detalle_carrito set cantidad -= 1 where cod_detalle = ?'
        cursor.execute(query,(producto))
        conn.commit()
        cursor.close()
        conn.close()

        conn = conectar()
        cursor = conn.cursor()
        query = 'select cantidad from detalle_carrito where cod_detalle = ?'
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
        query = 'select cod_producto,cantidad from detalle_carrito where cod_detalle = ?'
        cursor.execute(query,(producto))
        product = cursor.fetchone()

        cantidad = product[1]

        #AQUI REVISAMOS EL STOCK DEL MATERIAL QUE ESTA EN EL CARRITO
        conn = conectar()
        cursor = conn.cursor()
        query = 'select stock from producto where cod_producto = ?'
        cursor.execute(query,(product[0]))
        stock = cursor.fetchone()

        if cantidad + 1 <= stock[0]:


            conn = conectar()
            cursor = conn.cursor()
            query = 'UPDATE detalle_carrito set cantidad += 1 where cod_detalle = ?'
            cursor.execute(query,producto)
            conn.commit()
            cursor.close()
            conn.close()

            conn = conectar()
            cursor = conn.cursor()
            query = 'select cantidad from detalle_carrito where cod_detalle = ?'
            cursor.execute(query,(producto))
            datos = cursor.fetchone()
            
            return str(datos[0])
        else:
            return 'Sin Stock'
    else:
        return "No"
    
    return render_template('web/otros/buscador_productos.html')
# Fin RESTA DE PRODUCTO
# MANDAR ORDEN DE COMPRA
@bp.route('/mandarSalida', methods=["POST"])
def mandarSalida():
    num = request.form['id']
    tempPdfFilePath = r'C:\Users\JHOEL SEQUEIRA\Documents\GitHub\monografia\ordenCompra\Orden.pdf'

    conn = conectar()
    cursor = conn.cursor()

    # Consulta SQL para obtener los datos del ticket
    query = """
    SELECT sm.NumSalida, t.Tramportista, c.Placa, r.Rastra, con.NombreConductor, p.NombreProveedor, 
    m.NombreMaterial, sm.PesoBruto, sm.PesoTara, sm.PesoTara2, sm.PesoNeto, sm.Observacion, sm.FechaIngreso, sm.FechaSalida 
    FROM SalidaMaterial as sm 
    INNER JOIN Camiones as c ON sm.NumCamion = c.NumCamion 
    INNER JOIN Tramportistas as t ON sm.NumTramportista = t.NumTramportista 
    INNER JOIN Rastras as r ON r.NumRastra = sm.NumRastra
    INNER JOIN Materiales as m ON sm.NumMaterial = m.NumMaterial 
    INNER JOIN Proveedores as p ON sm.NumProveedor = p.NumProveedor 
    INNER JOIN Conductores as con ON sm.NumConductor = con.NumConductor 
    WHERE sm.NumSalida = ?
    """

    cursor.execute(query, (num,))
    ticket = cursor.fetchone()

    fecha_ingreso = ticket[12].strftime("%Y-%m-%d | %I:%M:%S %p") if isinstance(ticket[12], datetime) else str(ticket[12])
    fecha_salida = ticket[13].strftime("%Y-%m-%d | %I:%M:%S %p") if isinstance(ticket[13], datetime) else str(ticket[13])
    fecha = ticket[13].strftime("%Y-%m-%d") if isinstance(ticket[13], datetime) else str(ticket[13])

    pdf = FPDF('P', 'mm', (101.6, 175))
    pdf.set_margins(5.5, 5.5, 5.5)
    pdf.set_display_mode(zoom=100, layout='continuous')
    pdf.add_page()

    pdf.set_font('Arial', 'B', 30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 14)
    pdf.multi_cell(0, 5, 'Compañía Recicladora de Nicaragua', 0, "C")
    pdf.ln(1)
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'No de Boleta: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(30, 10, str(ticket[0]))
    pdf.ln(6)
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Fecha: ')
    pdf.set_font('Arial', 'B', 7.5)
    pdf.multi_cell(23, 10, fecha)
    pdf.ln(4)
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(20, 10, 'Salida de Material ')
    pdf.ln(8)  

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Placa: ')
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(20, 10, ticket[3])
    pdf.ln(6)
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Conductor: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(25, 10, ticket[4].upper())
    pdf.ln(9)
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Cliente: ')
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(30, 10, ticket[5].upper())
    pdf.ln(9)

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Material: ')
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(20, 10, ticket[6])
    pdf.ln(9)
    
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Peso Total: ')
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, "{:,.2f}".format(float(ticket[7])) + ' lb')
    pdf.ln(6)

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, 'Peso Tara: ')
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(25, 10, "{:,.2f}".format(float(ticket[8])) + ' lb')
    pdf.ln(6)

    # pdf.set_font('Arial', 'B', 7.5)
    # pdf.cell(30, 10, 'Peso Tara Adicional: ')
    # pdf.set_font('Arial', '', 7.5)
    # pdf.cell(20, 10,"{:,.2f}".format(float(ticket[9]) - float(ticket[7])) + 'lb')
    pdf.ln(8)

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(30, 10, 'Peso Bruto: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(20, 10, "{:,.2f}".format(float(ticket[10])) + ' lb')
    kg = float(ticket[10]) / 2.2046
    pdf.ln(6)
    

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(30, 10, '')
    pdf.cell(20, 10, "{:,.2f}".format(kg) + ' kg')
    pdf.ln(6)



    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(30, 10, 'Fecha y Hora Ingreso: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(30, 10, fecha_ingreso)
    pdf.ln(4)



    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(30, 10, 'Fecha y Hora Salida: ')
    pdf.set_font('Arial', '', 7.5)
    pdf.cell(30, 10, fecha_salida)
    pdf.ln(4)

    

   

    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(30, 10, 'Observacion: ')
    pdf.ln(6)
    pdf.set_font('Arial', 'B', 7.5)
    pdf.cell(180, 10, ticket[11].upper())
    pdf.ln(6)

    # pdf.set_font('Arial', 'B', 7.5)
    # pdf.cell(30, 10, ticket[12],0, 0, 'C')
    # pdf.ln(3)


    x = 35
    y = 110
    width = 30
    height = 0 
    imagePath = 'static/img/validado.png'

    pdf.image(imagePath, x, y, width, height)

   
    pdf.cell(30, 10, '___________________',0, 0, 'C')
    pdf.cell(30, 10, '___________________',0, 0, 'C')
    pdf.cell(30, 10, '___________________',0, 0, 'C')
    pdf.ln(6)
    pdf.cell(30, 10, 'Digitador',0, 0, 'C')
    pdf.cell(30, 10, 'Verificador',0, 0, 'C')
    pdf.cell(30, 10, 'Proveedor',0, 0, 'C')

    # Guardar el PDF como un archivo temporal
    pdf.output(tempPdfFilePath, 'F')

    # Configurar los detalles del correo
    from_email = 'bascula@crn.com.ni'
    to_email = ['maycol.gonzalez@crn.com.ni', 'david.garache@crn.com.ni', 'aurelio.larios@crn.com.ni', 'exportaciones@crn.com.ni']
    # to_email = ['it@crn.com.ni']
    cc_emails = ['bryan.oviedo@crn.com.ni']
    # cc_emails = ['it@crn.com.ni']
    subject = ticket[3]
    body = f"Se adjunta el checklist validado de la unidad: <b>{ticket[3]}</b><br> Material: <b>{ticket[6]}</b>"

    # Configurar el servidor SMTP
    smtp_server = 'smtp.office365.com'
    smtp_port = 587
    smtp_user = 'bascula@crn.com.ni'
    smtp_password = 'Cbasscula23'

    try:
         # Crear el mensaje de correo
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(to_email)  # Corregido: Convertir la lista de destinatarios a cadena
        msg['Cc'] = ', '.join(cc_emails)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        # Adjuntar el archivo PDF
        with open(tempPdfFilePath, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(tempPdfFilePath)}')
            msg.attach(part)

        # Enviar el correo
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)

        # Eliminar el archivo temporal después de enviar el correo
        os.remove(tempPdfFilePath)
        print('correo enviado')
        return 'Correo enviado con éxito'

    except Exception as e:
        print( {str(e)})
        return f'Error al enviar el correo: {str(e)}'


# FIN ENVIO ORDEN DE COMPRA

# RESTAR PRODUCTO DEL CARRITO
@bp.route('/borrarProducto', methods=['POST'])
def borrarProducto():

    if request.method == "POST":
        
        producto = request.form['producto']
        print(producto)

        conn = conectar()
        cursor = conn.cursor()
        query = 'delete from detalle_carrito where cod_detalle = ?'
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
        query = 'SELECT dc.cod_detalle,p.Imagen, p.nom_producto, dc.cantidad, p.precio, e.NombreEstado FROM carrito_compra AS cc inner join detalle_carrito as dc on cc.id_carrito = dc.cod_carrito INNER JOIN producto AS p ON dc.cod_producto = p.cod_producto INNER JOIN cliente AS c ON cc.num_cliente = c.num_cliente INNER JOIN estado AS e ON cc.id_estado = e.id_estado where cc.num_cliente = ? and cc.id_estado = 2 GROUP BY p.nom_producto, dc.cod_detalle, dc.cantidad, p.precio, e.NombreEstado, p.Imagen;'
        cursor.execute(query,(session['id']))
        datos = cursor.fetchall()
        print(datos)
        if not datos:
            datos = ''

        return render_template('web/otros/traer_productos.html', producto=datos)

@bp.route('/seguimiento', methods=['POST'])
def seguimiento():

        conn = conectar()
        cursor = conn.cursor()
        query = 'SELECT cc.id_carrito,e.NombreEstado as estado from carrito_compra as cc inner join estado as e on cc.id_estado = e.id_estado where cc.num_cliente = ? and cc.id_estado != 2 '
        cursor.execute(query,(session['id']))
        carrito = cursor.fetchall()

        return render_template('web/otros/seguimiento.html', producto=carrito)

@bp.route('/cantidadArticulos', methods=['POST'])
def cantidadArticulos():

        conn = conectar()
        cursor = conn.cursor()
        query = 'SELECT COUNT(DISTINCT p.cod_producto) AS total_productos FROM carrito_compra AS cc INNER JOIN detalle_carrito as dc on cc.id_carrito = dc.cod_carrito inner join producto AS p ON dc.cod_producto = p.cod_producto INNER JOIN cliente AS c ON cc.num_cliente = c.num_cliente INNER JOIN estado AS e ON cc.id_estado = e.id_estado WHERE cc.num_cliente = ? and cc.id_estado = 2;'
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
            query = 'select * from carrito_compra where num_cliente = ? and id_estado = 2'
            cursor.execute(query, (session['id']))
            carrito = cursor.fetchone()
            cursor.close()
            conn.close()

            print(carrito)

            if carrito:


                conn = conectar()
                cursor = conn.cursor()
                query = 'select * from detalle_carrito where cod_producto = ? and cod_carrito = ?'
                cursor.execute(query, (producto,carrito[0]))
                detallecarrito = cursor.fetchone()
                cursor.close()
                conn.close()

                print(detallecarrito)
                if detallecarrito:

                    conn = conectar()
                    cursor = conn.cursor()
                    query = 'UPDATE detalle_carrito set cantidad += ? where cod_detalle = ? and cod_producto = ?'
                    cursor.execute(query,(cantidad,detallecarrito[0],producto))
                    conn.commit()
                    cursor.close()
                    conn.close()
                else:
                    print('else')
                    print()
                    conn = conectar()
                    cursor = conn.cursor()
                    query = 'INSERT INTO detalle_carrito (cod_producto,cantidad,cod_carrito) VALUES (?,?,?)'
                    cursor.execute(query,(producto,cantidad,carrito[0]))
                    conn.commit()
                    cursor.close()
                    conn.close()

            else:

                #INSERTAMOS EL CARRITO
                conn = conectar()
                cursor = conn.cursor()
                query = 'INSERT INTO carrito_compra (num_cliente,id_estado) VALUES (?,2)'
                cursor.execute(query,(session['id']))
                conn.commit()
                cursor.close()
                conn.close()

                #SELECCIONAMOS EL ULTIMO CARRITO AGREGADO
                conn = conectar()
                cursor = conn.cursor()
                query = 'select TOP 1 * from carrito_compra where num_cliente = ? and id_estado = 2 order by id_carrito desc'
                cursor.execute(query, (session['id']))
                car = cursor.fetchone()
                cursor.close()
                conn.close()

                print(car[0])
                #INSERTAMOS EL DETALLE DEL CARRITO
                
                conn = conectar()
                cursor = conn.cursor()
                query = 'INSERT INTO detalle_carrito (cod_producto,cantidad,cod_carrito) VALUES (?,?,?)'
                cursor.execute(query,(producto,cantidad,car[0]))
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
            query = 'select count(*) from carrito_compra  as cc inner join detalle_carrito as dc on cc. id_carrito = dc.cod_carrito where cc.num_cliente = ? and cc.id_estado = 2'
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
    query = 'SELECT dc.cod_detalle,p.Imagen, p.nom_producto, dc.cantidad, p.precio, e.NombreEstado FROM carrito_compra AS cc inner join detalle_carrito as dc on cc.id_carrito = dc.cod_carrito INNER JOIN producto AS p ON dc.cod_producto = p.cod_producto INNER JOIN cliente AS c ON cc.num_cliente = c.num_cliente INNER JOIN estado AS e ON cc.id_estado = e.id_estado where cc.num_cliente = ? and cc.id_estado = 2 GROUP BY p.nom_producto, dc.cod_detalle, dc.cantidad, p.precio, e.NombreEstado, p.Imagen;'
    cursor.execute(query,(session['id']))
    datos = cursor.fetchall()


    conn = conectar()
    cursor = conn.cursor()
    query = 'SELECT SUM(dc.cantidad * p.precio) AS total_factura FROM carrito_compra AS cc inner join detalle_carrito as dc on cc.id_carrito = dc.cod_carrito INNER JOIN producto AS p ON dc.cod_producto = p.cod_producto INNER JOIN cliente AS c ON cc.num_cliente = c.num_cliente WHERE cc.num_cliente = ?'
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

