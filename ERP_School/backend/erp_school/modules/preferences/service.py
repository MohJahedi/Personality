"""Appearance preferences belong to each authenticated account."""
import re
from ...core.errors import AppError

FONTS = ('vazirmatn', 'estedad', 'shabnam', 'sahel', 'samim')
SIZES = ('small', 'normal', 'large')
THEMES = ('sky', 'emerald', 'violet', 'amber', 'rose')
DEFAULT = {'font': 'vazirmatn', 'size': 'normal', 'theme': 'sky', 'accent': ''}


def read(db, user):
    row = db.execute('SELECT font,size,theme,accent FROM user_preferences WHERE user_id=?', (user['id'],)).fetchone()
    return dict(row) if row else dict(DEFAULT)


def save(db, user, payload):
    if payload.get('font') not in FONTS or payload.get('size') not in SIZES or payload.get('theme') not in THEMES:
        raise AppError('فونت، اندازه یا تم معتبر نیست.')
    accent = payload.get('accent', '')
    if not isinstance(accent, str) or (accent and not re.fullmatch(r'#[0-9a-fA-F]{6}', accent)):
        raise AppError('رنگ انتخابی معتبر نیست.')
    db.execute('INSERT INTO user_preferences VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET font=excluded.font,size=excluded.size,theme=excluded.theme,accent=excluded.accent', (user['id'], payload['font'], payload['size'], payload['theme'], accent.lower()))
    return {'ok': True}
