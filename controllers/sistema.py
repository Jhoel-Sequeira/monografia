# controllers/sistema.py
from flask import Blueprint

bp = Blueprint('sistema', __name__)

@bp.route('/sistema')
def sistema_route():
    return 'Ruta del sistema'
