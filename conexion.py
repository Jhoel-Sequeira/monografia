import pyodbc


# TRABAJO
def conectar():
    server = 'CRNDEVIT'
    database = 'Vet_ElBuenProductor'
    username = 'sistemacrn'
    password = 'L8JZus@G1h&3'
    driver= '{ODBC Driver 17 for SQL Server}'

    # crear la cadena de conexión
    connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"

    # conectar a la base de datos
    conn = pyodbc.connect(connection_string)
    return conn


    # CASA
# def conectar():
#     server = 'DESKTOP-EU0OJJ3'
#     database = 'Vet_ElBuenProductor'
#     driver= '{ODBC Driver 17 for SQL Server}'

#     # Crear la cadena de conexión usando la autenticación integrada de Windows
#     connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes"

#     # Conectar a la base de datos
#     conn = pyodbc.connect(connection_string)
#     return conn