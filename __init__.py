from __future__ import absolute_import
from flask import Flask, render_template, request, flash, url_for, escape

from core.database import DatabaseConnection
import core.tracking as tracking
from core.session import session_start
from core.maintainance import Maintainance
from core.constants import *

app = Flask(__name__)
mysql = DatabaseConnection(DATABASE_HOST, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD)


#Functions below are just for testing different features and are a mess


@app.route('/')
@session_start(mysql)
def index(session):

    try:
        session['count'] += 1
    except KeyError:
        session['count'] = 1

    print session['count']
    return str(session.keys())
    #return render_template('index.html')

@app.route('/login', methods=['POST'])
@session_start(mysql)
def login(session):
    if request.method == 'POST':
        print 'login', escape(request.form['username'])
    else:
        print 'not POST yet'
    try:
        return str(session.pop('login_redirect'))
    except KeyError:
        go_to_page = None
    return render_template('login.html')


@app.route('/test/')
@app.route('/test/<int:id>')
@session_start(mysql)
def test(session, id=0):
    session['count'] += 1
    print session['count']
    return str(id)


@app.route('/admin')
@session_start(mysql, require_admin=True)
def admin(session):
    return 'u r admin'


@app.route('/maintainance')
def maintainance():
    m = Maintainance(mysql)
    print m.clear_sessions()
    return 'dun'

#@app.errorhandler(404)
#@session_start(mysql)
#def error_404(session):
#    return render_template('404.html'), 404

app.secret_key = APP_SECRET_KEY
if __name__ == "__main__":
    app.run()
