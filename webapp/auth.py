from functools import wraps
from flask import request, jsonify
import os

def require_api_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_token = request.headers.get('Authorization')
        if not api_token:
            return jsonify({'error': 'No API token provided'}), 401
            
        # Remove 'Bearer ' prefix if present
        if api_token.startswith('Bearer '):
            api_token = api_token[7:]
            
        # Compare with environment variable
        if api_token != os.getenv('API_TOKEN'):
            return jsonify({'error': 'Invalid API token'}), 401
            
        return f(*args, **kwargs)
    return decorated_function