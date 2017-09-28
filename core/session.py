from __future__ import absolute_import
from flask import session, redirect, url_for, flash, request
from functools import wraps
import cPickle
import uuid
import time

from core.hash import quick_hash
import core.tracking as tracking


SESSION_TIMEOUT = 3600
    

class SessionManager(object):
    def __init__(self, db_connection):
        self.sql = db_connection.sql
                
    def __enter__(self):
        try:
            session_id = session['sid']
            hash = quick_hash(session_id)
            session_data = self.sql('SELECT data_pickle, last_activity FROM temporary_storage WHERE id = %s', hash)
            if session_data and session_data[0][1] > time.time() - SESSION_TIMEOUT:
                self.hash = hash
                self.data = cPickle.loads(session_data[0][0])
                self._new_id = False
                return self
            else:
                raise KeyError
        except KeyError:
            self.new()
            return self
        
    def __getitem__(self, item):
        return self.data[item]
    
    def __setitem__(self, item, value):
        self.data[item] = value
    
    def get(self, item, default):
        return self.data.get(item, default)
    
    def keys(self):
        return self.data.keys()
    
    def values(self):
        return self.data.values()
        
    def pop(self, item):
        return self.data.pop(item)
        
    def iteritems(self):
        return self.data.iteritems()
        
    def items(self):
        return self.data.items()
    
    def new(self):
        self.regenerate()
        self.data = {}
    
    def regenerate(self):
        while True:
            session_id = uuid.uuid4().hex
            hash = quick_hash(session_id)
            if not self.sql('SELECT count(*) FROM temporary_storage WHERE id = %s', hash):
                session['sid'] = session_id
                self.hash = hash
                self._new_id = True
                return session_id
    
    def __exit__(self, *args):
        data = cPickle.dumps(self.data)
        if self._new_id:
            self.sql('INSERT INTO temporary_storage (id, data_pickle, last_activity) VALUES(%s, %s, UNIX_TIMESTAMP(NOW()))', self.hash, data)
        else:
            self.sql('UPDATE temporary_storage SET data_pickle = %s, last_activity = UNIX_TIMESTAMP(NOW()) WHERE id = %s', data, self.hash)
            

def session_start(mysql, require_login=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with SessionManager(mysql) as session:
                if require_login:
                    if not session.get('account_id', 0):
                        session['login_redirect'] = '{}?{}'.format(url_for(func.__name__, *args, **kwargs), request.query_string)
                        return redirect(url_for('login'))
                return func(session=session, *args, **kwargs)
        return wrapper
    return decorator
