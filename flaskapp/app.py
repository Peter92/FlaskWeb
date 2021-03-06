import os
import sys

from flask import Flask

# Add the repo to the path
sys.path.append(os.path.abspath(__file__).rsplit(os.path.sep, 2)[0])
from flaskapp.database import *
from flaskapp.views import blueprints

app = Flask(__name__)
app.debug = True
app.secret_key = 123
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
for blueprint in blueprints:
    app.register_blueprint(blueprint)

# Initialise the database and set the context (https://flask-sqlalchemy.palletsprojects.com/en/2.x/contexts)
db.init_app(app)
app.app_context().push()
db.create_all()

# Insert test records
admin = User(username='admin', email='admin@example.com', password='test')
guest = User(username='guest', email='guest@example.com', password='test')
db.session.add(admin)
db.session.add(guest)
db.session.commit()

admin.email = 'new@admin.com'
admin.password = 'pw'

p = PersistentLogin(user=admin, token='462642')
db.session.add(p)
db.session.commit()

session, new_token = PersistentLogin.get_session(admin, '462642', p.identifier)


if __name__ == "__main__":
    app.run()
