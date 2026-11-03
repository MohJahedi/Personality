"""The HTTP adapter alone reads cookies and creates cookie response headers."""
from http.cookies import CookieError, SimpleCookie
from ..core.auth_context import AuthContext

COOKIE = 'school_session'


def request_context(environ):
    cookie = SimpleCookie()
    try:
        cookie.load(environ.get('HTTP_COOKIE', ''))
        token = cookie[COOKIE].value if COOKIE in cookie else ''
    except CookieError:
        token = ''
    return AuthContext(token, environ.get('REMOTE_ADDR', 'local'))


def session_header(token, secure=False):
    suffix = '; Secure' if secure else ''
    value = token or ''
    age = 28800 if token else 0
    return ('Set-Cookie', f'{COOKIE}={value}; Path=/; HttpOnly; SameSite=Strict; Max-Age={age}{suffix}')
