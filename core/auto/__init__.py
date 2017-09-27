from __future__ import absolute_import

from core.auto.session import remove_old_sessions


class Maintainance(object):
    def __init__(self, db_connection):
        self.sql = db_connection
    
    def clear_sessions(self):
        return remove_old_sessions(self.sql)
