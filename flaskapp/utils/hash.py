from __future__ import absolute_import

import hashlib
import base64
import bcrypt
import uuid


def quick_hash(x=None):
    if x is None:
        x = uuid.uuid4().hex
    return hashlib.sha256(str(x)).hexdigest()


def _reduce_long_password(password):
    """This is required for bcrypt to work with longer passwords,
    as bcrypt only works with passwords under 72 characters.
    """
    if len(password) > 72:
        return base64.b64encode(hashlib.sha256(password).digest())
    return password

    
def password_hash(password, rounds=12):
    hash = bcrypt.hashpw(_reduce_long_password(password.encode('utf-8')), bcrypt.gensalt(rounds=rounds))
    if not password_check(password, hash):
        raise TypeError('failed to hash password')
    return hash
    
    
def password_check(password, hash):
    return bcrypt.checkpw(_reduce_long_password(password.encode('utf-8')), hash)
