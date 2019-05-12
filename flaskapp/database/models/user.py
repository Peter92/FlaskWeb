from __future__ import absolute_import

import time
import uuid
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import exc, validates

from ..connect import db
from ..misc import generate_uuid, unix_timestamp
from ...constants import UserPermissions
from ...utils.hash import quick_hash, password_hash


__all__ = ['User', 'Email', 'Activation', 'LoginAttempts', 'PasswordReset', 'PersistentLogin']


class User(db.Model):
    """User accounts."""
    # Columns
    row_id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.row_id'), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    password = db.Column(db.CHAR(60), nullable=False)
    activated = db.Column(db.Boolean, default=0)
    permissions = db.Column(db.SmallInteger, default=UserPermissions.Default)

    # Automatic
    password_edited = db.Column(db.Integer, nullable=False)
    created = db.Column(db.Integer, nullable=False)
    updated = db.Column(db.Integer, nullable=False)
    
    # Relationships
    email = db.relationship('Email')
    activation_codes = db.relationship('Activation', lazy=True)
    password_resets = db.relationship('PasswordReset', lazy=True)
    persistent_logins = db.relationship('PersistentLogin', lazy=True)

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
        super(User, self).__init__(email=email, password=password, username=username)

    def __repr__(self):
        return '<{} "{} ({})">'.format(self.__class__.__name__, self.username, self.email.address)


@db.event.listens_for(User, 'before_insert')
def user_insert(mapper, connection, target):
    target.created = unix_timestamp()
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
    """Email addresses.
    More than one account can have the same email, but the intention is that it will have the
    permission of UserPermissions.Deleted.
    """
    # Columns
    row_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(128), unique=True, nullable=False)

    # Automatic
    created = db.Column(db.Integer, nullable=False)
    updated = db.Column(db.Integer, nullable=False)

    # Relationships
    users = db.relationship('User', lazy=True)
    login_attempts = db.relationship('LoginAttempts', lazy=True)

    # Validators
    @validates('address')
    def validate_address(self, key, address):
        assert '@' in address
        return address

    # Overrides
    def __init__(self, address):
        super(Email, self).__init__(address=address)

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.address)


@db.event.listens_for(Email, 'before_insert')
def email_insert(mapper, connection, target):
    target.created = unix_timestamp()
    target.updated = unix_timestamp()


@db.event.listens_for(Email, 'before_update')
def email_update(mapper, connection, target):
    target.updated = unix_timestamp()


class Activation(db.Model):
    """Activate user accounts.
    The (unhashed) code will be sent to the user via email, and visiting the URL within the
    allocated time will activate their account.
    If a new activation code is sent, then delete this record.
    """
    # Columns
    row_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.row_id'), nullable=False)
    code = db.Column(db.CHAR(64), nullable=False, unique=True)

    # Automatic
    created = db.Column(db.Integer, nullable=False)

    # Relationships
    user = db.relationship('User')

    # Validators
    @validates('user')
    def validate_email(self, key, user):
        if not isinstance(user, User):
            user = User(user)
        return user

    @validates('code')
    def validate_code(self, key, code):
        return quick_hash(code)

    # Overrides
    def __init__(self, user, token):
        super(PasswordReset, self).__init__(user=user, code=code)

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.user.email.address)


@db.event.listens_for(Activation, 'before_insert')
def activation_insert(mapper, connection, target):
    target.created = unix_timestamp()


class LoginAttempts(db.Model):
    """Keep track of failed login attempts."""
    # Columns
    row_id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.row_id'), nullable=False)
    success = db.Column(db.Boolean, default=0)

    # Automatic
    created = db.Column(db.Integer, nullable=False)

    # Relationships
    email = db.relationship('Email')

    # Validators
    @validates('email')
    def validate_email(self, key, email):
        if not isinstance(email, Email):
            email = Email(email)
        return email

    # Overrides
    def __init__(self, email, success):
        super(PasswordReset, self).__init__(email=email, success=success)

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.user.email.address)


@db.event.listens_for(LoginAttempts, 'before_insert')
def login_attempt_insert(mapper, connection, target):
    target.created = unix_timestamp()


class PasswordReset(db.Model):
    """Reset user account password.
    Make sure to delete this record as soon as its used.
    """
    # Columns
    row_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.row_id'), nullable=False)
    code = db.Column(db.CHAR(64), nullable=False, unique=True)

    # Automatic
    created = db.Column(db.Integer, nullable=False)

    # Relationships
    user = db.relationship('User')

    # Validators
    @validates('user')
    def validate_email(self, key, user):
        if not isinstance(user, User):
            user = User(user)
        return user

    @validates('code')
    def validate_code(self, key, code):
        return quick_hash(code)

    # Overrides
    def __init__(self, user, token):
        super(PasswordReset, self).__init__(user=user, code=code)

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.user.email.address)

    
@db.event.listens_for(PasswordReset, 'before_insert')
def password_reset_insert(mapper, connection, target):
    target.created = unix_timestamp()


class PersistentLogin(db.Model):
    """Save logins between sessions.
    Information read from https://stackoverflow.com/a/244907/2403000.

    Identifier:
        The same between all login sessions.
        1-64 = random hash, 65-128 = email hash
        When comparing the identifier, only force all the sessions to end if the email is correct.
        Otherwise someone could log everyone out by using the wrong session.
    Token:
        Unique for each session.
        This is just a basic check of whether it exists or not.
        If a match, generate a fresh token and overwrite.
    """
    # Columns
    row_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.row_id'), nullable=False)
    identifier = db.Column(db.CHAR(128), unique=True)
    token = db.Column(db.CHAR(64), unique=True)

    # Automatic
    created = db.Column(db.Integer, nullable=False)
    updated = db.Column(db.Integer, nullable=False)

    # Relationships
    user = db.relationship('User')

    # Other
    @hybrid_property
    def identifier_user(self):
        """Generate the 2nd part of the identifier.
        If anything used here is changed, the user will be logged out.
        """
        return quick_hash(self.user.password + self.user.email.address)

    # Validators
    @validates('user')
    def validate_email(self, key, user):
        if not isinstance(user, User):
            user = User(user)
        return user

    @validates('token')
    def validate_token(self, key, token):
        return quick_hash(token)

    # Overrides
    def __init__(self, user, token):
        super(PersistentLogin, self).__init__(user=user, token=token)
        self.identifier = quick_hash() + self.identifier_user

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.user.email.address)

    # Extra
    @classmethod
    def get_session(cls, user, token, identifier):
        """Use the token and identifier to get the current session.
        Returns the session model and the new token.
        """
        # Find record with matching token
        token = quick_hash(token)
        try:
            session = PersistentLogin.query.filter(PersistentLogin.token==token).one()
        except exc.NoResultFound:
            return None
        
        # Find if identifier is valid
        if session.identifier != identifier:
            if session.identifier[64:128] != session.identifier_user:
                all_sessions = PersistentLogin.query.filter(PersistentLogin.identifier==session.identifier)
                all_sessions.delete()
                db.session.commit()
            return None

        return (session, session.regenerate_token())

    def regenerate_token(self):
        """Generate and set a new token."""
        token = generate_uuid()
        self.token = token
        return token


@db.event.listens_for(PersistentLogin, 'before_insert')
def persistent_login_insert(mapper, connection, target):
    target.created = unix_timestamp()
    target.updated = unix_timestamp()


@db.event.listens_for(PersistentLogin, 'before_update')
def persistent_login_update(mapper, connection, target):
    target.updated = int(time.time())
