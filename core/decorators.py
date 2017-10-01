#These are the decorators to be used with the function for each web page.
#The order may go something like below:
#
#   @app.route('/account')
#   @session_start(mysql)
#   @require_login
#   @set_template('account.html')
#   def account_page(session):
#       return dict(account_id = session['account_id'])

from __future__ import absolute_import
from functools import wraps
from flask import redirect, url_for, abort, request, make_response, render_template

from core.session import SessionManager


def set_template(template):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if result is None:
                result = {}
            elif not isinstance(result, dict):
                return result
            return render_template(template, **result)
        return wrapper
    return decorator
    

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
