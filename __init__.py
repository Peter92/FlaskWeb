from __future__ import absolute_import
from flask import Flask, render_template, request, flash, url_for, escape
import traceback

from core.database import *
import core.tracking as tracking
from core.maintainance import clean_database
from core.constants import *
from core.hash import password_hash, password_check
from core.decorators import *
from core.validation import *
from extensions.flask_compress import Compress

app = Flask(__name__)
Compress(app)
mysql = DatabaseConnection(DATABASE_HOST, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD)

#Functions below are just for testing different features and are a mess


@app.route('/')
@session_start(mysql)
@set_template('index.html')
def index(session):

    try:
        session['count'] += 1
    except KeyError:
        session['count'] = 1

    print session['count'], url_for('login', email='what')
    return dict()


@app.route('/register', methods=['GET', 'POST'])
@session_start(mysql)
@set_template('register.html')
def register(session):
    errors = []
    if request.method == 'POST':
        
        errors += validate_email(request.form['email'])
        errors += validate_password(request.form['password'], request.form['password_confirm'])
        errors += validate_username(request.form['username'], empty=True)         
        
        if not errors:
            try:
                result = mysql.command.insert_account(request.form['email'], request.form['password'])
            except TypeError:
                errors.append('Bcrypt failed to work, please get in touch if this continues.')
            else:
                if result:
                    return redirect(url_for('login', email=request.form['email']))
                else:
                    errors += format_error_message('Email address', [VALIDATION_ERROR_EXISTS])
                    
    return dict(errors=errors)


@app.route('/login', methods=['GET', 'POST'])
@session_start(mysql)
@csrf_protection
@set_template('login.html')
def login(session):
    warnings = []
    errors = []
    autofocus = 'username'
    try:
        login_redirect = session['login_redirect']
    except KeyError:
        login_redirect = None
    
    if request.method == 'POST':

        #Don't allow login if page hasn't already been visited (may be a bot)
        if not session.get('allow_login', False):
            errors.append('There has been an error, please reload the page.'.format(url_for('login')))
        else:

            #Validate and figure out if input was email or username
            valid_email = not validate_email(request.form['username'])
            valid_username = not validate_username(request.form['username'], ignore_short=True, ignore_long=True)
            if not valid_email and not valid_username:
                errors.append('Invalid username/email.')
            else:
                autofocus = 'password'
            login_email = request.form['username'] if valid_email else None
            login_username = request.form['username'] if valid_username else None

            #Attempt to log in
            if not errors:
                
                account_id = mysql.command.get_account_id(email=login_email, username=login_username)
                result = mysql.command.login(account_id, request.form['password'], session['ip_id'], request.form['username'])

                if result['status'] > 0:
                    session.regenerate()
                    
                    session['account_data'] = result['account']
                    session['account_data']['captcha_check'] = False

                    #lookup known ips for said account
                    #if no match then ask for captcha

                    #update visit group with account id

                    if login_redirect is None:
                        return redirect(url_for('account'))
                    else:
                        return redirect(login_redirect)
                    
                else:
                    session['account_data'] = {}
                    errors += result['errors']
                    warnings += result['warnings']
    
    else:
        session['allow_login'] = True
        if not session.get('allow_login_redirect', False):
            try:
                del session['login_redirect']
                login_redirect = None
            except KeyError:
                pass
        
    #Delete redirect flag so that redirect will only work if form is submitted now
    try:
        del session['allow_login_redirect']
    except KeyError:
        pass
    
    return dict(errors=errors, warnings=warnings, login_redirect=login_redirect, autofocus=autofocus)
    

@app.route('/account')
@session_start(mysql)
@require_login
def account(session):
    return 'yeah'

@app.route('/test/')
@app.route('/test/<int:id>')
@session_start(mysql)
@set_template('test.html')
def test(session, id=0):
    print request.endpoint
    return 5


@app.route('/admin')
@session_start(mysql)
@require_admin
@set_template('admin.html')
def admin(session):
    return dict()

@app.route('/logout')
@session_start(mysql)
def logout(session):
    session['account_data'] = {}
    return 'logged out'


#Handle all error codes
from werkzeug.exceptions import default_exceptions

def create_error_function(name):
    def func(error, session):
        pass
    func.__name__ = name
    return func

for code in default_exceptions:
    func_name = 'error_{}'.format(code)
    func = create_error_function(func_name)

    func = set_template('error.html', code, mysql)(func)
    func = session_start(mysql)(func)
    func = app.errorhandler(code)(func)


app.secret_key = APP_SECRET_KEY
if __name__ == "__main__":
    clean_database(mysql)
    app.run()
