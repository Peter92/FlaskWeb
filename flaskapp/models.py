from __future__ import absolute_import

import time

from flask_sqlalchemy import SQLAlchemy


__all__ = ['db', 'User', 'Email']


db = SQLAlchemy()


def unix_timestamp():
    """Get the current unix timestamp."""
    return int(time.time())


class User(db.Model):
    # Columns
    row_id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.row_id'), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.CHAR(60), nullable=False)
    
    # Relationships
    email = db.relationship('Email')

    # Automatic
    password_edited = db.Column(db.Integer, nullable=True)

    def __init__(self, **kwargs):
        # Convert to email object
        if 'email' in kwargs and not isinstance(kwargs['email'], Email):
            kwargs['email'] = Email(kwargs['email'])
        super(User, self).__init__(**kwargs)

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.username)


class Email(db.Model):
    row_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(128), unique=True, nullable=False)
    users = db.relationship('User', lazy=True)

    def __init__(self, address, **kwargs):
        super(Email, self).__init__(address=address, **kwargs)


@db.event.listens_for(User.password, 'set')
def password_edited(target, value, oldvalue, initiator):
    """Update password edited time"""
    if value != oldvalue:
        target.password_edited = unix_timestamp()
