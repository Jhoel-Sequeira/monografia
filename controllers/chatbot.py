
import spacy
import requests
from datetime import date
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request,session,redirect,make_response,current_app
from controllers.correo import enviar_correo, enviar_correo_receta, enviar_correo_registro
from conexion import conectar
nlp = spacy.load('es_core_news_sm')


# Conectarse a la base de datos



# Función para realizar una consulta a la base de datos
def consultar_citas_pendientes(usuario):
    print(usuario)
    conn = conectar()
    cursor = conn.cursor()
    query = 'select fecha_atencion from atencion where id_estado = 10 and num_cliente = ?'
    cursor.execute(query, usuario)
    citas = cursor.fetchone()
    cursor.close()
    conn.close()


    if len(citas) == 0:
        return "No tienes citas pendientes."
    else:
        fecha_hora = citas[0]
        fecha, hora = fecha_hora.split(' ')

        retorno = f"Tiene una cita pendiente para la fecha: {fecha} a las {hora}."
        return retorno

# Función para realizar una consulta de acuerdo a una solicitud específica y el nombre de usuario
# EN LA PARTE DE CITAS
def procesar_consulta(solicitud, usuario):
    print(solicitud)
    if 'cita' in solicitud and 'pendiente' in solicitud:
        resultado = consultar_citas_pendientes(usuario)
        return resultado
    elif 'cita' in solicitud and ('pasado' in solicitud or 'anterior' in solicitud or 'ultimo' in solicitud):
        # Agrega tu lógica para consultar los usuarios en la base de datos
        conn = conectar()
        cursor = conn.cursor()
        query = 'select fecha_atencion from atencion where id_estado = 14 and num_cliente = ? order by fecha_atencion desc'
        cursor.execute(query, usuario)
        citas = cursor.fetchone()
        cursor.close()
        conn.close()
        if len(citas) == 0:
            return "No tiene registro de citas."
        print(citas[0])
        fecha_hora = citas[0]
        fecha = fecha_hora.strftime('%Y-%m-%d')  # Ejemplo: '2025-01-03'
        hora = fecha_hora.strftime('%H:%M:%S')   # Ejemplo: '13:00:00'

        retorno = f"Su ultima cita fue: {fecha} a las {hora}."
        return retorno
    else:
        return "No entiendo tu solicitud."
    
# FUNCION PARA LAS OPCIONES DE LAS RECETAS
def procesar_receta(solicitud, usuario,app):
    if 'receta' in solicitud and 'ultimo' in solicitud or ('enviame' in solicitud or 'mandar' in solicitud or 'mandame' in solicitud or 'enviser' in solicitud or 'enviemir' in solicitud):
        # Agrega tu lógica para consultar los usuarios en la base de datos
        #CONSULTA LIMITADA
        #receta = db1.execute("select dr.Medicamento,dr.Pasos,dr.Cantidad,dr.Diagnostico from Consulta as c inner join Usuarios as u ON c.IdUsuario = u.Id_Usuario inner join Recetas as r on c.Id_Consulta = r.IdConsulta inner join DetalleReceta as dr on r.Id_Receta = dr.IdReceta WHERE u.Id_Usuario = :correo ORDER BY c.Fecha DESC limit 1", correo = usuario)
        
        
        conn = conectar()
        cursor = conn.cursor()
        query = "select top 1 a.cod_atencion,c.correo_cliente  from atencion a inner join cliente as c on a.num_cliente = c.num_cliente where c.num_cliente = ? order by fecha_atencion desc"
        cursor.execute(query,(usuario))
        cod_atencion = cursor.fetchone()

        correo = cod_atencion[1]

        
        conn = conectar()
        cursor = conn.cursor()
        query = "select a.cod_detalle,p.nom_producto,p.precio,a.cantidad,a.orientacion from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ?"
        cursor.execute(query,(cod_atencion[0]))
        consultas = cursor.fetchall()


        conn = conectar()
        cursor = conn.cursor()
        query = "select diagnostico,cod_atencion from atencion where cod_atencion = ?"
        cursor.execute(query,(cod_atencion[0]))
        diagnostico = cursor.fetchall()

        print(diagnostico)

        if consultas:
            enviar_correo_receta(current_app,"Usted tiene una nueva receta",correo,'recetar',consultas,diagnostico)
            return "Receta Enviada.."
        else:
            return "Usted no tiene ninguna receta."

    elif 'receta' in solicitud and 'tener' in solicitud and ('producto' in solicitud or 'existe' in solicitud or 'existencia' in solicitud):
        # Agrega tu lógica para consultar los usuarios en la base de datos
        conn = conectar()
        cursor = conn.cursor()
        query = "select top 1 a.cod_atencion,c.correo_cliente  from atencion a inner join cliente as c on a.num_cliente = c.num_cliente where c.num_cliente = ? order by fecha_atencion desc"
        cursor.execute(query,(usuario))
        cod_atencion = cursor.fetchone()

        correo = cod_atencion[1]

        
        conn = conectar()
        cursor = conn.cursor()
        query = "select p.cod_producto,p.nom_producto,a.cantidad,a.orientacion from atencion_producto as a inner join producto as p on a.cod_producto = p.cod_producto where a.cod_atencion = ?"
        cursor.execute(query,(cod_atencion[0]))
        receta = cursor.fetchall()
        
        control = 1
        retorno = ""
        if receta:
            for item in receta:
                conn = conectar()
                cursor = conn.cursor()
                query = "select * from Producto where cod_producto = ? and Stock > ? "
                cursor.execute(query,(item[0],item[2]))
                existencia = cursor.fetchone()
                if not existencia:
                    retorno += "\n Aun no contamos con este producto: "+item[1] +"\n"
                else:
                    retorno += "\n Contamos con este producto: "+item[1]+"\n"
            return retorno
        else:
            return "Usted no tiene recetas."   
    else:
        return "No entiendo tu solicitud."

def obtener_proximo_dia_semana(dia_semana):
    dias_semana = {
        'lunes': 0,
        'martes': 1,
        'miércoles': 2,
        'jueves': 3,
        'viernes': 4,
        'sábado': 5,
        'domingo': 6
    }
    
    hoy = datetime.today()
    dias_faltantes = (dias_semana[dia_semana.lower()] - hoy.weekday()) % 7
    proximo_dia_semana = hoy + timedelta(days=dias_faltantes)
    return proximo_dia_semana.date()




def es_feriado_nacional(fecha):
    url = f"https://calendarific.com/api/v2/holidays?api_key=zQNr5LqhJK3UHlgIkShftXX0g9oRnHlK&country=NI&year={fecha.year}&month={fecha.month}&day={fecha.day}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        holidays = data['response']['holidays']
        
        if holidays:
            return True
        
    return False




def procesar_abrir(solicitud, usuario):
    if 'proximo' in solicitud or 'este' in solicitud or 'abrirar' in solicitud or 'abrir' in solicitud:
        if 'lunes' in solicitud:
            fecha = obtener_proximo_dia_semana("lunes")
            if es_feriado_nacional(fecha):
                return "No abriremos debido a que es feriado nacional."
            else:
                return "Abriremos con normalidad, te esperamos."
        elif 'martes' in solicitud:
            fecha = obtener_proximo_dia_semana("martes")
            if es_feriado_nacional(fecha):
                return "No abriremos debido a que es feriado nacional."
            else:
                return "Abriremos con normalidad, te esperamos."
        elif 'miercoles' in solicitud:
            fecha = obtener_proximo_dia_semana("miercoles")
            if es_feriado_nacional(fecha):
                return "No abriremos debido a que es feriado nacional."
            else:
                return "Abriremos con normalidad, te esperamos."
        elif 'jueves' in solicitud:
            fecha = obtener_proximo_dia_semana("jueves")
            if es_feriado_nacional(fecha):
                return "No abriremos debido a que es feriado nacional."
            else:
                return "Abriremos con normalidad, te esperamos."
        elif 'viernes' in solicitud:
            fecha = obtener_proximo_dia_semana("viernes")
            if es_feriado_nacional(fecha):
                return "No abriremos debido a que es feriado nacional."
            else:
                return "Abriremos con normalidad, te esperamos."
        return "Ultima receta."
    elif 'feriado' in solicitud:
        # Agrega tu lógica para consultar los usuarios en la base de datos
        return "No abrimos los dias feriados."
    else:
        return "No entiendo tu solicitud."
    



# elif 'cita' in solicitud and ('receta' in solicitud or 'medicamento' in solicitud or 'producto' in solicitud):
#         # Agrega tu lógica para consultar los productos en la base de datos
#         return "Recetas de mis citas."
    

# Función para procesar la entrada del usuario y obtener la respuesta del chatbot
def procesar_entrada(filtered_tokens,usuario,app):
    
    # CITAS PENDIENTES DE LOS USUARIOS
    if 'cita' in filtered_tokens:
        resultado = procesar_consulta(filtered_tokens, usuario)
        return resultado
    # HORARIOS DE ATENCION
    elif 'receta' in filtered_tokens:
        resultado = procesar_receta(filtered_tokens, usuario,app)
        return resultado
    # PRECIOS DE LOS PRODUCTOS
    elif 'horario' in filtered_tokens:
        resultado = "Los horarios de Atención son de Lunes a Viernes de 8:00 am a 5:00 pm, Los Sabados de 8:00 am a 12:00 pm."
        return resultado
    # PRECIOS DE LOS PRODUCTOS
    elif 'abrir' in filtered_tokens or 'abrirar' in filtered_tokens:
        resultado = procesar_abrir(filtered_tokens, usuario)
        return resultado
    # PRECIOS DE LOS PRODUCTOS
    elif 'precio' in filtered_tokens or 'servicio' in filtered_tokens :
        
        return "Nuestros precios son: \nConsulta: 50 C$"
    elif 'Hola' in filtered_tokens or 'holar' in filtered_tokens:
        return "¡Hola, soy Vetbot En que le puedo ayudar!"
    else:
        return "No entiendo tu solicitud."