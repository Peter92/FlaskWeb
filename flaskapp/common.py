from __future__ import absolute_import

import time
import uuid
from flask import make_response

from .constants import *


def unix_timestamp():
    return int(time.time())
    

def generate_uuid():
    return uuid.uuid4().hex


def set_headers(output):
    """Add any custom headers to the page before it is processed.

    Worth looking at:
        Content-Security-Policy: CSP not found on this site
        Cookies: Cookies not using httpOnly or secure flags
        Public-Key-Pins: HPKP not set on this site
        Strict-Transport-Security: HSTS is OK
    """
    
    response = make_response(output)
    response.headers['X-Frame-Options'] = "DENY"
    response.headers['X-XSS-Protection'] = 1
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    #Disable caching
    if not PRODUCTION_SERVER:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = 0
        
    return response
