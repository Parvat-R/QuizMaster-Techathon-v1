import random
import uuid
import hashlib


def generate_uuid():
    return str(uuid.uuid4())

def generate_quiz_id(quiz_handler):
    return str(uuid.uuid4())

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()