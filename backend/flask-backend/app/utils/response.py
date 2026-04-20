from flask import jsonify

def success(data=None, message='success'):
    response = {
        'code': 200,
        'message': message,
        'data': data
    }
    return jsonify(response)

def error(message='error', code=500, data=None):
    response = {
        'code': code,
        'message': message,
        'data': data
    }
    return jsonify(response), code if code >= 400 else 500

def not_found(message='Resource not found'):
    return error(message, 404)

def bad_request(message='Bad request'):
    return error(message, 400)

def unauthorized(message='Unauthorized'):
    return error(message, 401)

def forbidden(message='Forbidden'):
    return error(message, 403)