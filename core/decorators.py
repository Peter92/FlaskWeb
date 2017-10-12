#These are the decorators to be used with the function for each web page.
#@app.route must start followed by @session_start. @set_template if set should be the last in the list.
#Anything in the middle may be in any order.
#Example below:
#
#   @app.route('/account')
#   @session_start(mysql)
#   @require_login
#   @csrf_protection
#   @set_template('account.html')
#   def account_page(session):
#       return dict(account_id = session['account_id'])

from __future__ import absolute_import, division
from functools import wraps
from flask import redirect, url_for, abort, request, make_response, render_template
from werkzeug.routing import BuildError
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import HTTPException
import traceback
import time

from core.constants import *
from core.session import SessionManager
from core.tracking import *
    

def set_template(template, status_code=200, mysql=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
                
            #Catch login redirect request from url
            if request.args.get('login', False):
                return require_login(func)(*args, **kwargs)
            
            #Get result from function
            result = func(*args, **kwargs)
            if result is None:
                result = {}
            
            #Skip rendering template if a string was returned
            elif not isinstance(result, dict):
                return result
            
            #Deal with status code errors
            if 'error_format' not in result:
                result['error_format'] = '{} {}'.format(status_code, HTTP_STATUS_CODES.get(status_code, 'Unknown Status Code'))
                for i in args:
                    if isinstance(i, HTTPException):
                        result['status_description'] = i.description.split('  ')
                if status_code == 500 and not result.get('status_description', False):
                    result['traceback'] = traceback.format_exc()
                    
            if mysql is not None and status_code // 100 != 2:
                mysql.command.log_status_code(status_code, kwargs['session']['group_id'])
            
            result['debug'] = {}
            if not PRODUCTION_SERVER:
                result['debug']['css_nocache'] = '?random={}'.format(int(time.time()))
            
            #Render the response
            response = render_template(template,
                                       get_data=request.args, post_data=request.form, session=kwargs['session'],
                                       login_url=_get_redirect_url(func, _add_queries={'login': '1'}),
                                       **result), status_code
            return _add_response_headers(response)
        return wrapper
    return decorator
    

def _get_redirect_url(func, _add_queries={}, *args, **kwargs):
    """Get current URL so things like login can redirect back to it."""
    try:
        redirect_url = url_for(func.__name__, **kwargs)
    except BuildError:
        return url_for('login')

    #Remove unneeded query values
    ignore = set(['login'])
    query_list = []
    if request.query_string:
        for query in request.query_string.split('&'):
            if query.split('=', 1)[0].lower() not in ignore:
                query_list.append(query)
        
    for k, v in _add_queries.iteritems():
        query_list.append('{}={}'.format(k, v))
    
    if not query_list:
        return redirect_url
    return '{}?{}'.format(redirect_url, '&'.join(query_list))


def session_start(mysql):
    """Wrap the code in the SessionManager class."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with SessionManager(mysql) as session:
                return func(session=session, *args, **kwargs)
        return wrapper
    return decorator

    
def require_admin(func):
    """Result in 401 error if user is not admin."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs['session'].get('account_data', {}).get('permission', 0) < PERMISSION_ADMIN:
            abort(401)
        return func(*args, **kwargs)
    return wrapper
    
    
def require_login(func):
    """Load login page with redirection if user is not logged in."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not kwargs['session'].get('account_data', {}).get('id', 0):
            kwargs['session']['login_redirect'] = _get_redirect_url(func)
            kwargs['session']['allow_login_redirect'] = True
            kwargs['session'].exit()
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

    
def csrf_protection(func):
    """Stop cross-site request forgery attacks.
    Idea modified from http://flask.pocoo.org/snippets/3/
    Added ideas from https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)_Prevention_Cheat_Sheet
    
    One token is generated per session, along with the field name for it.
    The idea of generating one per form looks good on paper, 
    but actually causes issues when resubmitting forms through browser controls.
    
    Possible bug (not tested):
        Internet Explorer 11 does not add the Origin header on a CORS request across sites of a trusted zone. 
        The Referer header will remain the only indication of the UI origin.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == "POST":
            
            #Read headers
            origin = get_origin() or get_referrer()
            try:
                if not origin:
                    raise TypeError
                origin_match = get_url_root().startswith(origin)
            
            #No origin or request headers
            except TypeError:
                origin_match = ACCEPT_REQUEST_WITH_NO_HEADERS
                if not PRODUCTION_SERVER and not ACCEPT_REQUEST_WITH_NO_HEADERS:
                    print 'Denied POST request due to no origin or referrer headers being present.'
            
            #Check CSRF token
            if kwargs['session']['csrf_token'] != request.form.get(kwargs['session']['csrf_form'], None) or not origin_match:
                abort(403)
                
        return func(*args, **kwargs)
    return wrapper

    
def _add_response_headers(output):
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
    
    
def set_content_type(content_type):
    """Change the content type of a page to allow things like rendering images."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return result, 200, {'Content-Type': content_type}
        return wrapper
    return decorator
