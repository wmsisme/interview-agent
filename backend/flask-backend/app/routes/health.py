from flask import Blueprint, current_app
from ..utils.response import success
from ..models import db
from sqlalchemy import text
import datetime

bp = Blueprint('health', __name__)

@bp.route('/health', methods=['GET'])
def health_check():
    try:
        db_status = 'CONNECTED'
        try:
            db.session.execute(text('SELECT 1'))
        except Exception as e:
            db_status = f'ERROR: {str(e)}'
        
        response = {
            'status': 'UP',
            'database': db_status,
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        
        return success(response)
    except Exception as e:
        return success({
            'status': 'DOWN',
            'database': 'UNKNOWN',
            'timestamp': datetime.datetime.utcnow().isoformat()
        })

@bp.route('/api/health', methods=['GET'])
def api_health_check():
    return health_check()

@bp.route('/api/test', methods=['GET'])
def test_endpoint():
    response = {
        'message': 'API is working',
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    return success(response)