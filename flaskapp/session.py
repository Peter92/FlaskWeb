"""Create a session in the database.
This is needed for security as Flask stores all the session data in cookies otherwise.
"""

import os
import pickle
import time
from flask import session

from .common import *
from .constants import *
from .database import *
from .utils.hash import quick_hash


class SessionManager(object):
    def __init__(self):
        self.id = session['sid']
        self.hash = quick_hash(self.id).hex()
        self.path = os.path.join(SESSION_DIR, self.hash)

    def __enter__(self):
        last_activity = os.path.getmtime(self.path)
        if last_activity < time.time() - SESSION_TIMEOUT:
            self.start()

        else:
            with open(self.path, 'rb') as f:
                self.data = pickle.loads(f.read())

        return self

    def __exit__(self, *args):
        self.save()

    def start(self):
        """Start a new session."""
        self.regenerate()
        if 'csrf_token' not in self.data:
            self.data['csrf_token'] = uuid.uuid4().hex
            self.data['csrf_form'] = uuid.uuid4().hex


        #Session(user=user, ip=ip, user_agent=user_agent, referrer=referrer, language=language)
        self.group_id = 1
        # RECORD THE FIRST PAGE VISIT

    def regenerate(self):
        """Regenerate the session with a new random ID."""
        for i in range(MAX_SESSION_ATTEMPTS):
            self.id = uuid.uuid4().hex
            self.hash = quick_hash(self.id).hex()
            self.path = os.path.join(SESSION_DIR, self.hash)
            
            if not os.path.exists(self.path):
                old_id = session.get('sid')
                if old_id is not None:
                    old_path = os.path.join(SESSION_DIR, old_id)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                session['sid'] = self.id
                break
        raise RuntimeError('unable to find empty session string')

    def save(self):
        # if last id == url id, then increment refresh
        #Visit(session=session, url=url)

        # RECORD A NEW PAGE VISIT HERE
        with open(self.path, 'wb') as f:
            f.write(pickle.dumps(data))
