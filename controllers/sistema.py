# controllers/sistema.py
from datetime import datetime, timedelta


import json
import os
import locale
from fpdf import FPDF
from flask import Blueprint, jsonify, render_template, request,session,redirect,make_response,current_app,url_for
from functools import wraps
from conexion import conectar
from conexion import conectarBack
from werkzeug.security import check_password_hash, generate_password_hash
import pandas as pd
from run import socketio


from controllers.excel import GenerarExcel_3
from controllers.correo import enviar_correo, enviar_correo_receta, enviar_correo_registro

backups_dir = 'C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\Backup'


ruta_absoluta_backups = os.path.abspath(backups_dir)
def capturarHora():
    hi = datetime.now()
    return hi

def capturarHoraBack():
    hi = datetime.now()
    return hi.strftime('%Y%m%d_%H%M%S')

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

@bp.route('/consultas')
@login_required
def consultas():
    
    return render_template('web/home.html')

@bp.route('/deslog')
def deslog():
    session.clear()
    return redirect(url_for('web.home'))

# MODULO: INVENTARIO
# INICIO DEL MODULO DE Movimientos Inventario
@bp.route('/movimientosInventario')
@login_required
def movimientosInventario():
    return render_template('sistema/movimientoInventario.html')



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


        conn = conectar()
        cursor = conn.cursor()
        query = 'select * from tipo'
        cursor.execute(query)
        categoria = cursor.fetchall()


        return render_template('sistema/tablas/tabla_inventario.html', productos=productos, categoria = categoria)
        
    else:
        return "No"


@bp.route('/tablaBackups', methods=['POST'])
def tablaBackups():
    if request.method == "POST":
        archivos = []
        base_path = os.path.abspath(backups_dir)  # ruta absoluta

        for filename in os.listdir(base_path):
            if filename.endswith('.sql') or filename.endswith('.bak') or filename.endswith('.zip'):
                path = os.path.join(base_path, filename)
                tamano = os.path.getsize(path)
                fecha_mod = os.path.getmtime(path)
                archivos.append({
                    'nombre': filename,
                    'tamano': tamano,
                    'fecha_modificacion': datetime.fromtimestamp(fecha_mod).strftime('%d/%m/%Y %H:%M')

                })

        archivos = sorted(archivos, key=lambda x: x['fecha_modificacion'], reverse=True)

        return render_template('sistema/tablas/tabla-backups.html', backups=archivos)
    else:
        return "Método no permitido"


@bp.route('/tablaLotes', methods=['POST'])
def tablaLotes():

    if request.method == "POST":
        id = request.form['id']
        conn = conectar()
        cursor = conn.cursor()
        query = """SELECT 
                    cod_lote,
                    lote,
                    CAST(FechaVencimiento AS DATE) AS FechaVencimiento,
                    cantidad
                FROM 
                    lotes
                WHERE 
                    idProducto = ?
                ORDER BY 
                    FechaVencimiento ASC;
                """
        cursor.execute(query,(id))
        productos = cursor.fetchall()


       
        print(id)
        print(productos)
        return render_template('sistema/tablas/tabla-lotes.html', productos=productos)
        
    else:
        return "No"

@bp.route('/tablaMovimientos', methods=['POST'])
def tablaMovimientos():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = 'select a.num_ajuste, p.nom_producto,a.fecha_hora,a.cantidad,a.tipo_ajuste,a.comentario from ajuste_inventario as a inner join producto as p on a.cod_producto = p.cod_producto order by a.num_ajuste desc'
        cursor.execute(query)
        productos = cursor.fetchall()

        print(productos)


        return render_template('sistema/tablas/tabla_ajustes.html', productos=productos)
        
    else:
        return "No"


@bp.route('/addFiltroInv', methods=["POST", "GET"])
def addFiltroInv():
    if request.method == "POST":
        filtro = request.form['filtro']
        # cur = mysql.connection.cursor()
        # cur.execute("select v.Id_Verificacion,v.Fecha,v.PO,v.NoBoleta,pc.NombrePuntoCompra,e.NombreEstado, p.NombreProveedor from tb_verificacion as v inner join tb_proveedor as p ON v.IdProveedor = p.Id_Proveedor inner join tb_puntocompra as pc ON v.IdPuntoCompra = pc.Id_PuntoCompra inner join tb_estado as e on v.IdEstado = e.Id_Estado where v.PO like %s and v.IdEstado = 6",[po+'%'])
        # verificaciones = cur.fetchall()
        # mysql.connection.commit()
        # primero es tener la consulta base
        data = json.loads(filtro)
        headers = []
        if data:
            consultaBase = '''select p.cod_producto,p.nom_producto,e.NombreEstado,pro.cod_proveedor,t.tipos,p.precio,p.stock,p.stock_critico from producto as p  inner join estado as e on p.id_estado = e.id_estado inner join tipo as t on p.tipo_producto = t.cod_tipo inner join proveedor as pro on p.cod_proveedor = pro.cod_proveedor where'''
            for clave in data.keys():
                headers.append(clave)
            consulta = ''
            contador = 0
            valores_stock = []
            for value in data.values():
                print(headers[contador] )
                if "stock" in headers[contador].lower():
                    valores_stock.append(int(value))
                    if valores_stock:
                        stock_min = min(valores_stock)
                        stock_max = max(valores_stock)
                        consulta += f' p.stock BETWEEN {stock_min} AND {stock_max} AND '
                elif headers[contador] == "cod_proveedor":
                    a = 1
                    
                    conn = conectar()
                    cursor = conn.cursor()
                    query = 'SELECT cod_proveedor from proveedor where nom_proveedor = ?'
                    cursor.execute(query,(value))
                    idprov = cursor.fetcone()

                    print("aqui se muestra el proveedor:")
                    print(idprov)

                    if idprov:
                        conn = conectar()
                        cursor = conn.cursor()
                        query = 'SELECT cod_proveedor from proveedor where nom_proveedor = ?'
                        cursor.execute(query,(value))
                        idprov = cursor.fetcone()

                        consulta += 'p.'+headers[contador] + \
                            ' = '+str(idprov[0]) + ' AND '
                    else:
                        conn = conectar()
                        cursor = conn.cursor()
                        query = 'SELECT cod_proveedor from proveedor where nom_proveedor = ?'
                        cursor.execute(query,(value))
                        idprov = cursor.fetcone()
                        # LLAMAMOS AL PROVEEDOR DE NOMBRE TAL
                        cur = mysql.connection.cursor()
                        cur.execute(
                            'SELECT Id_Proveedor from tb_proveedor where NombreProveedor = %s', [value])
                        idprov = cur.fetchone()

                        consulta += 'p.'+headers[contador] + \
                            ' = '+str(idprov[0]) + ' AND '

                    # consulta += 'date(v.'+headers[contador]+') BETWEEN "'+fechas[0]+'" AND "'+''+fechas[1]+'" AND '
                else:
                    
                    
                    consulta += 'p.stock'+' BETWEEN "' + \
                        fechas[0]+'" AND "'+''+fechas[1]+'" AND '
                    
                contador += 1
                # consultaBase += ' AND '+data
            consulta_total = consultaBase+' '+consulta[:-4]
            print(consulta_total)
        else:
             consultaBase = '''select p.cod_producto,p.nom_producto,e.NombreEstado,pro.cod_proveedor,t.tipos,p.precio,p.stock,p.stock_critico from producto as p  inner join estado as e on p.id_estado = e.id_estado inner join tipo as t on p.tipo_producto = t.cod_tipo
            inner join proveedor as pro on p.cod_proveedor = pro.cod_proveedor
            '''
        print(consulta_total)
        conn = conectar()
        cursor = conn.cursor()
        query = " "+consulta_total
        cursor.execute(query)
        productos = cursor.fetchall()    

        conn = conectar()
        cursor = conn.cursor()
        query = 'select * from tipo'
        cursor.execute(query)
        categoria = cursor.fetchall()


     
        return render_template('sistema/tablas/tabla_inventario.html', productos=productos, categoria = categoria)



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


@bp.route('/modalAgregarAjuste', methods=['POST'])
def modalAgregarAjuste():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = 'select * from producto where id_estado = 1'
        cursor.execute(query)
        proveedores = cursor.fetchall()

        

        
        return render_template('sistema/modales/modal_agregar_ajuste.html', proveedores = proveedores)
        
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
    imagen = request.files.get('imagen')


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


@bp.route('/guardarAjuste', methods=['POST'])
def guardarAjuste():

    nombre = request.form['producto']
    cantidad = request.form['cantidad']
    tipo = request.form['tipo']
    comentario = request.form['comentario']
    FechaActual = capturarHora()

    print(nombre)
    print(cantidad)
    print(tipo)
    print(FechaActual)
    
    conn = conectar()
    cursor = conn.cursor()
            # Realiza la inserción
    query = 'INSERT INTO ajuste_inventario (fecha_hora,tipo_ajuste,cod_producto,cantidad,comentario) VALUES (?,?,?,?,?)'
    cursor.execute(query, (FechaActual, tipo,nombre,cantidad,comentario))
    conn.commit()

    if tipo == 'ALTA':
        conn = conectar()
        cursor = conn.cursor()
        query = '''
        UPDATE producto
        SET stock += ?
        WHERE cod_producto = ?
        '''
        cursor.execute(query, (cantidad,nombre))
        conn.commit()
        cursor.close()
        conn.close()
    else:
        conn = conectar()
        cursor = conn.cursor()
        query = '''
        UPDATE producto
        SET stock = CASE 
                    WHEN stock - ? < 0 THEN 0 
                    ELSE stock - ? 
                    END
        WHERE cod_producto = ?;

        '''
        cursor.execute(query, (cantidad,cantidad,nombre))
        conn.commit()
        cursor.close()
        conn.close()
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

@bp.route('/mostrarDetalleAjuste', methods=['POST'])
def mostrarDetalleAjuste():

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

@bp.route('/compras')
@login_required
def compras():
    return render_template('sistema/compras.html')


@bp.route('/backups')
@login_required
def backups():
    return render_template('sistema/backups.html')



@bp.route('/generarBackup', methods=['POST'])
def generarBackup():
    print('Entró a generarBackup')
    hora = capturarHoraBack()
    try:
        nombre_backup = f"backup_{hora}"
        backup_dir = r'C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\Backup'


        # Backup file name
        backup_file = 'Vet_ElBuenProductor_' + nombre_backup + '.bak'

        # Backup command
        backup_command = 'BACKUP DATABASE Vet_ElBuenProductor TO DISK=\'' + os.path.join(backup_dir, backup_file) + '\''
        conn = conectar()
        conn.autocommit = True
        cursor = conn.cursor()
        # Execute the backup command
        cursor.execute(backup_command)
        
        return jsonify({"status": "ok", "mensaje": "Backup generado vía SP", "archivo": nombre_backup})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "mensaje": str(e)}), 500



@bp.route('/caja')
@login_required
def caja():

    conn = conectar()
    cursor = conn.cursor()
    query = "select c.num_cliente, c.nombres_cliente + ' '+ c.apellidos_cliente as Nombre from cliente as c inner join credenciales as cred on c.id_credencial = cred.id_credencial inner join roles as r on cred.rol = r.cod_rol where r.nombre_rol = 'CLIENTE'"
    cursor.execute(query)
    clientes = cursor.fetchall()


    return render_template('sistema/caja.html',clientes = clientes)


@bp.route('/cajaCompra')
@login_required
def cajaCompra():

    conn = conectar()
    cursor = conn.cursor()
    query = "select cod_proveedor,nom_proveedor from proveedor"
    cursor.execute(query)
    clientes = cursor.fetchall()


    return render_template('sistema/cajaCompra.html',clientes = clientes)

@bp.route('/traerId', methods=['POST'])
@login_required
def traerId():

    conn = conectar()
    cursor = conn.cursor()
    query = "select top 1 cod_venta from venta where cod_estado != 8 order by cod_venta desc "
    cursor.execute(query)
    ultimaventa = cursor.fetchone()
    if ultimaventa:
        print('ultimaventa : ',ultimaventa)
        return str(ultimaventa[0]+1)
    else:
        return str(1)
    
@bp.route('/traerIdCompra', methods=['POST'])
@login_required
def traerIdCompra():

    conn = conectar()
    cursor = conn.cursor()
    query = "select top 1 cod_compra from compras where cod_estado != 8 order by cod_compra desc "
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



@bp.route('/cancelarConsulta', methods=['POST'])
@login_required
def cancelarConsulta():

    num = request.form['id']

    conn = conectar()
    cursor = conn.cursor()
    query = "select e.NombreEstado from atencion as a inner join estado as e ON a.id_estado = e.id_estado where cod_atencion = ?"
    cursor.execute(query,(num))
    estado = cursor.fetchone()

    print(estado[0])
    if estado[0] != 'FINALIZADO':
        conn = conectar()
        cursor = conn.cursor()
                        # Query de actualización del producto
        query = '''
                UPDATE atencion
                SET id_estado = 9
                WHERE cod_atencion = ?
        '''
                        
                        # Ejecutar la consulta SQL
        cursor.execute(query, (num))
        conn.commit()

                        # Cerrar la conexión
        cursor.close()
        conn.close()

        return 'Hecho'
    else:
        return 'finalizado'
    
    
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

@bp.route('/crearFacturaCompra', methods=['POST'])
def crearFacturaCompra():
    if request.method == "POST":
        FechaActual = capturarHora()
        cliente1 = request.form['cliente']
        num = request.form['num']

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from compras where cod_compra = ? "
        cursor.execute(query,(num))
        existe = cursor.fetchone()

        if existe:
            return 'ya'
        
        print(cliente1)
        if cliente1:
            conn = conectar()
            cursor = conn.cursor()
            query = 'INSERT INTO compras (fechaCompra,cod_proveedor,cod_estado) VALUES (?,?,8)'
            cursor.execute(query, (FechaActual,cliente1))
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
        cod_detalle = request.form['num']
        cod_venta = request.form['venta']

        # 1. Obtener cantidad y producto desde Det_venta
        conn = conectar()
        cursor = conn.cursor()
        query = """
            SELECT cantidad, cod_producto_1 
            FROM Det_venta 
            WHERE cod_venta_1 = ? AND cod_detalle = ?
        """
        cursor.execute(query, (cod_venta, cod_detalle))
        detalle = cursor.fetchone()

        if not detalle:
            cursor.close()
            conn.close()
            return 'Detalle no encontrado', 404

        cantidad, cod_producto = detalle

        # 2. Obtener los lotes que se usaron para esta venta
        query = """
            SELECT cantidadUsada, codLote 
            FROM detalle_venta_lote 
            WHERE codDetalle = ?
        """
        cursor.execute(query, (cod_detalle,))
        lotes_usados = cursor.fetchall()

        # 3. Reintegrar cada cantidad al lote correspondiente
        for cantidad_usada, cod_lote in lotes_usados:
            cursor.execute("""
                UPDATE lotes SET cantidad = cantidad + ? WHERE cod_lote = ?
            """, (cantidad_usada, cod_lote))

        # 4. Eliminar registros en detalle_venta_lote
        cursor.execute("DELETE FROM detalle_venta_lote WHERE codDetalle = ?", (cod_detalle,))

        # 5. Eliminar el Det_venta
        cursor.execute("DELETE FROM Det_venta WHERE cod_venta_1 = ? AND cod_detalle = ?", (cod_venta, cod_detalle))

        # 6. (Opcional) Actualizar el stock general del producto
        cursor.execute("UPDATE producto SET stock = stock + ? WHERE cod_producto = ?", (cantidad, cod_producto))

        conn.commit()
        cursor.close()
        conn.close()

        return 'si'



@bp.route('/eliminarProductoCajaCompra', methods=['POST', 'GET'])
def eliminarProductoCajaCompra():
    if request.method == "POST":
        medicamento = request.form['num']
        venta = request.form['venta']

        print(venta)
        print(medicamento)

        conn = conectar()
        cursor = conn.cursor()
        query = "select cantidad,cod_producto,codLote from detalle_compra where cod_compra = ? and cod_detalleCompra = ? "
        cursor.execute(query,(venta,medicamento))
        cantidad = cursor.fetchone()

        print(cantidad)

        conn = conectar()
        cursor = conn.cursor()
        query = "delete detalle_compra where cod_compra = ? AND cod_detalleCompra = ? "
        cursor.execute(query,(venta,medicamento))
        conn.commit()
        cursor.close()
        conn.close()

        conn = conectar()
        cursor = conn.cursor()
        query = "delete lotes where cod_lote = ? "
        cursor.execute(query,(cantidad[2]))
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
    cantidad = 0
    cod_producto = 0
    precio = 0
    descuento_raw = 0 

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

                            SUM(
                                CASE 
                                    WHEN dv.cantidad = 0 THEN 
                                        CASE 
                                            WHEN dv.precio_venta < 1 THEN -(p.precio * dv.precio_venta)  -- Descuento porcentual sobre precio base
                                            ELSE -dv.precio_venta  -- Descuento fijo
                                        END
                                    ELSE 
                                        CASE 
                                            WHEN dv.precio_venta < 1 THEN dv.cantidad * (p.precio * (1 - dv.precio_venta))  -- Descuento porcentual
                                            ELSE dv.cantidad * (p.precio - dv.precio_venta)  -- Descuento fijo
                                        END
                                END
                            ) AS total_venta

                        FROM 
                            venta AS v 
                        INNER JOIN 
                            cliente AS vendedor ON vendedor.num_cliente = v.vendedor 
                        INNER JOIN 
                            detalle_carrito AS dv ON dv.cod_carrito = v.id_carrito
                        INNER JOIN 
                            producto AS p ON dv.cod_producto = p.cod_producto
                        WHERE 
                            v.cod_venta = ?
                        GROUP BY 
                            v.cod_venta, 
                            v.fecha_venta, 
                            vendedor.nombres_cliente, 
                            vendedor.apellidos_cliente;


                    
        """


        cursor.execute(query, (num))
        ticket = cursor.fetchone()

    conn = conectar()
    cursor = conn.cursor()
    query = "select p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento,p.cod_producto from detalle_carrito as dv inner join producto as p on dv.cod_producto = p.cod_producto INNER JOIN venta AS v on dv.cod_carrito = v.id_carrito where v.cod_venta = ?"
    cursor.execute(query,(num))
    detalle = cursor.fetchall()


    if not detalle:
        conn = conectar()
        cursor = conn.cursor()
        query = "select p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento,p.cod_producto from Det_venta as dv inner join producto as p on dv.cod_producto_1 = p.cod_producto INNER JOIN venta AS v on dv.cod_venta_1 = v.cod_venta where v.cod_venta = ?"
        cursor.execute(query,(num))
        detalle = cursor.fetchall()


    print(detalle)

    print('aaaaaaaaaaaaaaaaaa')
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
    pdf.set_font('Arial', 'B', 30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.multi_cell(0, 5, 'RUC 1524135412', 0, "C")
    pdf.ln(1)

    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, 'Monumento la reforma, 10vrs al sur, 10vrs al oeste, contiguo a la bahia de buses Mercadoo San Carlos Masaya, Nicaragua', 0, "C")
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

    # Iterar sobre los resultados y calcular el descuento
    for fila in detalle:
        nom_producto = str(fila[0]).upper()  # Nombre del producto en mayúsculas
        cantidad = float(fila[1])  # Cantidad comprada
        precio = float(fila[2])  # Precio unitario
        descuento_raw = float(fila[5])  # Descuento aplicado
        cod_producto = fila[6]

        # Actualizar stock
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('UPDATE producto SET stock = stock - ? WHERE cod_producto = ?', (cantidad, cod_producto))
        conn.commit()
        cursor.close()
        conn.close()

        # Calcular subtotal y descuento
        subtotal = cantidad * precio if cantidad else precio

        if descuento_raw == 0.0:
            descuento_aplicado = 0
        elif descuento_raw < 1:
            descuento_aplicado = subtotal * descuento_raw  # Descuento en %
        else:
            descuento_aplicado = descuento_raw  # Descuento directo

        total = subtotal - descuento_aplicado

    pdf.set_line_width(0.0)
    pdf.set_font('Arial', '', 7.5)

    # Coordenadas actuales
    pdf.set_line_width(0.2) 
    pdf.set_font('Arial', 'B', 7.5)

    # Encabezados de la tabla
    pdf.cell(30, 10, 'Producto', 1)
    pdf.cell(15, 10, 'Cantidad', 1)
    pdf.cell(15, 10, 'Descuento', 1)
    pdf.cell(30, 10, 'Subtotal', 1)
    pdf.ln(10)  # Salto de línea

    for fila in detalle:
        nom_producto = str(fila[0]).upper()
        cantidad = float(fila[1])
        precio = float(fila[2])
        descuento_raw = float(fila[5])
        cod_producto = fila[6]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('UPDATE producto SET stock = stock - ? WHERE cod_producto = ?', (cantidad, cod_producto))
        conn.commit()
        cursor.close()
        conn.close()

        subtotal = cantidad * precio if cantidad else precio

        if descuento_raw == 0.0:
            descuento_aplicado = 0
        elif descuento_raw < 1:
            descuento_aplicado = subtotal * descuento_raw
        else:
            descuento_aplicado = descuento_raw

        total = subtotal - descuento_aplicado

        pdf.set_line_width(0.0)
        pdf.set_font('Arial', '', 7.5)

        x = pdf.get_x()
        y = pdf.get_y()

        pdf.multi_cell(30, 4, nom_producto, border=1)
        altura_fila = pdf.get_y() - y

        pdf.set_xy(x + 30, y)
        pdf.cell(15, altura_fila, str(cantidad), 1, 0, 'C')

        if cantidad:
            if descuento_aplicado == 0:
                descuento_str = ""
            else:
                descuento_str = f"C$ {descuento_aplicado:.2f}"
        else:
            if descuento_aplicado == 0:
                descuento_str = ""
            elif descuento_raw < 1:
                descuento_str = f"{descuento_raw * 100:.0f} %"
            else:
                descuento_str = f"C$ {descuento_raw:.2f}"

        pdf.cell(15, altura_fila, descuento_str, 1, 0, 'C')
        pdf.cell(30, altura_fila, f"C$ {total:.2f}", 1, 0, 'C')
        pdf.ln(altura_fila)



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


@bp.route('/facturarCompra', methods=['POST', 'GET'])
def facturarCompra():
    num = request.args.get('id')

    conn = conectar()
    cursor = conn.cursor()

    # Consulta SQL para obtener los datos del ticket
    query = """
    	select v.cod_compra,v.fechaCompra,c.nom_proveedor as cliente,SUM(dv.cantidad * p.precio - dv.precio_venta) AS total_venta  
        from compras as v inner join proveedor as c on v.cod_proveedor = c.cod_proveedor 
            INNER JOIN 
                            detalle_compra AS dv ON v.cod_compra = dv.cod_compra
                        INNER JOIN 
                            producto AS p ON dv.cod_producto = p.cod_producto
                        where v.cod_compra = ?
                        GROUP BY 
                            v.cod_compra, 
                            v.fechaCompra, 
                            c.nom_proveedor
    """

    cursor.execute(query, (num))
    ticket = cursor.fetchone()
    no_tiene = 1
    

    conn = conectar()
    cursor = conn.cursor()
    query = "select p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento,p.cod_producto from detalle_compra as dv inner join producto as p on dv.cod_producto = p.cod_producto INNER JOIN compras AS v on dv.cod_compra = v.cod_compra where v.cod_compra = ?"
    cursor.execute(query,(num))
    detalle = cursor.fetchall()

    print(detalle)

    print('aaaaaaaaaaaaaaaaaa')
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
    pdf.set_font('Arial', 'B', 30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.multi_cell(0, 5, 'RUC 1524135412', 0, "C")
    pdf.ln(1)

    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, 'Monumento la reforma, 10vrs al sur, 10vrs al oeste, contiguo a la bahia de buses Mercadoo San Carlos Masaya, Nicaragua', 0, "C")
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
        pdf.cell(25, 10, 'Proveedor: ')
        pdf.set_font('Arial', 'B', 7.5)
        pdf.cell(20, 10, ticket[2])
        pdf.ln(6)
    
        
    pdf.ln(5)

    pdf.set_line_width(0.2) 
    pdf.set_font('Arial', 'B', 7.5)

    # Encabezados de la tabla

    # Iterar sobre los resultados y calcular el descuento
    for fila in detalle:
        nom_producto = str(fila[0]).upper()  # Nombre del producto en mayúsculas
        cantidad = float(fila[1])  # Cantidad comprada
        precio = float(fila[2])  # Precio unitario
        descuento_raw = float(fila[5])  # Descuento aplicado
        cod_producto = fila[6]

    # Actualizar stock
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('UPDATE producto SET stock = stock + ? WHERE cod_producto = ?', (cantidad, cod_producto))
    conn.commit()
    cursor.close()
    conn.close()

    # Calcular subtotal y descuento
    subtotal = cantidad * precio if cantidad else precio

    if descuento_raw == 0.0:
        descuento_aplicado = 0
    elif descuento_raw < 1:
        descuento_aplicado = subtotal * descuento_raw  # Descuento en %
    else:
        descuento_aplicado = descuento_raw  # Descuento directo

    total = subtotal - descuento_aplicado

    pdf.set_line_width(0.0)
    pdf.set_font('Arial', '', 7.5)

    # Coordenadas actuales
    pdf.set_line_width(0.2) 
    pdf.set_font('Arial', 'B', 7.5)

    # Encabezados de la tabla
    pdf.cell(30, 10, 'Producto', 1)
    pdf.cell(15, 10, 'Cantidad', 1)
    pdf.cell(15, 10, 'Descuento', 1)
    pdf.cell(30, 10, 'Subtotal', 1)
    pdf.ln(10)  # Salto de línea

    for fila in detalle:
        nom_producto = str(fila[0]).upper()
        cantidad = float(fila[1])
        precio = float(fila[2])
        descuento_raw = float(fila[5])
        cod_producto = fila[6]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('UPDATE producto SET stock = stock + ? WHERE cod_producto = ?', (cantidad, cod_producto))
        conn.commit()
        cursor.close()
        conn.close()

        subtotal = cantidad * precio if cantidad else precio

        if descuento_raw == 0.0:
            descuento_aplicado = 0
        elif descuento_raw < 1:
            descuento_aplicado = subtotal * descuento_raw
        else:
            descuento_aplicado = descuento_raw

        total = subtotal - descuento_aplicado

        pdf.set_line_width(0.0)
        pdf.set_font('Arial', '', 7.5)

        x = pdf.get_x()
        y = pdf.get_y()

        pdf.multi_cell(30, 4, nom_producto, border=1)
        altura_fila = pdf.get_y() - y

        pdf.set_xy(x + 30, y)
        pdf.cell(15, altura_fila, str(cantidad), 1, 0, 'C')

        if cantidad:
            if descuento_aplicado == 0:
                descuento_str = ""
            else:
                descuento_str = f"C$ {descuento_aplicado:.2f}"
        else:
            if descuento_aplicado == 0:
                descuento_str = ""
            elif descuento_raw < 1:
                descuento_str = f"{descuento_raw * 100:.0f} %"
            else:
                descuento_str = f"C$ {descuento_raw:.2f}"

        pdf.cell(15, altura_fila, descuento_str, 1, 0, 'C')
        pdf.cell(30, altura_fila, f"C$ {total:.2f}", 1, 0, 'C')
        pdf.ln(altura_fila)



    if no_tiene ==1:
        pdf.set_font('Arial', 'B', 7.5)  # Título "Total"
        pdf.cell(25, 30, 'Total: ')
        pdf.set_font('Arial', '', 30)  # Aumentar el tamaño de la fuente para el valor
        pdf.cell(65, 30, 'C$ '+str(ticket[3]), 0, 1, 'R')  # Alinear a la derecha
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
            UPDATE compras
            SET cod_estado = 7
            WHERE cod_compra = ?
    '''
                    
                    # Ejecutar la consulta SQL
    cursor.execute(query, (num))
    conn.commit()

                    # Cerrar la conexión
    cursor.close()
    conn.close()

    

    return response


@bp.route('/facturarOrden', methods=['POST', 'GET'])
def facturarOrden():
    num = request.args.get('id')

    conn = conectar()
    cursor = conn.cursor()

    # Consulta SQL para obtener los datos del ticket
    query = """
    	select v.cod_venta,v.fecha_venta,c.nombres_cliente + ' ' + c.apellidos_cliente as cliente, vendedor.nombres_cliente + ' ' +vendedor.apellidos_cliente as vendedor,SUM(dv.cantidad * p.precio - dv.precio_venta) AS total_venta  from venta as v inner join cliente as c on v.num_cliente = c.num_cliente  INNER JOIN cliente as vendedor on vendedor.num_cliente = v.vendedor
    INNER JOIN 
                    detalle_carrito AS dv ON v.id_carrito = dv.cod_carrito
                INNER JOIN 
                    producto AS p ON dv.cod_producto = p.cod_producto
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

                SUM(
                    CASE 
                        WHEN dv.cantidad = 0 THEN 
                            CASE 
                                WHEN dv.precio_venta < 1 THEN -(p.precio * dv.precio_venta)  -- Descuento porcentual sobre precio base
                                ELSE -dv.precio_venta  -- Descuento fijo
                            END
                        ELSE 
                            CASE 
                                WHEN dv.precio_venta < 1 THEN dv.cantidad * (p.precio * (1 - dv.precio_venta))  -- Descuento porcentual
                                ELSE dv.cantidad * (p.precio - dv.precio_venta)  -- Descuento fijo
                            END
                    END
                ) AS total_venta

            FROM 
                venta AS v 
            INNER JOIN 
                cliente AS vendedor ON vendedor.num_cliente = v.vendedor 
            INNER JOIN 
                detalle_carrito AS dv ON dv.cod_carrito = v.id_carrito
            INNER JOIN 
                producto AS p ON dv.cod_producto = p.cod_producto
            WHERE 
                v.cod_venta = ?
            GROUP BY 
                v.cod_venta, 
                v.fecha_venta, 
                vendedor.nombres_cliente, 
                vendedor.apellidos_cliente;


        
        """


        cursor.execute(query, (num))
        ticket = cursor.fetchone()

    conn = conectar()
    cursor = conn.cursor()
    query = "select p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento,p.cod_producto from detalle_carrito as dv inner join producto as p on dv.cod_producto = p.cod_producto INNER JOIN venta AS v on dv.cod_carrito = v.id_carrito where v.cod_venta = ?"
    cursor.execute(query,(num))
    detalle = cursor.fetchall()

    print(detalle)

    print('aaaaaaaaaaaaaaaaaa')
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
    pdf.set_font('Arial', 'B', 30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.multi_cell(0, 5, 'RUC 1524135412', 0, "C")
    pdf.ln(1)

    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, 'Monumento la reforma, 10vrs al sur, 10vrs al oeste, contiguo a la bahia de buses Mercadoo San Carlos Masaya, Nicaragua', 0, "C")
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
    # Encabezado de la tabla
    pdf.set_font('Arial', 'B', 7.5)
    pdf.set_line_width(0.2)
    pdf.cell(30, 10, 'Producto', 1)
    pdf.cell(15, 10, 'Cantidad', 1)
    pdf.cell(15, 10, 'Descuento', 1)
    pdf.cell(30, 10, 'Subtotal', 1)
    pdf.ln(10)

    # Fuente normal para el contenido
    pdf.set_font('Arial', '', 7.5)
    pdf.set_line_width(0.0)

    # Iterar sobre los productos en el detalle
    for fila in detalle:
        nom_producto = str(fila[0]).upper()
        cantidad = float(fila[1])
        precio = float(fila[2])
        descuento_raw = float(fila[5])
        cod_producto = fila[6]

        # Actualizar stock en base de datos
        conn = conectar()
        cursor = conn.cursor()
        query = '''
            UPDATE producto
            SET stock = stock - ?
            WHERE cod_producto = ?
        '''
        cursor.execute(query, (cantidad, cod_producto))
        conn.commit()
        cursor.close()
        conn.close()

        # Calcular subtotal y descuento
        subtotal = cantidad * precio if cantidad else precio
        if descuento_raw == 0.0:
            descuento_aplicado = 0
        elif descuento_raw < 1:
            descuento_aplicado = subtotal * descuento_raw
        else:
            descuento_aplicado = descuento_raw

        total = subtotal - descuento_aplicado

        # Imprimir los datos en el PDF
        x = pdf.get_x()
        y = pdf.get_y()

        # Nombre del producto (puede cambiar por multi_cell si es muy largo)
        pdf.multi_cell(30, 4, nom_producto, border=1)
        altura_fila = pdf.get_y() - y
        pdf.set_xy(x + 30, y)

        # Cantidad
        pdf.cell(15, altura_fila, str(cantidad), 1, 0, 'C')

        # Descuento
        if cantidad:
            if descuento_aplicado == 0:
                descuento_str = ""
            else:
                descuento_str = f"C$ {descuento_aplicado:.2f}"
        else:
            if descuento_aplicado == 0:
                descuento_str = ""
            elif descuento_raw < 1:
                descuento_str = f"{descuento_raw * 100:.0f} %"
            else:
                descuento_str = f"C$ {descuento_raw:.2f}"

        pdf.cell(15, altura_fila, descuento_str, 1, 0, 'C')

        # Subtotal
        pdf.cell(30, altura_fila, f"C$ {total:.2f}", 1, 0, 'C')

        # Salto de línea a la altura de la celda más alta
        pdf.ln(altura_fila)

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
        cantidad = int(request.form['cantidad'])
        descuento = request.form['descuento']

        # Verificar si el medicamento ya está en el detalle de la venta
        conn = conectar()
        cursor = conn.cursor()
        query = """
            SELECT * FROM Det_venta 
            WHERE cod_venta_1 = ? AND cod_producto_1 = ? AND precio_venta = ?
        """
        cursor.execute(query, (venta, medicamento, descuento))
        existe = cursor.fetchone()

        # Verificar si hay suficientes lotes
        cantidad_faltante = cantidad
        lotes_usados = []

        query = """
            SELECT cod_lote, cantidad
            FROM lotes
            WHERE idProducto = ?
            AND cantidad > 0
            ORDER BY FechaVencimiento ASC
        """
        cursor.execute(query, (medicamento,))
        lotes = cursor.fetchall()

        for lote in lotes:
            cod_lote, disponible = lote
            if cantidad_faltante <= 0:
                break
            if disponible >= cantidad_faltante:
                lotes_usados.append((cantidad_faltante, cod_lote))
                cantidad_faltante = 0
            else:
                lotes_usados.append((disponible, cod_lote))
                cantidad_faltante -= disponible

        if cantidad_faltante > 0:
            cursor.close()
            conn.close()
            return 'No hay suficiente stock en los lotes disponibles.', 400

        # Insertar o actualizar el detalle de venta
        if existe:
            cod_detalle = existe[0]
            query = 'UPDATE Det_venta SET cantidad = cantidad + ? WHERE cod_detalle = ?'
            cursor.execute(query, (cantidad, cod_detalle))
        else:
            query = '''
                INSERT INTO Det_venta (cod_producto_1, cod_venta_1, cantidad, precio_venta)
                VALUES (?, ?, ?, ?)
            '''
            cursor.execute(query, (medicamento, venta, cantidad, descuento))
            conn.commit()
            cursor.close()
            conn.close()

            conn = conectar()
            cursor = conn.cursor()
            query = """
                SELECT * FROM Det_venta 
                WHERE cod_venta_1 = ? AND cod_producto_1 = ? AND precio_venta = ? order by cod_venta_1 desc
            """
            cursor.execute(query, (venta, medicamento, descuento))
            cod_detalle1 = cursor.fetchone()
            cod_detalle = cod_detalle1[0]

        # Registrar cada lote usado y descontar su cantidad
        for cant_usada, cod_lote in lotes_usados:
            # Descontar del lote
            cursor.execute(
                "UPDATE lotes SET cantidad = cantidad - ? WHERE cod_lote = ?",
                (cant_usada, cod_lote)
            )
            # Insertar detalle del lote usado
            cursor.execute(
                "INSERT INTO detalle_venta_lote (codDetalle, cantidadUsada, codLote) VALUES (?, ?, ?)",
                (cod_detalle, cant_usada, cod_lote)
            )

        conn.commit()
        cursor.close()
        conn.close()


        conn = conectar()
        cursor = conn.cursor()
        query = 'update producto set stock = stock-? where cod_producto = ?'
        cursor.execute(query, (cantidad,medicamento))
        conn.commit()
        cursor.close()
        conn.close()

        return 'hecho'



@bp.route('/ingresarMedicamentoCompra', methods=['POST'])
def ingresarMedicamentoCompra():
    if request.method == "POST":
        venta = request.form['venta']
        medicamento = request.form['medicamento']
        cantidad = request.form['cantidad']
        descuento = request.form['descuento']

        lote = request.form['lote']
        vencimiento = request.form['fvencimiento']

        print('aquiii')
        print(descuento)
        print(venta)
        print(medicamento)
        print(cantidad)

        # BUSCAMOS EL MEDICAMENTO ESTA EN LA FACTURA

        conn = conectar()
        cursor = conn.cursor()
        query = "select dc.cod_detalleCompra,l.cod_lote from detalle_compra as dc inner join lotes as l on dc.codLote = l.cod_lote where dc.cod_compra = ? and dc.cod_producto = ? and dc.precio_venta = ? and l.lote = ?"
        cursor.execute(query,(venta,medicamento,descuento,lote))
        existe = cursor.fetchone()

        print(existe)

        if existe:

            conn = conectar()
            cursor = conn.cursor()
            query = 'UPDATE detalle_compra set cantidad += ? where cod_detalleCompra = ?'
            cursor.execute(query, (cantidad,existe[0]))
            conn.commit()
            cursor.close()
            conn.close()

            conn = conectar()
            cursor = conn.cursor()
            query = 'UPDATE lotes set cantidad += ? where cod_lote = ?'
            cursor.execute(query, (cantidad,existe[1]))
            conn.commit()
            cursor.close()
            conn.close()
        else:

            conn = conectar()
            cursor = conn.cursor()
            query = 'INSERT INTO lotes (lote,FechaVencimiento,idProducto,cantidad) VALUES (?,?,?,?)'
            cursor.execute(query, (lote,vencimiento,medicamento,cantidad))
            conn.commit()
            cursor.close()
            conn.close()


            conn = conectar()
            cursor = conn.cursor()
            query = "select cod_lote from lotes order by cod_lote desc"
            cursor.execute(query)
            loteI = cursor.fetchone()

            print(loteI)



            conn = conectar()
            cursor = conn.cursor()
            query = 'INSERT INTO detalle_compra (cod_producto,cod_compra,cantidad,precio_venta,codLote) VALUES (?,?,?,?,?)'
            cursor.execute(query, (medicamento,venta,cantidad,descuento,loteI[0]))
            conn.commit()
            cursor.close()
            conn.close()
        

        print('cantidad: ', cantidad)
        conn = conectar()
        cursor = conn.cursor()
        query = 'update producto set stock = stock + ? where cod_producto = ?'
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
    query = """
            SELECT SUM(
            CASE
                WHEN dv.cantidad = 0 THEN
                    CASE
                        WHEN dv.precio_venta < 1 THEN -(p.precio * dv.precio_venta) -- porcentaje descuento en devolución
                        ELSE -dv.precio_venta -- descuento fijo en devolución
                    END
                ELSE -- cantidad > 0
                    CASE
                        WHEN dv.precio_venta < 1 THEN dv.cantidad * (p.precio * (1 - dv.precio_venta)) -- porcentaje descuento
                        ELSE dv.cantidad * (p.precio - dv.precio_venta) -- descuento fijo
                    END
            END
        ) AS total_venta
        FROM Det_venta AS dv
        INNER JOIN producto AS p ON dv.cod_producto_1 = p.cod_producto
        WHERE dv.cod_venta_1 = ?;

    """
    cursor.execute(query,(num))
    total = cursor.fetchone()
    print(total)
    if total[0]:
        return str(total[0])
    else:
        return '0'

@bp.route('/totalCajaCompra', methods=['POST'])
def totalCajaCompra():

    num = request.form['num']

    print(num)
    conn = conectar()
    cursor = conn.cursor()
    query = """
            SELECT SUM(
            CASE
                WHEN dv.cantidad = 0 THEN
                    CASE
                        WHEN dv.precio_venta < 1 THEN -(p.precio * dv.precio_venta) -- porcentaje descuento en devolución
                        ELSE -dv.precio_venta -- descuento fijo en devolución
                    END
                ELSE -- cantidad > 0
                    CASE
                        WHEN dv.precio_venta < 1 THEN dv.cantidad * (p.precio * (1 - dv.precio_venta)) -- porcentaje descuento
                        ELSE dv.cantidad * (p.precio - dv.precio_venta) -- descuento fijo
                    END
            END
        ) AS total_venta
        FROM detalle_compra AS dv
        INNER JOIN producto AS p ON dv.cod_producto = p.cod_producto
        WHERE dv.cod_compra = ?;

    """
    cursor.execute(query,(num))
    total = cursor.fetchone()
    print(total)
    if total[0]:
        return str(total[0])
    else:
        return '0'

@bp.route('/totalOrden', methods=['POST'])
def totalOrden():

    num = request.form['num']

    print(num)
    conn = conectar()
    cursor = conn.cursor()
    query = """
            SELECT SUM(
            CASE
                WHEN dv.cantidad = 0 THEN
                    CASE
                        WHEN dv.precio_venta < 1 THEN -(p.precio * dv.precio_venta) -- porcentaje descuento en devolución
                        ELSE -dv.precio_venta -- descuento fijo en devolución
                    END
                ELSE -- cantidad > 0
                    CASE
                        WHEN dv.precio_venta < 1 THEN dv.cantidad * (p.precio * (1 - dv.precio_venta)) -- porcentaje descuento
                        ELSE dv.cantidad * (p.precio - dv.precio_venta) -- descuento fijo
                    END
            END
        ) AS total_venta
        FROM detalle_carrito AS dv
        INNER JOIN producto AS p ON dv.cod_producto = p.cod_producto
        INNER JOIN venta AS v on dv.cod_carrito = v.id_carrito
        WHERE v.cod_venta = ?;

    """
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


@bp.route('/listadoProductosCajaCompra', methods=['POST'])
def listadoProductosCajaCompra():

    num = request.form['num']
    print(num)


    conn = conectar()
    cursor = conn.cursor()
    query = "select dv.cod_detalleCompra,p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento from detalle_compra as dv inner join producto as p on dv.cod_producto = p.cod_producto where dv.cod_compra = ?"
    cursor.execute(query,(num))
    medicamentos = cursor.fetchall()
    

    return render_template('sistema/tablas/tabla-caja-compra.html',medicamentos = medicamentos)

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

@bp.route('/agregarOrden', methods=['POST'])
def agregarOrden():
    nohay = []
    hay = []

    num = request.form['num']
    cod_atencion = request.form['receta']

    print(num)
    print(cod_atencion)

    conn = conectar()
    cursor = conn.cursor()

    # Obtener productos de la receta
    query = """select p.cod_producto,dv.cantidad,p.nom_producto,p.stock from venta as v 
                inner join detalle_carrito as dv on v.id_carrito = dv.cod_carrito inner join producto as p on dv.cod_producto = p.cod_producto 
                where v.cod_venta = ?"""
    cursor.execute(query, (cod_atencion,))
    receta_productos = cursor.fetchall()

    for cod_producto, cantidad, nom_producto, stock in receta_productos:
        if stock is not None and stock >= cantidad:
            hay.append((cod_producto, cantidad))  # Guardamos solo los productos con stock suficiente
        else:
            nohay.append(nom_producto)

  
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
                      p.stock, p.stock_critico,dv.precio_venta as descuento
               FROM detalle_carrito AS dv 
               INNER JOIN producto AS p ON dv.cod_producto = p.cod_producto 
               INNER JOIN 
	            venta AS v on dv.cod_carrito = v.id_carrito
               WHERE v.cod_venta = ? 
               AND dv.cod_producto IN ({})""".format(placeholders)
    
    # Extraer solo los códigos de producto de los que se insertaron
    params = [cod_atencion] + [prod[0] for prod in hay]  

    print(query)
    print(params)
    cursor.execute(query, params)
    medicamentos = cursor.fetchall()

    cursor.close()
    conn.close()

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

@bp.route('/validarFacturaCompra', methods=['POST'])
def validarFacturaCompra():
    if request.method == "POST":
        num = request.form['num']
    
        conn = conectar()
        cursor = conn.cursor()
        query = "select *  from compras where cod_compra = ? and cod_estado = 8"
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

@bp.route('/validarProductosCompra', methods=['POST'])
def validarProductosCompra():
    if request.method == "POST":
        num = request.form['num']
    
        conn = conectar()
        cursor = conn.cursor()
        query = "select dv.cod_detalleCompra,p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento from detalle_compra as dv inner join producto as p on dv.cod_producto = p.cod_producto where dv.cod_compra = ?"
        cursor.execute(query,(num))
        tiene = cursor.fetchone()
        
        if tiene:
            return 'si'
        else:
            return 'no'

@bp.route('/validarProductosOrden', methods=['POST'])
def validarProductosOrden():
    if request.method == "POST":
        num = request.form['num']
    
        conn = conectar()
        cursor = conn.cursor()
        query = "select dv.cod_detalle,p.nom_producto,dv.cantidad,p.precio,p.stock,p.stock_critico,dv.precio_venta as descuento from detalle_carrito as dv inner join producto as p on dv.cod_producto = p.cod_producto INNER JOIN venta AS v on dv.cod_carrito = v.id_carrito where v.cod_venta = ?"
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
        query = "SELECT v.cod_compra,vendedor.nom_proveedor, CONVERT(DATE, v.fechaCompra) AS fecha,FORMAT(v.fechaCompra, 'HH:mm') AS hora, SUM(dv.cantidad * p.precio - dv.precio_venta) AS total_venta, e.NombreEstado AS estado FROM compras AS v INNER JOIN proveedor AS vendedor ON vendedor.cod_proveedor = v.cod_proveedor INNER JOIN detalle_compra AS dv ON v.cod_compra = dv.cod_compra INNER JOIN producto AS p ON dv.cod_producto = p.cod_producto INNER JOIN estado AS e ON v.cod_estado = e.id_estado GROUP BY v.cod_compra, CONVERT(DATE, v.fechaCompra), FORMAT(v.fechaCompra, 'HH:mm'), vendedor.nom_proveedor, e.NombreEstado order by v.cod_compra desc;"
        cursor.execute(query)
        ventas = cursor.fetchall()

        return render_template('sistema/tablas/tabla_compra.html', ventas=ventas)
        
    else:
        return "No"


@bp.route('/tablaVentas', methods=['POST'])
def tablaVentas():

    if request.method == "POST":

        conn = conectar()
        cursor = conn.cursor()
        query = "SELECT v.cod_venta, CONVERT(DATE, v.fecha_venta) AS fecha,FORMAT(v.fecha_venta, 'HH:mm') AS hora, cred.usuario AS vendedor, SUM(dv.cantidad * p.precio - dv.precio_venta) AS total_venta, e.NombreEstado AS estado FROM venta AS v INNER JOIN cliente AS vendedor ON vendedor.num_cliente = v.vendedor INNER JOIN Det_venta AS dv ON v.cod_venta = dv.cod_venta_1 INNER JOIN producto AS p ON dv.cod_producto_1 = p.cod_producto INNER JOIN estado AS e ON v.cod_estado = e.id_estado INNER JOIN credenciales as cred on vendedor.id_credencial = cred.id_credencial GROUP BY v.cod_venta, CONVERT(DATE, v.fecha_venta), FORMAT(v.fecha_venta, 'HH:mm'), vendedor.nombres_cliente, vendedor.apellidos_cliente, e.NombreEstado, cred.usuario order by v.cod_venta desc;"
        cursor.execute(query)
        ventas = cursor.fetchall()

        return render_template('sistema/tablas/tabla_ventas.html', ventas=ventas)
        
    else:
        return "No"

#  FIN CARGA DE LA TABLA

# TRAER CLIENTE DE LA ORDEN DE COMPRA

# INICIO DE LA CARGA DE LA TABLA


# FIN CLIENTE ORDEN DE COMPRA

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

        if general:


            return render_template('sistema/modales/modal_detalle_factura.html', detalle=detalle, general = general)
        else:
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


@bp.route('/traerCitasSistema')
def traerCitasSistema():
    print('ENTRO')
    if session['rol'] != 'ADMINISTRADOR':
        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_atencion,c.nombres_cliente,a.fecha_atencion,e.NombreEstado from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente INNER JOIN estado as e on a.id_estado = e.id_estado where e.NombreEstado = 'AGENDADO'"
        cursor.execute(query)
        agendas = cursor.fetchall()
    else:
        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_atencion,c.nombres_cliente,a.fecha_atencion,e.NombreEstado from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente INNER JOIN estado as e on a.id_estado = e.id_estado where e.NombreEstado = 'AGENDADO'"
        cursor.execute(query)
        agendas = cursor.fetchall()
    agenda= []
    print(agendas)
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
    print(agenda)
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

    conn = conectar()
    cursor = conn.cursor()
    query = "select * from especie "
    cursor.execute(query)
    especies = cursor.fetchall()

    

    return render_template('sistema/modales/programar_cita.html', fecha = fecha,clientes = clientes,atencion = atencion,especies = especies)


@bp.route('/modalAgendarValoracion', methods=['POST'])
@login_required
def modalAgendarValoracion():
    fecha = request.form['fecha']
    id = request.form['id']


    conn = conectar()
    cursor = conn.cursor()
    query = "select c.num_cliente,c.nombres_cliente + ' ' + apellidos_cliente as Nombre from hospitalizacion as h inner join mascota as m on h.idMascota = m.idMascota INNER JOIN cliente as c on m.num_cliente = c.num_cliente where h.id_hosp = ? "
    cursor.execute(query,(id))
    clientes = cursor.fetchall()

    conn = conectar()
    cursor = conn.cursor()
    query = "select m.idMascota,m.Nombre_mascota from hospitalizacion as h inner join mascota as m on h.idMascota = m.idMascota INNER JOIN cliente as c on m.num_cliente = c.num_cliente where h.id_hosp = ? "
    cursor.execute(query,(id))
    mascota = cursor.fetchall()

 
    conn = conectar()
    cursor = conn.cursor()
    query = "select cod_tipo,tipo from tipo_atencion "
    cursor.execute(query)
    atencion = cursor.fetchall()

    conn = conectar()
    cursor = conn.cursor()
    query = "select * from especie "
    cursor.execute(query)
    especies = cursor.fetchall()

    

    return render_template('sistema/modales/programar_cita_valoracion.html',mascotas = mascota, fecha = fecha,clientes = clientes,atencion = atencion,especies = especies)






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
    print(especie)
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
    print(mascotas_list)

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

    print(atencion)

    fecha_hora_str = f"{fecha} {hora}"
    fecha_hora = datetime.strptime(fecha_hora_str, "%Y-%m-%d %I:%M %p")

    # Separar el día y el mes
    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    dia = fecha_obj.strftime("%d")  # Día con ceros a la izquierda
    locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8')  # Español de México
    mes = fecha_obj.strftime("%B").capitalize()

   

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

    print(mascota[0])

    conn = conectar()
    cursor = conn.cursor()
            # Realiza la inserción
    query = 'INSERT INTO cliente_mascota (cod_mascota,cod_cliente) VALUES (?,?)'
    cursor.execute(query, (mascota[0],cliente ))
    conn.commit()
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
        query = "select a.cod_atencion,a.fecha_atencion,c.nombres_cliente + ' ' + c.apellidos_cliente as Nombre,e.NombreEstado,m.Nombre_mascota,es.nom_especie,ta.tipo,a.peso,a.altura,a.temperatura,vet.nombres_cliente as veterinario from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente inner join estado as e on a.id_estado = e.id_estado inner join mascota as m on a.idMascota = m.idMascota inner join tipo_atencion as ta on a.tipo_atencion = ta.cod_tipo inner join raza as r on m.id_raza = r.id_raza inner join especie as es on r.id_especie = es.id_especie inner join cliente as vet on a.num_veterinario = vet.num_cliente order by a.cod_atencion DESC"
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

        if session['rol'] == 'ADMINISTRADOR' or session['rol'] == 'DESARROLLADOR':
            conn = conectar()
            cursor = conn.cursor()
            query = "select a.cod_atencion,a.fecha_atencion,c.nombres_cliente + ' ' + c.apellidos_cliente as Nombre,e.NombreEstado,m.Nombre_mascota,es.nom_especie,ta.tipo,a.peso,a.altura,a.temperatura  from atencion as a inner join cliente as c on a.num_cliente = c.num_cliente inner join estado as e on a.id_estado = e.id_estado inner join mascota as m on a.idMascota = m.idMascota inner join tipo_atencion as ta on a.tipo_atencion = ta.cod_tipo inner join raza as r on m.id_raza = r.id_raza inner join especie as es on r.id_especie = es.id_especie inner join cliente as vet on a.num_veterinario = vet.num_cliente inner join credenciales as cred on cred.id_credencial = vet.id_credencial where a.id_estado = 10 AND CONVERT(DATE, a.fecha_atencion) = ? order by a.cod_atencion DESC"
            cursor.execute(query,(fechaActual.date()))
            consultas = cursor.fetchall()
        else:

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
        query = "select a.cod_detalle,p.nom_producto,p.precio,a.cantidad,a.orientacion from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ? order by cod_atencion DESC"
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

        peso = request.form['peso']
        altura = request.form['altura']
        temperatura = request.form['temperatura']


        conn = conectar()
        cursor = conn.cursor()
        query = 'UPDATE atencion set id_estado = 14, diagnostico = ?,peso = ?,altura = ?, temperatura = ? where cod_atencion = ?'
        cursor.execute(query, (diagnostico,peso,altura,temperatura,detalle))
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



@bp.route('/nuevoProveedor',methods = ['GET','POST'])
def nuevoProveedor():
    nombre = request.form['nombre']
    info = request.form['info']
    direccion = request.form['direccion']
    correo = request.form['correo']


    conn = conectar()
    cursor = conn.cursor()
    query = 'INSERT INTO proveedor (nom_proveedor,info_proveedor,dir_proveedor,correo_proveedor,id_estado) VALUES (?,?,?,?,1)'
    cursor.execute(query, (nombre,info,direccion,correo))
    conn.commit()
    cursor.close()
    conn.close()
    conn = conectar()
    cursor = conn.cursor()


    
    
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

        conn = conectar()
        cursor = conn.cursor()
        query = "select * from especie "
        cursor.execute(query)
        especies = cursor.fetchall()

        
        return render_template('sistema/modales/modal_agregar_hospitalizacion.html', habitaciones = cuarto,mascotas = mascotas,estados = estados,clientes = cliente, especies = especies)
        
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


@bp.route('/api/ventas')
def api_ventas():
    conn = conectar()
    cursor = conn.cursor()

    # Ejecutar SET LANGUAGE primero
    cursor.execute("SET LANGUAGE Spanish;")

    # Ahora ejecutar la consulta
    query = """
        SELECT 
            YEAR(v.fecha_venta) AS anio,
            MONTH(v.fecha_venta) AS mes_num,
            FORMAT(v.fecha_venta, 'MMMM') AS mes_nombre,
            SUM(dv.cantidad * dv.precio_venta) AS total_ventas
        FROM venta v
        INNER JOIN Det_venta dv ON v.cod_venta = dv.cod_venta_1
        GROUP BY YEAR(v.fecha_venta), MONTH(v.fecha_venta), FORMAT(v.fecha_venta, 'MMMM')
        ORDER BY anio, mes_num;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    # Construir respuesta
    ventas = []
    años = set()
    for r in rows:
        anio, mes_num, mes_nombre, total_ventas = r
        ventas.append({
            'anio': anio,
            'mes_num': mes_num,
            'mes_nombre': mes_nombre,
            'total_ventas': total_ventas
        })
        años.add(anio)

    return jsonify({
        'ventas': ventas,
        'años': sorted(list(años))
    })

@bp.route('/api/meta_anual')
def meta_anual():
    conn = conectar()
    cursor = conn.cursor()

   

    # Obtener año actual y año anterior
    cursor.execute("SELECT YEAR(GETDATE())")
    anio_actual = cursor.fetchone()[0]
    anio_anterior = anio_actual - 1

    print(anio_actual)
    print(anio_anterior)
    # Consulta para obtener la suma total ventas año actual
    query_actual = """
        SELECT SUM(dv.cantidad * dv.precio_venta)
        FROM venta v
        INNER JOIN Det_venta dv ON v.cod_venta = dv.cod_venta_1
        WHERE YEAR(v.fecha_venta) = ?
    """
    cursor.execute(query_actual, (anio_actual,))
    meta = cursor.fetchone()[0] or 0

    # Consulta para obtener suma total ventas año anterior
    cursor.execute(query_actual, (anio_anterior,))
    ventas_anterior = cursor.fetchone()[0] or 0

    # Calcular crecimiento porcentual (cuidado división por cero)
    if ventas_anterior == 0:
        crecimiento = 100 if meta > 0 else 0
    else:
        crecimiento = round(((meta - ventas_anterior) / ventas_anterior) * 100, 2)

    # Ejemplo breakup: % ventas primer semestre vs segundo semestre del año actual
    query_breakup = """
        SELECT 
            SUM(CASE WHEN MONTH(v.fecha_venta) BETWEEN 1 AND 6 THEN dv.cantidad * dv.precio_venta ELSE 0 END) AS primer_semestre,
            SUM(CASE WHEN MONTH(v.fecha_venta) BETWEEN 7 AND 12 THEN dv.cantidad * dv.precio_venta ELSE 0 END) AS segundo_semestre
        FROM venta v
        INNER JOIN Det_venta dv ON v.cod_venta = dv.cod_venta_1
        WHERE YEAR(v.fecha_venta) = ?
    """
    cursor.execute(query_breakup, (anio_actual,))
    primer_sem, segundo_sem = cursor.fetchone()
    total_sem = (primer_sem or 0) + (segundo_sem or 0)
    if total_sem == 0:
        breakup = [0, 0]
    else:
        breakup = [
            round((primer_sem or 0) / total_sem * 100, 2),
            round((segundo_sem or 0) / total_sem * 100, 2)
        ]

    cursor.close()
    conn.close()

    data = {
        "meta": round(meta, 2),
        "crecimiento": crecimiento,
        "anio_actual": anio_actual,
        "anio_anterior": anio_anterior,
        "breakup": breakup
    }

    return jsonify(data)

@bp.route('/api/monthly_earnings')
def monthly_earnings():
    conn = conectar()
    cursor = conn.cursor()

    # Obtener año actual para filtrar ventas de este año
    cursor.execute("SELECT YEAR(GETDATE())")
    anio_actual = cursor.fetchone()[0]

    # Consulta para obtener suma de ventas por mes del año actual
    query = """
        SELECT 
            MONTH(v.fecha_venta) AS mes_num,
            FORMAT(v.fecha_venta, 'MMMM') AS mes_nombre,
            SUM(dv.cantidad * dv.precio_venta) AS total_ventas
        FROM venta v
        INNER JOIN Det_venta dv ON v.cod_venta = dv.cod_venta_1
        WHERE YEAR(v.fecha_venta) = ?
        GROUP BY MONTH(v.fecha_venta), FORMAT(v.fecha_venta, 'MMMM')
        ORDER BY mes_num
    """
    cursor.execute(query, (anio_actual,))
    resultados = cursor.fetchall()

    # Construir respuesta en formato JSON
    data = []
    for row in resultados:
        mes_num, mes_nombre, total_ventas = row
        data.append({
            "mes_num": mes_num,
            "mes_nombre": mes_nombre.capitalize(),  # Primer letra mayúscula
            "total_ventas": round(total_ventas or 0, 2)
        })

    cursor.close()
    conn.close()

    return jsonify({
        "anio": anio_actual,
        "ventas_mensuales": data
    })



# WEBSOCKET
# SOCKET EMIT
@socketio.on('dato_nuevo')
def handle_nuevo_dato(data):
    print('entro')
    emit('actualizacion_tabla', data, broadcast=True)



# FIN WEBSOCKET
