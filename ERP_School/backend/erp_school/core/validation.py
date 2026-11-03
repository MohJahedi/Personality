"""Small shared input validators; business rules remain in their modules."""
import re

from .errors import AppError


def ids(value, maximum=500):
    if not isinstance(value, list) or len(value) > maximum:
        raise AppError('فهرست انتخاب‌ها معتبر نیست.')
    if any(not isinstance(item, str) or not item or len(item) > 180 for item in value):
        raise AppError('شناسهٔ انتخاب‌شده معتبر نیست.')
    return list(dict.fromkeys(value))


def integer(value, minimum, maximum, title):
    if type(value) is not int or not minimum <= value <= maximum:
        raise AppError(f'{title} باید عدد صحیح بین {minimum} و {maximum} باشد.')
    return value


def optional_text(payload, key, maximum=100):
    value = payload.get(key, '')
    if not isinstance(value, str) or len(value.strip()) > maximum:
        raise AppError('متن ورودی معتبر نیست.')
    return value.strip()


def clock(value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', value):
        raise AppError('زمان باید با قالب ساعت و دقیقه باشد.')
    return value
