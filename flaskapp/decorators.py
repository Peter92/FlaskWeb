import time
import traceback
from functools import wraps
from flask import redirect, request, render_template
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import HTTPException

from .common import *
from .constants import *


def set_template(template, status_code=200):
    """Set a template with the correct headers."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):            
            # Get result of page function
            result = func(*args, **kwargs)
            if result is None:
                result = {}
            
            # Skip template if a string was returned
            elif not isinstance(result, dict):
                return result
            
            result['debug'] = {}
            if not PRODUCTION_SERVER:
                result['debug']['css_nocache'] = '?random={}'.format(int(time.time()))
            
            #Render the response (request.args is GET, request.form is POST)
            response = render_template(template, request=request, **result), status_code
            return set_headers(response)
        return wrapper
    return decorator
