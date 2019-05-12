from __future__ import absolute_import

import time
import uuid


def unix_timestamp():
    return int(time.time())
    

def generate_uuid():
    return uuid.uuid4().hex
