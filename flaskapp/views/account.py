from flask import Blueprint, jsonify

from ..database import *
from ..decorators import *
from flaskapp.utils.hash import password_check


app = Blueprint(__name__, __name__, template_folder='templates')


@app.route('/users')
@app.route('/user/<string:username>')
def test_page(username=None):
    if username is not None:
        user = db.session.query(User).filter(User.username==username).first()
        if user is None:
            users = []
        else:
            users = [user]
    else:
        users = db.session.query(User).all()
    return jsonify([dict(username=user.username, email=user.email.address) for user in users])


@app.route('/login', methods=['GET', 'POST'])
@set_template('login.html')
def login():
    data = {'errors': [], 'warnings': [], 'autofocus': None}
    if request.method == 'POST':
        email_input = request.form['email'].lower()
        password_input = request.form['password']

        email = Email.query.filter_by(address=email_input).first()
        user = User.query.filter(User.email==email).first()
        if not email_input:
            data['warnings'].append('Email is empty.')
            if data['autofocus'] is None:
                data['autofocus'] = 'email'
        if not password_input:
            data['warnings'].append('Password is empty.')
            if data['autofocus'] is None:
                data['autofocus'] = 'password'
        if user is None or not password_check(password_input, user.password):
            data['errors'].append('Invalid email or password.')
            if data['autofocus'] is None:
                data['autofocus'] = 'email'
        
    return data


@app.route('/register', methods=['GET', 'POST'])
@set_template('register.html')
def register():
    data = {'errors': [], 'autofocus': None}
    if request.method == 'POST':
        email_input = request.form['email'].lower()
        password_input = request.form['password']
        password2_input = request.form['password2']
        username_input = request.form['username']

        # Validation
        email = Email.query.filter_by(address=email_input).first()
        if email is not None and User.query.filter(User.email==email).first() is not None:
            data['errors'].append('User with this email already exists.')
            if data['autofocus'] is None:
                data['autofocus'] = 'email'
        if username_input and User.query.filter_by(username=username_input).first():
            data['errors'].append('Username already in use.')
            if data['autofocus'] is None:
                data['autofocus'] = 'username'
        if len(password_input) <= 6:
            data['errors'].append('Password must be longer than 6 characters.')
            if data['autofocus'] is None:
                data['autofocus'] = 'password'
        elif len(password_input) > 1024:
            data['errors'].append('Password must be shorter than 1024 characters.')
            if data['autofocus'] is None:
                data['autofocus'] = 'password'
        elif password_input != password2_input:
            data['errors'].append('Passwords don\'t match.')
            if data['autofocus'] is None:
                data['autofocus'] = 'password2'
        
        # Insert record
        if not data['errors']:
            user = User(email_input, password_input)
            if username_input:
                user.username = username_input
            db.session.add(user)
            db.session.commit()

    return data


@app.route('/register/success')
def register_success():
    pass


@app.route('/register/success/<string:activation_code>')
def account_activate(activation_code):
    pass


@app.route('/login/reset')
def reset_password():
    pass