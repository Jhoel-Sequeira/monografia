# controllers/sistema.py
import os
from flask import Blueprint, render_template, request,session
from functools import wraps
from conexion import conectar

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:  # Verifica si el usuario está en la sesión
            return render_template('sistema/error.html')  # Redirige a la página de error si no está autenticado
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


# FIN DE EDITAR     

# FIN DEL MODULO DE INVENTARIO

# INICIO DEL MODULO DE VENTAS
@bp.route('/ventas')
@login_required
def ventas():
    return render_template('sistema/ventas.html')


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