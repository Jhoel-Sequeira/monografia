import pyodbc

def conectar():
    server = 'CRNDEVIT'
    database = 'FEC'
    username = 'sistemacrn'
    password = 'L8JZus@G1h&3'
    driver= '{ODBC Driver 17 for SQL Server}'

    # crear la cadena de conexión
    connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"

    # conectar a la base de datos
    conn = pyodbc.connect(connection_string)
    return conn