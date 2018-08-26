from __future__ import absolute_import

from core.constants import BAN_TIME_IP, BAN_TIME_ACCOUNT
from core.session import SESSION_TIMEOUT


MIN_TIMEOUT = 7200

def remove_old_sessions(sql_execute):
    return sql_execute('DELETE FROM temporary_storage WHERE last_activity < UNIX_TIMESTAMP(NOW()) - {}'.format(max(MIN_TIMEOUT, SESSION_TIMEOUT)))
    
    
def remove_login_attempts(sql_execute):
    return sql_execute('DELETE FROM login_attempts WHERE attempt_time < UNIX_TIMESTAMP(NOW()) - {}'.format(max(MIN_TIMEOUT, BAN_TIME_IP, BAN_TIME_ACCOUNT)))