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

from core.constants import *
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
                
            #Catch login redirect request from url
            if request.args.get('login', False):
                return require_login(func)(*args, **kwargs)
                
            return render_template(template, 
                                   get_data=request.args, post_data=request.form, session=kwargs['session'],
                                   page_url=_get_redirect_url(func, _add_queries={'login': '1'}),
                                   **result)
        return wrapper
    return decorator
    

def _get_redirect_url(func, _add_queries={}, *args, **kwargs):

    #Remove unneeded query values
    ignore = set(['login'])
    query_list = []
    if request.query_string:
        for query in request.query_string.split('&'):
            if query.split('=', 1)[0].lower() not in ignore:
                query_list.append(query)
        
    for k, v in _add_queries.iteritems():
        query_list.append('{}={}'.format(k, v))
    
    if query_list:
        return '{}?{}'.format(url_for(func.__name__, **kwargs), '&'.join(query_list))
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
        if kwargs['session'].get('account_data', {}).get('permission', 0) < PERMISSION_ADMIN:
            kwargs['session']['admin_redirect'] = _get_redirect_url(func)
            kwargs['session'].skip = True
            return add_response_headers(redirect(url_for('unauthorized')))
        return func(*args, **kwargs)
    return wrapper
    
    
def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not kwargs['session'].get('account_data', {}).get('id', 0):
            kwargs['session']['login_redirect'] = _get_redirect_url(func)
            kwargs['session']['allow_login_redirect'] = True
            kwargs['session'].skip = True
            return add_response_headers(redirect(url_for('login')))
        return func(*args, **kwargs)
    return wrapper


def add_response_headers(output):
    """Add any custom headers to the page before it is processed."""
    resp = make_response(output)
    resp.headers['X-Frame-Options'] = "DENY"
    resp.headers['X-XSS-Protection'] = 1
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    if not PRODUCTION_SERVER:
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = 0
    return resp
