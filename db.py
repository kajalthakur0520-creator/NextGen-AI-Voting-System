from flask_pymongo import PyMongo
import base64

mongo = PyMongo()

def encrypt_vote(text):
    key = 'super_secret_key_123'
    xored = ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(text, key * (len(text) // len(key) + 1)))
    return base64.b64encode(xored.encode('utf-8')).decode('utf-8')

def decrypt_vote(encoded_text):
    try:
        key = 'super_secret_key_123'
        xored = base64.b64decode(encoded_text.encode('utf-8')).decode('utf-8')
        return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(xored, key * (len(xored) // len(key) + 1)))
    except:
        return encoded_text