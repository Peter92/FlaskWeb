from __future__ import absolute_import

from core.maintainance.database import *


def clean_database(connection):
    remove_old_sessions(connection.sql)
    remove_login_attempts(connection.sql)
