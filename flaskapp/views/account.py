from flask import Blueprint, jsonify

from ..database import *


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


@app.route('/login')
def login():
    pass


@app.route('/register')
def register():
    pass


@app.route('/register/success')
def register_success():
    pass


@app.route('/register/success/<string:activation_code>')
def account_activate(activation_code):
    pass


@app.route('/login/reset')
def reset_password():
    pass