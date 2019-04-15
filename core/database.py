from __future__ import absolute_import
import pymysql

from core.constants import *
from core.hash import *
from core.tracking import get_url_id
from core.validation import *


class DatabaseConnection(object):

    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.refresh()
        self.command = DatabaseCommands(self)
    
    def refresh(self):
        self.connection = pymysql.connect(host=self.host, db=self.database, user=self.user, password=self.password)
        #self.cursor = self.connection.cursor()
    
    def sql(self, sql, *args):
        """Basic sql commands with their outputs.
        
        Note: Using "cursor" as a variable name will crash the server, see here:
        https://stackoverflow.com/questions/6650940
        """
        cursor = self.connection.cursor()
        try:
            num_records = cursor.execute(sql, args)
            
        #Restart mysql if it's died for whatever reason, seems quite common
        except (pymysql.err.InterfaceError, pymysql.err.OperationalError):
            self.refresh()
            num_records = cursor.execute(sql, args)
            
        self.connection.commit()
        
        try:
            if sql.startswith('SELECT count(*) FROM'):
                return cursor.fetchall()[0][0]
                
            elif sql.startswith('SELECT'):
                return cursor.fetchall()
                
            elif sql.startswith('UPDATE'):
                return num_records
                
            elif sql.startswith('INSERT'):
                return cursor.lastrowid
                
            elif sql.startswith('DELETE'):
                return num_records
        finally:
            cursor.close()
            

class DatabaseCommands(object):
    def __init__(self, connection):
        self.sql = connection.sql
    
    def get_email_id(self, email, insert=True):
        """Get the ID belonging to an email address, insert it into the database if required."""
        try:
            return self.sql('SELECT id FROM emails WHERE email_address = %s', email)[0][0]
        except IndexError:
            if insert:
                return self.sql('INSERT INTO emails (email_address) VALUES (%s)', email)
        return 0
    
    def get_account_id(self, email=None, username=None, email_id=None):
        """Get an account ID by using providing either the email or username."""
        if email_id is not None:
            login_type = 'email_id'
            login_value = email_id
        elif email is not None:
            login_type = 'email_id'
            login_value = self.get_email_id(email)
        elif username is not None:
            login_type = 'username'
            login_value = username
        else:
            return 0
        
        try:
            return self.sql('SELECT id FROM accounts WHERE {} = %s'.format(login_type), login_value)[0][0]
        except IndexError:
            return 0
    
    def insert_account(self, email, password, username=None):
        """Add an account to the database and return the ID."""
        email_id = self.get_email_id(email)
        
        #Check if email or username already exists
        errors = []
        if self.sql('SELECT count(*) FROM accounts WHERE email_id = %s', email_id):
            errors.append('Email address is already in use.')
        if username:
            if self.sql('SELECT count(*) FROM accounts WHERE username = %s', username):
                errors.append('Username is already in use.')
        else:
            username = 'NULL'
        
        #Insert into database
        if not errors:
            sql = 'INSERT INTO accounts (email_id, username, password, permission)'
            sql += ' VALUES (%s, %s, %s, %s)'
            
            if not PRODUCTION_SERVER:
                print 'Account created for "{}"'.format(email)
            
            status = self.sql(sql, email_id, username, password_hash(password), PERMISSION_REGISTERED)
        else:
            status = 0
        return dict(status=status, errors=errors)
    
    def failed_logins_ip(self, ip_id):
        """Check how many login attempts remain for an IP.
        An existing ban doesn't need to be checked as it will not allow access to the site anyway.
        The remaining number of attempts will be returned.
        """
        #Get how many logins
        login_attempts = self.sql('SELECT count(*) FROM login_attempts WHERE success >= 0 AND attempt_time > UNIX_TIMESTAMP(NOW()) - %s AND ip_id = %s', BAN_TIME_IP, ip_id)
        remaining_attempts = MAX_LOGIN_ATTEMPTS_IP - login_attempts
        
        #Ban IP if not enough remaining attempts
        if remaining_attempts <= 0:
            self.ban_ip(ip_id)
        
        if not PRODUCTION_SERVER:
            print 'IP {} attempted to login to an account. Remaining attempts: {}'.format(ip_id, remaining_attempts)
            
        return remaining_attempts
        
    def failed_logins_account(self, account_id, field_data):
        """Check if account is banned or has too many failed login attempts.
        This will work for both existing and non existing accounts.
        The remaining number of attempts with the duration of the current ban will also be returned.
        """
        
        hash = quick_hash(field_data)
        
        #Check if banned
        if account_id:
            try:
                ban_remaining = self.sql('SELECT GREATEST(ban_until, UNIX_TIMESTAMP(NOW())) - UNIX_TIMESTAMP(NOW()) FROM accounts WHERE id = %s', account_id)[0][0]
            except IndexError:
                ban_remaining = 0
        else:
            ban_remaining = 0
        
        #Check login attempts if not banned
        if ban_remaining:
            remaining_attempts = 0
        else:
            try:
                last_login = self.sql('SELECT attempt_time FROM login_attempts WHERE success = 1 AND BINARY field_data = %s ORDER BY attempt_time DESC LIMIT 1', hash)[0][0]
            except IndexError:
                last_login = 0
            
            #Get how many failed logins
            failed_logins = self.sql('SELECT count(*) FROM login_attempts WHERE attempt_time > GREATEST(%s, UNIX_TIMESTAMP(NOW()) - %s) AND BINARY field_data = %s', last_login, BAN_TIME_ACCOUNT, hash)
            remaining_attempts = MAX_LOGIN_ATTEMPTS_ACCOUNT - failed_logins
            
            #Ban account if not enough remaining attempts
            if remaining_attempts <= 0:
                ban_remaining = self.ban_account(account_id)
                
                #Workaround to get psuedo-ban for account that don't exist
                if not account_id:
                    try:
                        ban_offset = self.sql('SELECT UNIX_TIMESTAMP(NOW()) - attempt_time FROM login_attempts WHERE success < 1 AND BINARY field_data = %s ORDER BY attempt_time DESC LIMIT 1 OFFSET {}'.format(-remaining_attempts), hash)[0][0]
                        print ban_offset
                    except IndexError:
                        ban_offset = 0
                    ban_remaining -= ban_offset
        
        if not PRODUCTION_SERVER:
            print 'Account "{}" attempted to login. Remaining attempts: {}. Ban time remaining: {}'.format(field_data, remaining_attempts, ban_remaining)
            
        return remaining_attempts, ban_remaining
        
    def ban_ip(self, ip_id, length=BAN_TIME_IP):
        """Ban an IP and return how long it has been banned for."""
        self.sql('UPDATE ip_addresses SET ban_until = UNIX_TIMESTAMP(NOW()) + %s, ban_count = ban_count + 1 WHERE id = %s', length, ip_id)
        
        if not PRODUCTION_SERVER:
            print 'Banned IP {} for {} seconds'.format(ip_id, length)
            
        return length
    
    def ban_account(self, account_id, length=BAN_TIME_ACCOUNT):
        """Ban an account and return how long it has been banned for.
        If the account is invalid then just return the ban length anyway.
        """
        if account_id:
            self.sql('UPDATE accounts SET ban_until = UNIX_TIMESTAMP(NOW()) + %s, ban_count = ban_count + 1 WHERE id = %s', length, account_id)
        
            if not PRODUCTION_SERVER:
                print 'Banned Account {} for {} seconds'.format(account_id, length)
            
        return length
    
    def login_attempt_record(self, field_data, ip_id, success=0):
        """Save a login attempt to use for rate limiting."""
        hash = quick_hash(field_data)
        attempt_id = self.sql('INSERT INTO login_attempts (field_data, ip_id, success) VALUES (%s, %s, %s)', hash, ip_id, int(success))
        
        if not PRODUCTION_SERVER:
            print 'Recorded login attempt for "{}" with IP {}.'.format(field_data, ip_id)
        
        return attempt_id
        
    def login(self, account_id, password, group_id=None, ip_id=None, form_data=None):
    
        data = {'account': {}, 'warnings': [], 'errors': []}
        
        login_data = self.sql('SELECT password, email_id, username, password_time, register_time, last_activity, credits, permission, activated, ban_until FROM accounts WHERE id = %s', account_id)
        if login_data and password_check(password, login_data[0][0]):
            
            valid = 1
            data['account']['id'] = account_id
            data['account']['email_id'] = login_data[0][1]
            data['account']['username'] = login_data[0][2]
            data['account']['pw_update'] = login_data[0][3]
            data['account']['created'] = login_data[0][4]
            data['account']['last_seen'] = login_data[0][5]
            data['account']['credits'] = login_data[0][6]
            data['account']['permission'] = login_data[0][7]
            data['account']['activated'] = login_data[0][8]
            data['account']['ban_until'] = login_data[0][9]
            
        else:
            valid = 0
            data['errors'].append('Incorrect login details')
        
        #Check for bans
        if ip_id is not None and form_data is not None:
            self.login_attempt_record(form_data, ip_id, success=valid)
            
            remaining_attempts = self.failed_logins_ip(ip_id)
            if remaining_attempts <= 10:
                data['warnings'].append('You have {} more login attempt{} until your IP is temporarily banned.'.format(remaining_attempts, '' if remaining_attempts == 1 else 's'))
            
            remaining_attempts, ban_remaining = self.failed_logins_account(account_id, form_data)
            if ban_remaining > 0:
                data['errors'].append('Your account is disabled for another {} seconds.'.format(ban_remaining))
                valid = -1
            elif remaining_attempts <= 10:
                data['warnings'].append('You have {} more login attempt{} before this account is temporarily disabled.'.format(remaining_attempts, '' if remaining_attempts == 1 else 's'))
            
        if not PRODUCTION_SERVER:
            print 'Account with ID {} {} with login attempt.'.format(account_id, 'failed' if valid < 1 else 'succeeded')
        
        #Update database tables if successful login
        if valid == 1:
            if group_id is not None:
                self.sql('UPDATE visit_groups SET account_id = %s WHERE id = %s', account_id, group_id)
            self.sql('UPDATE accounts SET login_count = login_count + 1 WHERE id = %s', account_id)
        
        data['status'] = valid
        
        return data
        
    def log_status_code(self, status_code, group_id):
        self.sql('INSERT INTO status_codes (visit_group_id, url_id, status_code) VALUES (%s, %s, %s)', group_id, get_url_id(self.sql), status_code)