from flask import Flask
from flask_socketio import SocketIO


# Crea la instancia de la aplicación Flask
app = Flask(__name__)
socketio = SocketIO(app)
# Importa los controladores
from controllers import web
from controllers import sistema

# Registra los Blueprints (si usas Blueprints)
app.register_blueprint(web.bp)
app.register_blueprint(sistema.bp)
app.secret_key = 'your_secret_key'


if __name__ == '__main__':
    socketio.run(app, debug=True)
