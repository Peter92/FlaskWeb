from __future__ import absolute_import

import time
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from ..connect import db
from ..misc import unix_timestamp
from ...constants import Permissions
from ...utils.hash import password_hash


__all__ = ['User', 'Email']


class User(db.Model):
    # Columns
    row_id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.row_id'), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password = db.Column(db.CHAR(60), nullable=False)
    activated = db.Column(db.Boolean, default=0)
    permissions = db.Column(db.SmallInteger, default=Permissions.User)
    
    # Relationships
    email = db.relationship('Email')

    # Automatic
    password_edited = db.Column(db.Integer, nullable=False)
    added = db.Column(db.Integer, nullable=False)
    updated = db.Column(db.Integer, nullable=False)

    # Validation
    @validates('email')
    def validate_email(self, key, email):
        if not isinstance(email, Email):
            email = Email(email)
        return email

    @validates('password')
    def validate_password(self, key, password):
        return password_hash(password)

    # Overrides
    def __init__(self, email, password, username=None):
        # Convert to email object
        if not isinstance(email, Email):
            email = Email(email)
        super(User, self).__init__(email=email, password=password, username=username)

    def __repr__(self):
        return '<{} "{} ({})">'.format(self.__class__.__name__, self.username, self.email.address)


@db.event.listens_for(User, 'before_insert')
def user_insert(mapper, connection, target):
    target.added = unix_timestamp()
    target.updated = unix_timestamp()
    target.password_edited = unix_timestamp()


@db.event.listens_for(User, 'before_update')
def user_update(mapper, connection, target):
    target.updated = int(time.time())


@db.event.listens_for(User.password, 'set')
def user_password_update(target, value, oldvalue, initiator):
    """Update password edited time"""
    if value != oldvalue:
        target.password_edited = unix_timestamp()


class Email(db.Model):
    # Columns
    row_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(128), unique=True, nullable=False)
    users = db.relationship('User', lazy=True)

    # Automatic
    added = db.Column(db.Integer, nullable=False)
    updated = db.Column(db.Integer, nullable=False)

    @validates('address')
    def validate_address(self, key, address):
        assert '@' in address
        return address

    def __init__(self, address):
        super(Email, self).__init__(address=address)

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.address)


@db.event.listens_for(Email, 'before_insert')
def email_insert(mapper, connection, target):
    target.added = unix_timestamp()
    target.updated = unix_timestamp()


@db.event.listens_for(Email, 'before_update')
def email_update(mapper, connection, target):
    target.updated = unix_timestamp()
