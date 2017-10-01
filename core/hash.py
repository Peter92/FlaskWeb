from __future__ import absolute_import
import hashlib
import base64
import bcrypt


BCRYPT_MAX_LENGTH = 72


def quick_hash(x):
    hash = hashlib.sha256()
    hash.update(str(x))
    return hash.hexdigest()


def _reduce_long_password(password):
    """This is required for bcrypt to work with longer passwords."""
    if len(password) > BCRYPT_MAX_LENGTH:
        return base64.b64encode(hashlib.sha256(password).digest())
    return password

    
def password_hash(password, rounds=12):
    hash = bcrypt.hashpw(_reduce_long_password(password.encode('utf-8')), bcrypt.gensalt(rounds=rounds))
    if not password_check(password, hash):
        raise TypeError('failed to hash password')
    
    
def password_check(password, hash):
    return bcrypt.checkpw(_reduce_long_password(password.encode('utf-8')), hash)
