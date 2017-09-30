from __future__ import absolute_import
from flask import session
import cPickle
import uuid
import time
import zlib

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
            data_pickle, compressed, last_activity = self.sql('SELECT data_pickle, compressed, last_activity FROM temporary_storage WHERE id = %s', hash)[0]
            
            if last_activity > time.time() - SESSION_TIMEOUT:
                if compressed:
                    data_pickle = zlib.decompress(data_pickle)
                self.data = cPickle.loads(data_pickle)
                self.hash = hash
                self._new_id = False
                return self
            
        except IndexError:
            pass
            
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
        self._track_start()
    
    def _track_continue(self):
        """Record a new page visit."""
        url_id = tracking.get_url_id(self.sql)
        last_id = self.data.get('url_id', 0)
        group_id = self.data['group_id']
        
        if url_id == last_id:
            sql = 'UPDATE visit_pages SET refresh_count = refresh_count + 1 WHERE id = %s'
            self.sql(sql, self.data['visit_id'])
        else:
            sql = 'INSERT INTO visit_pages (group_id, url_id, visit_time) VALUES (%s, %s, UNIX_TIMESTAMP(NOW()))'
            id = self.sql(sql, group_id, url_id)
            self.data['visit_id'] = id
        
        sql = 'UPDATE visit_groups SET last_activity = UNIX_TIMESTAMP(NOW()), pages_unique = pages_unique + {}, pages_total = pages_total + 1 WHERE id = %s'
        self.sql(sql.format(int(url_id != last_id)), group_id)
        self.data['url_id'] = url_id
    
    def _track_start(self):
        """Start a tracking session."""
        ip_id = tracking.get_ip_id(self.sql)
        ua_id = tracking.get_ua_id(self.sql)
        language_id = tracking.get_language_id(self.sql)
        referrer_id = tracking.get_referrer_id(self.sql)
        account_id = self.data.get('account_id', 0)
        
        sql = ('INSERT INTO visit_groups'
               ' (account_id, ip_id, user_agent_id, referrer_id, language_id, time_started, last_activity)'
               ' VALUES (%s, %s, %s, %s, %s, UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()))')
        group_id = self.sql(sql, account_id, ip_id, ua_id, referrer_id, language_id)
        self.data['group_id'] = group_id

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
        self._track_continue()
        data = cPickle.dumps(self.data)
        data_len = len(data)
        compressed = False
        
        #Compress if too large for blob
        if data_len > 65535:
            data = zlib.compress(data)
            compressed = True
            
        if self._new_id:
            self.sql('INSERT INTO temporary_storage (id, data_pickle, data_len, compressed, last_activity) VALUES(%s, %s, %s, %s, UNIX_TIMESTAMP(NOW()))', self.hash, data, data_len, int(compressed))
        else:
            self.sql('UPDATE temporary_storage SET data_pickle = %s, data_len = %s, compressed = %s, last_activity = UNIX_TIMESTAMP(NOW()) WHERE id = %s', data, data_len, int(compressed), self.hash)
