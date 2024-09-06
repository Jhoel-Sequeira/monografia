from flask import Flask

# Crea la instancia de la aplicación Flask
app = Flask(__name__)

# Importa los controladores
from controllers import web
from controllers import sistema

# Registra los Blueprints (si usas Blueprints)
app.register_blueprint(web.bp)
app.register_blueprint(sistema.bp)

if __name__ == '__main__':
    app.run(debug=True)
