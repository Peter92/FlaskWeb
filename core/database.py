from __future__ import absolute_import
import pymysql

from core.constants import *
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
        if self.sql('SELECT count(*) FROM accounts WHERE email_id = %s', email_id):
            return False
        sql = 'INSERT INTO accounts (email_id, username, password, password_changed, register_time, last_activity, permission)'
        sql += ' VALUES (%s, %s, %s, UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()), UNIX_TIMESTAMP(NOW()), %s)'
        return self.sql(sql, email_id, username, password_hash(password), PERMISSION_REGISTERED)
    
    def failed_logins_ip(self, ip_id, reset_on_success=False):
        
        #Get the time of the last successful login
        if reset_on_success:
            last_login = self.sql('SELECT attempt_time FROM login_attempts WHERE success = 1 AND ip_id = %s', ip_id)
            try:
                last_login = last_login[0][0]
            except IndexError:
                last_login = 0
        else:
            last_login = 0
        
        #Get how many failed logins
        ip_failed_logins = self.sql('SELECT count(*) FROM login_attempts WHERE attempt_time > GREATEST(%s, UNIX_TIMESTAMP(NOW()) - %s) AND ip_id = %s', last_login, BAN_TIME_IP, ip_id)
        remaining_attempts = MAX_LOGIN_ATTEMPTS_IP - ip_failed_logins
        
        #Ban IP if not enough remaining attempts
        if remaining_attempts <= 0:
            self.ban_ip(ip_id)
            
        return remaining_attempts
        
    def ban_ip(self, ip_id, length=BAN_TIME_IP):
        return self.sql('UPDATE ip_addresses SET ban_until = UNIX_TIMESTAMP(NOW()) + %s, ban_count = ban_count + 1 WHERE id = %s', BAN_TIME_IP, ip_id)
    
    def login(self, email, username, password, session, ip_id):
    
        fail = False
        account_id = None
        
        #Detect if username or email has been input
        if email is not None:
            login_type = 'email_id'
            login_value = self._get_email_id(email)
        elif username is not None:
            login_type = 'username'
            login_value = username
        else:
            raise ValueError('need email or username to log in')
        
        login_data = self.sql('SELECT password, id, email_id, username, password_changed, register_time, last_activity, credits, permission, activated, ban_until FROM accounts WHERE {} = %s'.format(login_type), login_value)
        if login_data and password_check(password, login_data[0][0]):
            
            s = session['account_data']
            account_id = login_data[0][1]
            s['id'] = account_id
            s['email_id'] = login_data[0][2]
            s['username'] = login_data[0][3]
            s['pw_update'] = login_data[0][3]
            s['created'] = login_data[0][4]
            s['last_seen'] = login_data[0][5]
            s['credits'] = login_data[0][6]
            s['permission'] = login_data[0][7]
            s['activated'] = login_data[0][8]
            s['ban_until'] = login_data[0][9]
            
            if s['ban_until']:
                print 'Banned for {} seconds'.format(ban_remaining)
            
        else:
            fail = True
            ban_remaining = 0
            account_id = 0
            
        self.sql('INSERT INTO login_attempts (ip_id, account_id, attempt_time, success) VALUES (%s, %s, UNIX_TIMESTAMP(NOW()), %s)', ip_id, account_id, not fail)
        
        return not fail
