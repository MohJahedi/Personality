"""core / values.py: extracted from the real v0.3 pilot."""
from __future__ import annotations
from datetime import date, datetime, timezone
import re
import secrets
from .errors import AppError

def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def uid():
    return secrets.token_hex(16)

def text(payload, key, title, maximum=100):
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise AppError(f'{title} معتبر نیست.')
    return value.strip()

def money(value):
    table = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
    value = re.sub('[,٬\\s]', '', str(value).translate(table))
    if not re.fullmatch('[0-9]+', value) or len(value) > 10 or (not 1 <= int(value) <= 1000000000):
        raise AppError('مبلغ را به تومان، بدون اعشار و بین ۱ تا یک میلیارد وارد کنید.')
    return int(value) * 10

def day(value):
    try:
        value = str(value)
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError()
        return value
    except ValueError:
        raise AppError('تاریخ معتبر نیست.')
