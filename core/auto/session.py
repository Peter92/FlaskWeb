from __future__ import absolute_import
import time

from core.session import SESSION_TIMEOUT


def remove_old_sessions(db_connection):
    return db_connection.sql('DELETE FROM temporary_storage WHERE last_activity < {}'.format(time.time() - SESSION_TIMEOUT))
