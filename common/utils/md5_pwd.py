import hashlib
from flask import current_app

def encrypt(pwd,secret=None):
    if not secret:
        secret = current_app.config['JWT_SECRET']

    sault = hashlib.md5(secret.encode('utf-8'))
    sault.update(pwd.encode('utf-8'))
    ret = sault.hexdigest()
    return ret