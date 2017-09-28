import hashlib


def quick_hash(x):
    hash = hashlib.sha256()
    hash.update(str(x))
    return hash.hexdigest()


HASH_LENGTH = len(quick_hash(0))
