from __future__ import absolute_import
from functools import wraps
from flask import redirect, url_for, abort, request, make_response

from core.session import SessionManager


def _get_redirect_url(func, *args, **kwargs):
    if request.query_string:
        return '{}?{}'.format(url_for(func.__name__, **kwargs), request.query_string)
    else:
        return url_for(func.__name__, **kwargs)

        
def session_start(mysql, require_login=False, require_admin=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with SessionManager(mysql) as session:
                return add_response_headers(func(session=session, *args, **kwargs))
        return wrapper
    return decorator

    
def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = kwargs.pop('session')
        if not session.get('admin', False):
            session['admin_redirect'] = _get_redirect_url(func)
            return add_response_headers(redirect(url_for('unauthorized')))
        return func(session=session, *args, **kwargs)
    return wrapper
    
    
def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = kwargs.pop('session')
        if not session.get('account_id', 0):
            session['login_redirect'] = _get_redirect_url(func)
            return add_response_headers(redirect(url_for('login')))
        return func(session=session, *args, **kwargs)
    return wrapper

    
def add_response_headers(output):
    resp = make_response(output)
    resp.headers["X-Frame-Options"] = "DENY"
    return resp
