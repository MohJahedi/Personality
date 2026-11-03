"""Composition root. Module dependencies are assembled here, never by a view."""
from functools import partial
from pathlib import Path
from .http.application import SchoolApplication
from .infrastructure.database import Database
from .modules.identity.service import IdentityService
from .modules.workspace.bootstrap import initialize_workspace
from .modules.identity.permissions import initialize_roles

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def create_application(data_dir, allowed_hosts=None, secure_cookie=False,
                       setup_token=None, seed_demo=False, web_root=None):
    database = Database(data_dir)
    with database.transaction() as db:
        initialize_roles(db)
    identity = IdentityService(database, partial(initialize_workspace, seed_demo=seed_demo), setup_token)
    application = SchoolApplication(database, identity,
        allowed_hosts or ['127.0.0.1:8765', 'localhost:8765'],
        web_root or PROJECT_ROOT / 'web')
    application.legacy_api = seed_demo
    application.secure_cookie = secure_cookie
    return application
