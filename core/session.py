from __future__ import absolute_import
from flask import session, abort
import cPickle
import uuid
import time
import zlib
import time

from core.constants import *
from core.hash import quick_hash
import core.tracking as tracking


SESSION_TIMEOUT = 3600


class SessionManager(object):
    
    MAX_LENGTH = 65535

    def __init__(self, db_connection):
        self.sql = db_connection.sql
        self.skip = False
                
    def __enter__(self):
        self._session_start()
        self._check_ban_ip()
        return self
        
    def __getitem__(self, item):
        return self.data[item]
    
    def __setitem__(self, item, value):
        self.data[item] = value
        
    def __delitem__(self, item):
        del self.data[item]
    
    def _session_start(self):
        """Load session data from database if possible."""
        try:
            session_id = session['sid']
            hash = quick_hash(session_id)
            data_pickle, compressed, last_activity = self.sql('SELECT data_pickle, compressed, last_activity FROM temporary_storage WHERE BINARY id = %s', hash)[0]
            
            if last_activity > time.time() - SESSION_TIMEOUT:
                if compressed:
                    data_pickle = zlib.decompress(data_pickle)
                self.data = cPickle.loads(data_pickle)
                self.hash = hash
                self._new_id = False
                return
                
        except (IndexError, KeyError):
            pass
            
        self.new()
    
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
    
    def exit(self):
        """Stop the tracking code from running.
        Meant to be used for redirects.
        """
        self.skip = True
    
    def generate_csrf_token(self, override=False):
        if override or 'csrf_token' not in self.data:
            self.data['csrf_token'] = uuid.uuid4().hex
            self.data['csrf_form'] = uuid.uuid4().hex
    
    def _check_ban_ip(self):
        """Don't allow IP to access site while banned."""
        banned_until = self.sql('SELECT ban_until FROM ip_addresses WHERE id = %s', self.data['ip_id'])[0][0]
        
        if banned_until > time.time():
            if not PRODUCTION_SERVER:
                print 'IP {} tried to visit but is banned.'.format(self.data['ip_id'])
            abort(408)
    
    def new(self):
        self.regenerate()
        self.data = {'account_data': {}}
        self._get_user_data()
        self._track_start()
        self.generate_csrf_token()
    
    def _get_user_data(self):
        self.data['ip_id'] = tracking.get_ip_id(self.sql)
        self.data['ua_id'] = tracking.get_ua_id(self.sql)
        self.data['language_id'] = tracking.get_language_id(self.sql)
        self.data['referrer_id'] = tracking.get_referrer_id(self.sql)
    
    def _track_continue(self):
        """Record a new page visit."""
        if self.skip:
            return
        
        group_id = self.data['group_id']
        url_id = tracking.get_url_id(self.sql)
        last_id = self.data.get('url_id', 0)
        
        if url_id == last_id:
            sql = 'UPDATE visit_pages SET refresh_count = refresh_count + 1 WHERE id = %s'
            self.sql(sql, self.data['visit_id'])
        else:
            sql = 'INSERT INTO visit_pages (group_id, url_id) VALUES (%s, %s)'
            id = self.sql(sql, group_id, url_id)
            self.data['visit_id'] = id
        
        self.data['url_id'] = url_id
    
    def _track_start(self):
        """Start a tracking session."""
        account_id = self.data.get('account_id', 0)
        
        sql = ('INSERT INTO visit_groups'
               ' (account_id, ip_id, user_agent_id, referrer_id, language_id)'
               ' VALUES (%s, %s, %s, %s, %s)')
        group_id = self.sql(sql, account_id, self.data['ip_id'], self.data['ua_id'], self.data['referrer_id'], self.data['language_id'])
        self.data['group_id'] = group_id

    def update_account_id(self):
        """Update the visit group table with the account ID (if set)."""
        try:
            account_id = self.data['account_data'][id]
            group_id = self.data['group_id']
        except (KeyError, AttributeError):
            return False
        if not account_id:
            return False
        return self.sql('UPDATE visit_groups SET account_id = %s WHERE id = %s', account_id, group_id)
       
    def regenerate(self):
        """Regenerate the session with a new random ID."""
        self.update_account_id()
        while True:
            session_id = uuid.uuid4().hex
            hash = quick_hash(session_id)
            if not self.sql('SELECT count(*) FROM temporary_storage WHERE id = %s', hash):
                old_id = session.get('sid', None)
                if old_id is not None:
                    self.sql('DELETE FROM temporary_storage WHERE id = %s', old_id)
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
        if data_len > self.MAX_LENGTH:
            data = zlib.compress(data)
            if len(data) > self.MAX_LENGTH:
                return self.new()
            compressed = True
            
        if self._new_id:
            self.sql('INSERT INTO temporary_storage (id, data_pickle, data_len, compressed) VALUES(%s, %s, %s, %s)', self.hash, data, data_len, int(compressed))
        else:
            self.sql('UPDATE temporary_storage SET data_pickle = %s, data_len = %s, compressed = %s WHERE id = %s', data, data_len, int(compressed), self.hash)
