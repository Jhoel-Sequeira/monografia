# -*- coding: utf-8 -*-

import re
import locale
import spacy
import requests
from datetime import datetime, timedelta, time, date
from flask import current_app, session
from controllers.correo import enviar_correo_receta, enviar_correo
from conexion import conectar

nlp = spacy.load('es_core_news_sm')

# =========================
# Configuración de negocio
# =========================
HORARIO_LABORAL = {
    0: (time(8,0),  time(17,0)),  # lunes
    1: (time(8,0),  time(17,0)),
    2: (time(8,0),  time(17,0)),
    3: (time(8,0),  time(17,0)),
    4: (time(8,0),  time(17,0)),
    5: (time(8,0),  time(12,0)),  # sábado
    6: None                       # domingo: cerrado
}
_DIAS = ['lunes','martes','miercoles','miércoles','jueves','viernes','sabado','sábado','domingo']

# =========================
# Helpers generales
# =========================

def _formatea_fecha(fecha_hora):
    """Admite datetime o str 'YYYY-MM-DD HH:MM:SS'."""
    if isinstance(fecha_hora, datetime):
        return fecha_hora.strftime('%Y-%m-%d'), fecha_hora.strftime('%H:%M:%S')
    if isinstance(fecha_hora, str):
        try:
            dt = datetime.fromisoformat(fecha_hora)
            return dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M:%S')
        except ValueError:
            partes = fecha_hora.split()
            if len(partes) >= 2:
                return partes[0], partes[1]
            return fecha_hora, ""
    return str(fecha_hora), ""

def obtener_proximo_dia_semana(dia_semana):
    dias = {'lunes':0,'martes':1,'miercoles':2,'miércoles':2,'jueves':3,'viernes':4,'sabado':5,'sábado':5,'domingo':6}
    hoy = datetime.today()
    if dia_semana.lower() not in dias: return None
    faltan = (dias[dia_semana.lower()] - hoy.weekday()) % 7
    return (hoy + timedelta(days=faltan)).date()

def es_feriado_nacional(fecha):
    try:
        url = (f"https://calendarific.com/api/v2/holidays"
               f"?api_key=zQNr5LqhJK3UHlgIkShftXX0g9oRnHlK&country=NI"
               f"&year={fecha.year}&month={fecha.month}&day={fecha.day}")
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            data = r.json()
            holidays = data.get('response', {}).get('holidays', [])
            return bool(holidays)
    except Exception:
        return False
    return False

def dentro_horario_laboral(dt: datetime) -> bool:
    cfg = HORARIO_LABORAL.get(dt.weekday())
    if not cfg:
        return False
    inicio, fin = cfg
    return inicio <= dt.time() <= fin

# =========================
# Helpers búsqueda de productos (público / sin sesión)
# =========================

PALABRAS_RUIDO = {
    'precio','precios','stock','existencia','existencias','producto','productos',
    'tener','hay','disponible','disponibles','cuesta','vale','costo','costar',
    'ver','mostrar','busca','buscar','dame','decir','consultar','consulta',
    'de','del','la','el','los','las','un','una','unos','unas','para','por','con','al'
}

def _filtra_tokens_producto(tokens):
    """Quita palabras genéricas e insignificantes; retorna keywords para LIKE."""
    return [t for t in tokens if t not in PALABRAS_RUIDO and len(t) >= 2]

def _buscar_productos(tokens_busqueda, limite=10):
    """
    Busca en producto por nombre con OR entre tokens (LOWER(nom_producto) LIKE ?).
    Si no hay tokens útiles, no trae toda la tabla (retorna []).
    """
    if not tokens_busqueda:
        return []
    conn = conectar()
    try:
        cur = conn.cursor()
        condiciones = " OR ".join(["LOWER(nom_producto) LIKE ?"] * len(tokens_busqueda))
        sql = (
            f"SELECT TOP {limite} cod_producto, nom_producto, precio, stock "
            f"FROM producto WHERE {condiciones} ORDER BY nom_producto ASC"
        )
        params = [f"%{kw.lower()}%" for kw in tokens_busqueda]
        cur.execute(sql, params)
        filas = cur.fetchall()
        print(sql); print(params)
    finally:
        cur.close(); conn.close()
    return filas or []

def _respuesta_lista_productos(filas, solo_stock=False, solo_precio=False):
    if not filas:
        return "No encontré productos que coincidan con lo que pediste."
    lineas = []
    for cod, nombre, precio, stock in filas:
        if solo_stock:
            lineas.append(f"{nombre} (cod {cod}) → stock: {stock}")
        elif solo_precio:
            lineas.append(f"{nombre} (cod {cod}) → precio: {precio} C$")
        else:
            lineas.append(f"{nombre} (cod {cod}) → precio: {precio} C$, stock: {stock}")
    return "Coincidencias:\n" + "\n".join(lineas)

def consultar_productos_publico(filtered_tokens):
    """
    Consulta pública de productos por precio/stock usando los tokens lematizados.
    - Filtra ruido y arma un LIKE con OR entre palabras clave.
    - Detecta intención de solo stock / solo precio / ambos.
    """
    tokens_busqueda = _filtra_tokens_producto(filtered_tokens)
    filas = _buscar_productos(tokens_busqueda, limite=10)
    tokens_set = set(filtered_tokens)
    solo_stock  = any(t in tokens_set for t in ['stock','existencia','existencias'])
    solo_precio = any(t in tokens_set for t in ['precio','precios'])
    if solo_stock and not solo_precio:
        return _respuesta_lista_productos(filas, solo_stock=True)
    if solo_precio and not solo_stock:
        return _respuesta_lista_productos(filas, solo_precio=True)
    return _respuesta_lista_productos(filas)

# =========================
# Parseo de fecha/hora desde texto (para agendar)
# =========================

def _normaliza_pm(hh:int, pm:bool) -> int:
    if pm and hh < 12: return hh + 12
    if not pm and hh == 12: return 0
    return hh

def _parse_hora(txt:str):
    """
    Retorna (hh, mm) o None. Soporta:
    - '15:30', '15.30', '15 30'
    - '3pm', '3 pm', '3:15 pm', '03:15p.m.'
    - '3 de la tarde', '3 de la mañana'
    """
    txt_l = txt.lower()
    m = re.search(r'(\b\d{1,2})(?:[:.\s](\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?\b', txt_l)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2)) if m.group(2) else 0
        suf = m.group(3)
        pm = False
        if suf:
            pm = 'p' in suf
        else:
            if 'tarde' in txt_l or 'noche' in txt_l:
                pm = True
        hh = _normaliza_pm(hh, pm)
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return hh, mm
    return None

def _parse_fecha_absoluta(txt:str):
    """
    Soporta:
    - '25/08/2025', '25-08-2025', '25/8/25'
    - '2025-08-25'
    """
    txt_l = txt.lower()
    m = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', txt_l)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100: y += 2000
        try:
            return date(y, mth, d)
        except ValueError:
            return None
    m = re.search(r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b', txt_l)
    if m:
        y, mth, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mth, d)
        except ValueError:
            return None
    return None

def _parse_fecha_relativa_o_dow(txt:str):
    """
    'hoy', 'mañana', 'pasado mañana', 'próximo lunes', 'este jueves', 'lunes'
    """
    txt_l = txt.lower()
    hoy = datetime.today().date()
    if 'pasado mañana' in txt_l or 'pasadomanana' in txt_l:
        return hoy + timedelta(days=2)
    if 'mañana' in txt_l or 'manana' in txt_l:
        return hoy + timedelta(days=1)
    if 'hoy' in txt_l:
        return hoy
    for d in _DIAS:
        if d in txt_l:
            base = obtener_proximo_dia_semana(d)
            if 'próximo' in txt_l or 'proximo' in txt_l:
                if base == hoy:
                    base = base + timedelta(days=7)
            return base
    return None

def _parse_datetime_desde_texto(txt:str) -> datetime | None:
    """
    Combina fecha y hora detectadas. Si solo hay hora:
      - Usa hoy si la hora futura todavía no pasó; si ya pasó, usa mañana.
    Si solo hay fecha:
      - Usa 9:00 por defecto.
    """
    f_abs = _parse_fecha_absoluta(txt)
    f_rel = _parse_fecha_relativa_o_dow(txt)
    h     = _parse_hora(txt)
    hoydt = datetime.today()

    if f_abs or f_rel:
        f = f_abs or f_rel
        if h:
            hh, mm = h
            return datetime(f.year, f.month, f.day, hh, mm)
        return datetime(f.year, f.month, f.day, 9, 0)

    if h:
        hh, mm = h
        cand = hoydt.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if cand <= hoydt:
            cand = cand + timedelta(days=1)
        return cand

    return None

# =========================
# Citas (con BD)
# =========================

def consultar_citas_pendientes(usuario):
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute('SELECT fecha_atencion FROM atencion WHERE id_estado = 10 AND num_cliente = ?', (usuario,))
        fila = cur.fetchone()
    finally:
        cur.close(); conn.close()

    if not fila or not fila[0]:
        return "No tienes citas pendientes."

    fecha, hora = _formatea_fecha(fila[0])
    return f"Tiene una cita pendiente para la fecha: {fecha}" + (f" a las {hora}." if hora else ".")

def _existe_conflicto_exact(usuario, dt: datetime) -> bool:
    """Conflicto exacto: misma fecha/hora para el mismo usuario con estado pendiente."""
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM atencion WHERE num_cliente = ? AND id_estado = 10 AND CONVERT(datetime, fecha_atencion) = ?",
            (usuario, dt)
        )
        return cur.fetchone() is not None
    finally:
        cur.close(); conn.close()

def _insertar_cita_raw(cliente, mascota, peso, altura, observacion, hora, fecha, atencion, temperatura) -> bool:
    """
    Inserción igual a tu endpoint /agendarCita, usada desde el flujo del chatbot.
    hora: string 'HH:MM AM/PM'; fecha: string 'YYYY-MM-DD'
    """
    try:
        fecha_hora_str = f"{fecha} {hora}"
        fecha_hora = datetime.strptime(fecha_hora_str, "%Y-%m-%d %I:%M %p")

        # Para correo legible
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
        dia = fecha_obj.strftime("%d")
        try:
            locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8')
        except Exception:
            pass
        mes = fecha_obj.strftime("%B").capitalize()

        conn = conectar()
        cur = conn.cursor()
        query = ('INSERT INTO atencion (fecha_atencion,num_cliente,id_estado,num_veterinario,idMascota,'
                 'tipo_atencion,peso,altura,temperatura,descripcion,costo) VALUES (?,?,?,?,?,?,?,?,?,?,?)')
        cur.execute(query, (fecha_hora, cliente, 10, 6, mascota, atencion, peso, altura, temperatura, observacion, 0))
        conn.commit()
        cur.close(); conn.close()

        # correo al cliente
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT correo_cliente FROM cliente WHERE num_cliente = ?", (cliente,))
        correo = cur.fetchone()
        cur.close(); conn.close()
        if correo and correo[0]:
            enviar_correo(current_app, "Usted tiene una nueva cita", correo[0], 'agendar', dia, mes, hora)
        return True
    except Exception as e:
        print("Error insertando cita desde chatbot:", e)
        try:
            conn.rollback()
        except:
            pass
        try:
            cur.close(); conn.close()
        except:
            pass
        return False

def _listar_mascotas(usuario):
    """
    Devuelve lista [(idMascota, nombre)] del cliente.
    Ajusta nombres de tabla/columnas si difieren.
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute("SELECT idMascota, nombre_Mascota FROM mascota WHERE num_cliente = ?", (usuario,))
        filas = cur.fetchall()
    finally:
        cur.close(); conn.close()
    return filas or []

def _horas_disponibles_db(fecha: str):
    """
    Lógica de /horasDisponibles: bloques 08:00-12:00 y 13:00-17:00, intervalos de 45 min.
    Retorna lista 'HH:MM AM/PM'.
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT CONVERT(varchar(5), fecha_atencion, 108) AS hora_atencion 
            FROM atencion 
            WHERE CONVERT(date, fecha_atencion) = ?;
        """, (fecha,))
        ocupadas = cur.fetchall()
    finally:
        cur.close(); conn.close()

    horas_ocupadas = [datetime.strptime(h[0], '%H:%M') for h in ocupadas]

    horarios = [('08:00','12:00'), ('13:00','17:00')]
    intervalos = []
    for inicio, fin in horarios:
        hora_actual = datetime.strptime(inicio, '%H:%M')
        hora_fin    = datetime.strptime(fin, '%H:%M')
        while hora_actual + timedelta(minutes=45) <= hora_fin:
            intervalo_ocupado = any(
                ocup <= hora_actual < ocup + timedelta(minutes=45)
                for ocup in horas_ocupadas
            )
            if not intervalo_ocupado:
                intervalos.append(hora_actual.strftime('%I:%M %p'))
            hora_actual += timedelta(minutes=45)
    return intervalos

# =========================
# Flujo interactivo: agendar cita (pide MASCOTA primero)
# =========================

def _flow_reset():
    session.pop('flow_agendar', None)

def _flow_get():
    return session.setdefault('flow_agendar', {
        'step': 'mascota',     # mascota → fecha → elegir_hora → atencion → confirmar
        'mascota': None,
        'fecha': None,         # 'YYYY-MM-DD'
        'hora': None,          # 'HH:MM AM/PM'
        'atencion': None,      # texto
        'peso': None,          # opcional
        'altura': None,        # opcional
        'temperatura': None,   # opcional
        'observacion': None    # opcional
    })

def _extraer_fecha_y_hora(texto_original):
    dt = _parse_datetime_desde_texto(texto_original)
    if not dt:
        return None, None
    f = dt.strftime("%Y-%m-%d")
    h = dt.strftime("%I:%M %p")
    return f, h

def procesar_agendar_interactivo(usuario, texto_original):
    flow = _flow_get()

    # Paso 1: MASCOTA
    if flow['step'] == 'mascota':
        mascotas = _listar_mascotas(usuario)
        if not mascotas:
            _flow_reset()
            return "No encontré mascotas registradas en tu cuenta. Agrega una mascota antes de agendar."
        # Acepta: "mascota 7", "id 7", "ID:7", "mascota: 7"
        m = re.search(r'\b(?:id|mascota)\s*[:#-]?\s*(\d+)\b', (texto_original or "").lower())
        if m:
            sel = int(m.group(1))
            if any(mid == sel for mid, _ in mascotas):
                flow['mascota'] = sel
                flow['step'] = 'fecha'
            else:
                lista = "\n".join([f"{mid} - {nom}" for mid, nom in mascotas])
                return f"No encontré la mascota con ID {sel}. Tus mascotas:\n{lista}\n\nResponde con: 'mascota <ID>'."
        else:
            lista = "\n".join([f"{mid} - {nom}" for mid, nom in mascotas])
            return f"Para agendar, dime **la mascota**. Tus mascotas registradas:\n{lista}\n\nResponde con: 'mascota <ID>'."

    # Paso 2: FECHA (y opcionalmente hora)
    if flow['step'] == 'fecha':
        f, h = _extraer_fecha_y_hora(texto_original)
        if not f:
            return "¿Para qué fecha quieres la cita? (Ej: 2025-08-25, 'mañana', 'próximo lunes')"
        try:
            f_date = datetime.strptime(f, "%Y-%m-%d").date()
        except ValueError:
            return "Formato de fecha inválido. Usa 'YYYY-MM-DD' o frases como 'mañana/próximo lunes'."
        if f_date < datetime.now().date():
            return "La fecha indicada ya pasó. Elige una fecha futura."
        if f_date.weekday() == 6:
            return "Los domingos no atendemos. Elige otro día."
        if es_feriado_nacional(f_date):
            return "Es feriado nacional. Elige otro día, por favor."
        flow['fecha'] = f
        if h:
            flow['hora'] = h
            flow['step'] = 'atencion'
        else:
            flow['step'] = 'elegir_hora'

    # Paso 3a: Sugerir HORAS disponibles
    if flow['step'] == 'elegir_hora':
        horas = _horas_disponibles_db(flow['fecha'])
        if not horas:
            flow['step'] = 'fecha'
            return "Ese día ya no tiene horas disponibles. Elige otra fecha."
        lista = ", ".join(horas[:12]) + (" ..." if len(horas) > 12 else "")
        return f"Estas son las horas disponibles para {flow['fecha']} (intervalos de 45 min):\n{lista}\n\nResponde con una hora (ej: 10:30 AM)."

    # Paso 3b: Capturar HORA
    if flow['step'] == 'elegir_hora' or (flow['step'] == 'atencion' and not flow['hora']):
        m = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm|a\.?m\.?|p\.?m\.?)\b', (texto_original or "").lower())
        if m:
            hh = int(m.group(1)); mm = int(m.group(2)); suf = m.group(3)
            suf = 'AM' if 'a' in suf else 'PM'
            flow['hora'] = f"{hh:02d}:{mm:02d} {suf}"
        elif flow['step'] == 'elegir_hora':
            return "No reconocí la hora. Usa formato como '10:30 AM' o '03:15 PM'."

    # Paso 4: Tipo de ATENCIÓN
    if flow['step'] in ['fecha','elegir_hora'] and flow['hora']:
        flow['step'] = 'atencion'

    if flow['step'] == 'atencion':
        m = re.search(r'(control|vacuna|consulta|desparasitación|desparasitacion|cirugía|cirugia|profilaxis|urgencia)', (texto_original or "").lower())
        if m:
            flow['atencion'] = m.group(1)
            flow['step'] = 'confirmar'
        else:
            return "¿Qué tipo de atención necesitas? (ej: consulta, vacuna, control, desparasitación, cirugía, profilaxis, urgencia)"

    # Paso 5: Confirmar e insertar (opcionales: peso/altura/temperatura/observación)
    if flow['step'] == 'confirmar':
        try:
            dt = datetime.strptime(f"{flow['fecha']} {flow['hora']}", "%Y-%m-%d %I:%M %p")
        except ValueError:
            flow['step'] = 'elegir_hora'
            return "Hora inválida. Elige una hora como '10:30 AM'."

        if dt <= datetime.now():
            flow['step'] = 'fecha'
            return "La fecha/hora indicada ya pasó. Elige otra fecha u hora."

        if not dentro_horario_laboral(dt):
            flow['step'] = 'elegir_hora'
            return "La cita debe estar dentro del horario (L-V 8:00–17:00, S 8:00–12:00). Elige otra hora."

        if es_feriado_nacional(dt.date()):
            flow['step'] = 'fecha'
            return "Es feriado nacional. Elige otro día, por favor."

        if _existe_conflicto_exact(usuario, dt):
            flow['step'] = 'elegir_hora'
            return "Ya tienes una cita pendiente a esa hora. Elige otra franja."

        # Relleno opcionales si vienen en el texto
        if flow.get('peso') is None:
            m = re.search(r'\bpeso\s*(\d+(?:\.\d+)?)', (texto_original or "").lower())
            if m: flow['peso'] = float(m.group(1))
        if flow.get('altura') is None:
            m = re.search(r'\baltura\s*(\d+(?:\.\d+)?)', (texto_original or "").lower())
            if m: flow['altura'] = float(m.group(1))
        if flow.get('temperatura') is None:
            m = re.search(r'\btemp(?:eratura)?\s*(\d+(?:\.\d+)?)', (texto_original or "").lower())
            if m: flow['temperatura'] = float(m.group(1))
        if flow.get('observacion') is None:
            m = re.search(r'(observaci[oó]n|nota|detalle)\s*:\s*(.+)$', (texto_original or "").lower())
            if m: flow['observacion'] = m.group(2)[:250]

        mascota     = flow['mascota']
        fecha       = flow['fecha']
        hora        = flow['hora']
        atencion    = flow['atencion']
        peso        = flow.get('peso') or 0
        altura      = flow.get('altura') or 0
        temperatura = flow.get('temperatura') or 0
        obs         = flow.get('observacion') or ''

        ok = _insertar_cita_raw(
            cliente=usuario, mascota=mascota, peso=peso, altura=altura,
            observacion=obs, hora=hora, fecha=fecha,
            atencion=atencion, temperatura=temperatura
        )
        if ok:
            _flow_reset()
            return f"Cita agendada ✔️ para la mascota {mascota} el {fecha} a las {hora} ({atencion})."
        else:
            return "No pude agendar la cita por un problema interno. Intenta de nuevo."

    # Fallback de paso
    return "Sigamos con el agendamiento. Indícame la mascota con: 'mascota <ID>'."

# =========================
# Recetas y abrir (existentes)
# =========================

def procesar_consulta(solicitud, usuario):
    if 'cita' in solicitud and 'pendiente' in solicitud:
        return consultar_citas_pendientes(usuario)

    if 'cita' in solicitud and any(w in solicitud for w in ['pasado','anterior','ultimo','último']):
        conn = conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                'SELECT TOP 1 fecha_atencion FROM atencion WHERE id_estado = 14 AND num_cliente = ? ORDER BY fecha_atencion DESC',
                (usuario,)
            )
            fila = cur.fetchone()
        finally:
            cur.close(); conn.close()

        if not fila or not fila[0]:
            return "No tiene registro de citas."

        fecha, hora = _formatea_fecha(fila[0])
        return f"Su ultima cita fue: {fecha}" + (f" a las {hora}." if hora else ".")

    return "No entiendo tu solicitud."

def procesar_receta(solicitud, usuario, app):
    # Enviar la última receta por correo
    if ('receta' in solicitud and ('ultimo' in solicitud or 'último' in solicitud)) or \
       any(w in solicitud for w in ['enviame','mandar','mandame','enviser','enviemir','enviar']):
        conn = conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT TOP 1 a.cod_atencion, c.correo_cliente "
                "FROM atencion a INNER JOIN cliente c ON a.num_cliente = c.num_cliente "
                "WHERE c.num_cliente = ? ORDER BY fecha_atencion DESC", (usuario,)
            )
            cab = cur.fetchone()
            if not cab:
                return "Usted no tiene ninguna receta."
            cod_atencion, correo = cab[0], cab[1]

            cur.execute(
                "SELECT a.cod_detalle, p.nom_producto, p.precio, a.cantidad, a.orientacion "
                "FROM atencion_producto a INNER JOIN producto p ON a.cod_producto = p.cod_producto "
                "WHERE a.cod_atencion = ?", (cod_atencion,)
            )
            consultas = cur.fetchall()

            cur.execute("SELECT diagnostico, cod_atencion FROM atencion WHERE cod_atencion = ?", (cod_atencion,))
            diagnostico = cur.fetchall()
        finally:
            cur.close(); conn.close()

        if consultas:
            enviar_correo_receta(current_app, "Usted tiene una nueva receta", correo, 'recetar', consultas, diagnostico)
            return "Receta Enviada.."
        return "Usted no tiene ninguna receta."

    # Verificar existencia de productos de la receta
    if 'receta' in solicitud and 'tener' in solicitud and any(w in solicitud for w in ['producto','existe','existencia']):
        conn = conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT TOP 1 a.cod_atencion, c.correo_cliente "
                "FROM atencion a INNER JOIN cliente c ON a.num_cliente = c.num_cliente "
                "WHERE c.num_cliente = ? ORDER BY fecha_atencion DESC", (usuario,)
            )
            cab = cur.fetchone()
            if not cab:
                return "Usted no tiene recetas."
            cod_atencion = cab[0]

            cur.execute(
                "SELECT p.cod_producto, p.nom_producto, a.cantidad, a.orientacion "
                "FROM atencion_producto a INNER JOIN producto p ON a.cod_producto = p.cod_producto "
                "WHERE a.cod_atencion = ?", (cod_atencion,)
            )
            receta = cur.fetchall()
        finally:
            cur.close(); conn.close()

        if not receta:
            return "Usted no tiene recetas."

        msgs = []
        for cod_prod, nombre, cantidad, _ in receta:
            conn2 = conectar()
            try:
                c2 = conn2.cursor()
                c2.execute("SELECT 1 FROM producto WHERE cod_producto = ? AND stock > ?", (cod_prod, cantidad))
                existe = c2.fetchone()
            finally:
                c2.close(); conn2.close()
            msgs.append(f"{'Contamos' if existe else 'Aún no contamos'} con este producto: {nombre}")
        return "\n".join(msgs)

    return "No entiendo tu solicitud."

def procesar_abrir(solicitud, usuario=None):
    if any(w in solicitud for w in ['proximo','próximo','este','abrirar','abrir']):
        for d in _DIAS:
            if d in solicitud:
                fecha = obtener_proximo_dia_semana(d)
                if not fecha:
                    break
                if es_feriado_nacional(fecha):
                    return "No abriremos debido a que es feriado nacional."
                return "Abriremos con normalidad, te esperamos."
        return "Abrimos de lunes a viernes y sábados en horario regular, salvo feriados nacionales."
    if 'feriado' in solicitud:
        return "No abrimos los dias feriados."
    return "No entiendo tu solicitud."

# =========================
# Routers
# =========================

def procesar_entrada(filtered_tokens, usuario, app, texto_original: str = ""):
    tokens = set(filtered_tokens)

    # Agendar cita (flujo interactivo, requiere login)
    if ('cita' in tokens) and any(t in tokens for t in ['agendar','agenda','agendo','reservar','programar','programa']):
        return procesar_agendar_interactivo(usuario, texto_original or " ".join(filtered_tokens))

    # Consultas de citas existentes
    if 'cita' in tokens and not any(t in tokens for t in ['agendar','agenda','agendo','reservar','programar','programa']):
        return procesar_consulta(filtered_tokens, usuario)

    # Recetas
    if 'receta' in tokens:
        return procesar_receta(filtered_tokens, usuario, app)

    # Información general
    if 'horario' in tokens or 'hora' in tokens:
        return "Los horarios de Atención son de Lunes a Viernes de 8:00 am a 5:00 pm, Los Sabados de 8:00 am a 12:00 pm."

    if 'abrir' in tokens or 'abrirar' in tokens or 'proximo' in tokens or 'próximo' in tokens or 'este' in tokens:
        return procesar_abrir(filtered_tokens, usuario)

    if 'precio' in tokens or 'servicio' in tokens:
        return "Nuestros precios son: \nConsulta: 50 C$"

    if 'hola' in tokens:
        return "¡Hola, soy Vetbot! ¿En qué le puedo ayudar?"

    return "No entiendo tu solicitud."

def procesar_entrada_publica(filtered_tokens):
    tokens = set(filtered_tokens)

    # No requieren BD
    if 'horario' in tokens or 'hora' in tokens:
        return "Los horarios de Atención son de Lunes a Viernes de 8:00 am a 5:00 pm, Los Sabados de 8:00 am a 12:00 pm."

    if 'abrir' in tokens or 'abrirar' in tokens or 'proximo' in tokens or 'próximo' in tokens or 'este' in tokens or 'feriado' in tokens:
        return procesar_abrir(filtered_tokens)

    # Consulta pública a BD para productos (precio/stock)
    if 'precio' in tokens or 'precios' in tokens or 'stock' in tokens or 'existencia' in tokens or 'existencias' in tokens or 'producto' in tokens or 'productos' in tokens:
        return consultar_productos_publico(filtered_tokens)

    if 'hola' in tokens:
        return "¡Hola! Puedes preguntarme por horarios, precios, stock de productos o si abrimos un día específico."

    # Requieren sesión
    if 'cita' in tokens or 'receta' in tokens:
        return "Para ver o agendar citas y para recetas necesito identificar tu usuario. Inicia sesión y vuelve a preguntar, por favor."

    return "Puedo ayudarte con horarios, precios, stock de productos y si abrimos ciertos días. ¿Qué te gustaría saber?"
