from __future__ import absolute_import
from flask import Flask, render_template, request, flash, url_for, escape, send_from_directory
import traceback
import uuid

from core.database import *
import core.tracking as tracking
from core.maintainance import clean_database
from core.constants import *
from core.hash import password_hash, password_check
from core.decorators import *
from core.validation import *
#from core.sendmail import Mail
from extensions.flask_compress import Compress
#from extensions.html2text import *

app = Flask(__name__)
Compress(app)
mysql = DatabaseConnection(DATABASE_HOST, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD)

#Functions below are just for testing different features and are a mess

@app.route('/image/<string:id>.jpg')
def image_jpg(id):
    return send_from_directory('static', '{}.jpg'.format(id))
@app.route('/image/<string:id>.png')
def image_png(id):
    return send_from_directory('static', '{}.png'.format(id))
    
@app.route('/tracking/email/<string:id>.gif')
@set_content_type('image/gif')
def email_tracking(id):
    #write id to database
    #call it like this in the email - <img src="url_for('email_tracking', id='xxx')" style="display:none">
    return 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
    

@app.route('/wipe_server')
def _wipe():
    tables_to_wipe = [
        'accounts',
        'account_activation',
        'email_history',
        'email_queue',
        'emails',
        'ip_addresses',
        'languages',
        'login_attempts',
        'password_reset',
        'persistant_logins',
        'referrers',
        'status_codes',
        'temporary_storage',
        'urls',
        'user_agents',
        'visit_pages',
        'visit_groups'
    ]
    for table in tables_to_wipe:
        mysql.sql('TRUNCATE {}'.format(table))
        print 'Truncated table: {}'.format(table)
    return redirect(url_for('register'))


@app.route('/email/edit/<string:template_id>', methods=['GET', 'POST'])
@session_start(mysql)
@set_template('email_template_edit.html')
def email_template_edit(session, template_id):
    permission = session['account_data'].get('permission', PERMISSION_DEFAULT)
    allow_html = permission >= EMAIL_HTML_PERMISSION
    allow_html = True
    email_subject = None
    email_content = None
    email_preview = {}
    
    if request.method == 'POST':
        
        email_content = request.form['email_content']
        email_subject = request.form['email_subject']
        if not email_subject:
            email_subject = 'No Subject'
            
        email_preview['subject'] = email_subject
        if allow_html:
            email_preview['body'] = request.form['email_content']
            print list(html2text(request.form['email_content']))
            email_preview['plain'] = html2text(request.form['email_content']).replace('\n', '<br/>')
        else:
            email_preview['body'] = escape_html(request.form['email_content']).replace('\r', '<br/>')
        
        if 'submit_preview' in request.form:
            print 'u want preview'
        if 'submit_save' in request.form:
            print 'u want save'
        print email_content
    
    return dict(t_id=template_id, allow_html=allow_html, email_preview=email_preview,
                email_content=email_content, email_subject=email_subject)
    
@app.route('/email/edit/', methods=['GET', 'POST'])
@session_start(mysql)
@set_template('email_template_list.html')
def email_template_list(session):
    pass

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
@csrf_protection
@set_template('register.html')
def register(session):
    errors = []
    if request.method == 'POST':
        
        errors += validate_email(request.form['email'])
        errors += validate_password(request.form['password'], request.form['password_confirm'])
        errors += validate_username(request.form['username'], empty=True)         
        
        if not errors:
            try:
                result = mysql.command.insert_account(request.form['email'], request.form['password'], request.form['username'])
            except TypeError:
                errors.append('Bcrypt failed to work, please get in touch if this continues.')
            else:
                if result['status']:
                    session.exit()
                    return redirect(url_for('login', email=request.form['email']))
                else:
                    errors += result['errors']
                    
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
                result = mysql.command.login(account_id, request.form['password'], session['group_id'], session['ip_id'], request.form['username'])

                if result['status'] > 0:
                    session.regenerate()
                    
                    session['account_data'] = result['account']
                    session['account_data']['captcha_check'] = False

                    #lookup known ips for said account
                    #if no match then ask for captcha

                    #update visit group with account id

                    session.exit()
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

#Raise error codes
@app.route('/abort/<int:code>')
@session_start(mysql)
@set_template('error.html')
def abort_test(session, code):
    try:
        abort(code)
    except LookupError:
        valid_codes = ', '.join(map(str, sorted(default_exceptions.keys())))
        return dict(error_format='Unknown Error Code',
                    status_description=['Invalid error code provided.',
                                        'Valid codes are {}.'.format(valid_codes)])


app.secret_key = APP_SECRET_KEY
if __name__ == "__main__":
    clean_database(mysql)
    app.run()
