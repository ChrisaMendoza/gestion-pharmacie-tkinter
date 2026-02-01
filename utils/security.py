import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def has_permission(user_role, required_roles):
    return user_role in required_roles
