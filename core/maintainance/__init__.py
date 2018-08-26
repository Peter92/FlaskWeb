from __future__ import absolute_import

from core.maintainance.database import *


def clean_database(connection):
    print 'Cleaned old sessions: {}'.format(remove_old_sessions(connection.sql))
    print 'Cleaned login attempts: {}'.format(remove_login_attempts(connection.sql))