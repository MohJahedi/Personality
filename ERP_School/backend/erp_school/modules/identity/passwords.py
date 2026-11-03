"""modules / identity / passwords.py: extracted from the real v0.3 pilot."""
from __future__ import annotations
import hashlib
import hmac
import secrets
import re
from ...core.errors import AppError
ITERATIONS = 600_000

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def password_hash(password):
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${hashed.hex()}'

def password_matches(password, encoded):
    try:
        algo, count, salt, expected = encoded.split('$')
        if algo != 'pbkdf2_sha256' or not 600000 <= int(count) <= 2000000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), int(count))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False

def credentials(payload):
    username = str(payload.get('username', '')).strip().lower()
    password = payload.get('password', '')
    if not re.fullmatch('[a-z][a-z0-9_.-]{2,39}', username):
        raise AppError('نام کاربری باید ۳ تا ۴۰ حرف انگلیسی، عدد، نقطه یا زیرخط باشد و با حرف شروع شود.')
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        raise AppError('گذرواژه باید بین ۱۲ تا ۱۲۸ نویسه باشد.')
    return (username, password)
