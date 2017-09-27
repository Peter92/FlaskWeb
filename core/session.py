from flask import session
import cPickle
import hashlib
import uuid
import time


SESSION_TIMEOUT = 3600


def quick_hash(x):
    hash = hashlib.sha1()
    hash.update(str(x))
    return hash.hexdigest()
    
    
class SessionManager(object):
    def __init__(self, db_connection):
        self.sql = db_connection.sql
                
    def __enter__(self):
        try:
            session_id = session['sid']
            hash = quick_hash(session_id)
            session_data = self.sql('SELECT data_pickle, last_activity FROM temporary_storage WHERE id = %s', hash)
            if session_data and session_data[0][1] > time.time() - SESSION_TIMEOUT:
                session['sid'] = session_id
                self.hash = hash
                self.data = cPickle.loads(session_data[0][0])
                self.new_id = False
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
                self.new_id = True
                return session_id
    
    def __exit__(self, *args):
        data = cPickle.dumps(self.data)
        if self.new_id:
            self.sql('INSERT INTO temporary_storage (id, data_pickle, last_activity) VALUES(%s, %s, UNIX_TIMESTAMP(NOW()))', self.hash, data)
        else:
            self.sql('UPDATE temporary_storage SET data_pickle = %s, last_activity = UNIX_TIMESTAMP(NOW()) WHERE id = %s', data, self.hash)
