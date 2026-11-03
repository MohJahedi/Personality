"""Hosting entry point. No implicit domain, demo data, or first-admin exposure."""
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'backend'))
from erp_school.bootstrap import create_application

hosts = [host.strip() for host in os.environ.get('SCHOOL_ALLOWED_HOSTS', '').split(',') if host.strip()]
if not hosts or '*' in hosts:
    raise RuntimeError('Set SCHOOL_ALLOWED_HOSTS to the exact intended domain.')
app = create_application(os.environ.get('SCHOOL_DATA_DIR', 'data'), hosts,
    os.environ.get('SCHOOL_SECURE_COOKIES', '1') == '1',
    os.environ.get('SCHOOL_SETUP_TOKEN'))
with app.connection() as db:
    if not db.execute('SELECT id FROM local_users LIMIT 1').fetchone() and not app.setup_digest:
        raise RuntimeError('Set a random SCHOOL_SETUP_TOKEN before first startup.')
