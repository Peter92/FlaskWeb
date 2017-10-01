from __future__ import absolute_import
import pymysql

from core.exceptions import *
from core.hash import password_hash, password_check, _reduce_long_password


class DatabaseConnection(object):

    def __init__(self, host, database, user, password):
        
        #Not in use (but not sure if needed) - port: 3306, charset: utf8, use_unicode: True
        self.connection = pymysql.connect(host=host, db=database, user=user, password=password)
        self.cursor = self.connection.cursor()
        self.command = DatabaseCommands(self)
        
    def sql(self, sql, *args):
        num_records = self.cursor.execute(sql, args)
        self.connection.commit()
        
        if sql.startswith('SELECT count(*) FROM'):
            return self.cursor.fetchall()[0][0]
            
        elif sql.startswith('SELECT'):
            return self.cursor.fetchall()
            
        elif sql.startswith('UPDATE'):
            return num_records
            
        elif sql.startswith('INSERT'):
            return self.cursor.lastrowid
            
        elif sql.startswith('DELETE'):
            return num_records
            

class DatabaseCommands(object):
    def __init__(self, connection):
        self.sql = connection.sql
    
    def _get_email_id(self, email):
        id = self.sql('SELECT id FROM emails WHERE email_address = %s', email)
        if id:
            return id[0][0]
        else:
            return self.sql('INSERT INTO emails (email_address, time_added) VALUES (%s, UNIX_TIMESTAMP(NOW()))', email)
        
    def insert_account(self, email, password, username='NULL'):
        email_id = self._get_email_id(email)
        hash = password_hash(password)
        if self.sql('SELECT count(*) FROM accounts WHERE email_id = %s', email_id):
            return False
        sql = 'INSERT INTO accounts (email_id, username, password, password_changed, register_time, last_activity)'
        sql += ' VALUES (%s, %s, %s, UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()))'
        return self.sql(sql, email_id, username, hash)
