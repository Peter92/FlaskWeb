from __future__ import absolute_import
from flask import Flask, render_template, request, flash, url_for, escape

from core.database import *
import core.tracking as tracking
from core.maintainance import clean_database
from core.constants import *
from core.hash import password_hash, password_check
from core.decorators import *
from core.validation import *

app = Flask(__name__)
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

    print session['count']
    return str(session.keys())


@app.route('/register', methods=['GET', 'POST'])
@session_start(mysql)
@set_template('register.html')
def register(session):
    errors = []
    print request.form
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
                    print 'account created'
                else:
                    errors += format_error_message('Email address', VALIDATION_ERROR_EXISTS)
                    

    return dict(errors=errors, form_data=request.form)


@app.route('/login', methods=['GET', 'POST'])
@session_start(mysql)
@set_template('login.html')
def login(session):
    if request.method == 'POST':
        print escape(request.form['username'])
        
        hashed = password_hash(request.form['password'], rounds=11)

        print password_check(password, hashed)
    
    try:
        go_to_page = session.pop('login_redirect')
    except KeyError:
        go_to_page = None
    print 'redirect to {}'.format(go_to_page)
    return dict(x='5')
    

@app.route('/account')
@session_start(mysql)
@require_login
def account(session):
    return 'yeah'

@app.route('/test/')
@app.route('/test/<int:id>')
@session_start(mysql)
def test(session, id=0):
    print request.endpoint
    return str(id)


@app.route('/admin')
@session_start(mysql)
@require_admin
def admin(session):
    return 'u r admin'

#@app.errorhandler(404)
#@session_start(mysql)
#def error_404(session):
#    return render_template('404.html'), 404

app.secret_key = APP_SECRET_KEY
if __name__ == "__main__":
    clean_database(mysql)
    app.run()
