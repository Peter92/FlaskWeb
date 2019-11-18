import time
import uuid
from flask import jsonify
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import exc, validates

from ..connect import db
from ..constants import UserPermission
from ...common import generate_uuid, unix_timestamp


class Session(db.Model):
    """User accounts."""
    __tablename__ = 'Session'
    row_id = db.Column(db.Integer, primary_key=True)
    ip_id = db.Column(db.Integer, db.ForeignKey('IP.row_id'), nullable=False)
    ua_id = db.Column(db.Integer, db.ForeignKey('UserAgent.row_id'), nullable=False)
    referrer_id = db.Column(db.Integer, db.ForeignKey('Referrer.row_id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('Language.row_id'), nullable=False)

    ip = db.relationship('IP')
    user_agent = db.relationship('UserAgent')
    referrer = db.relationship('Referrer')
    language = db.relationship('Language')


class Visit(db.Model):
    """User accounts."""
    __tablename__ = 'Visit'
    row_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, nullable=False)
    url_id = db.Column(db.Integer, nullable=False)

    visited = db.Column(db.Integer, nullable=False)


class IP(db.Model):
    __tablename__ = 'IP'
    row_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(45), nullable=False, unique=True)

    created = db.Column(db.Integer, nullable=False)
    visited = db.Column(db.Integer, nullable=False)


class UserAgent(db.Model):
    __tablename__ = 'UserAgent'
    row_id = db.Column(db.Integer, primary_key=True)
    agent = db.Column(db.String(256), nullable=False, unique=True)

    created = db.Column(db.Integer, nullable=False)
    visited = db.Column(db.Integer, nullable=False)


class Referrer(db.Model):
    __tablename__ = 'Referrer'
    row_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

    created = db.Column(db.Integer, nullable=False)
    visited = db.Column(db.Integer, nullable=False)


class Language(db.Model):
    __tablename__ = 'Language'
    row_id = db.Column(db.Integer, primary_key=True)
    locale = db.Column(db.String(8), nullable=False, unique=True)

    created = db.Column(db.Integer, nullable=False)
    visited = db.Column(db.Integer, nullable=False)
