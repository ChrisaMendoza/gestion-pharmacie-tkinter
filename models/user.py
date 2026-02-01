import hashlib

class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.role = role
