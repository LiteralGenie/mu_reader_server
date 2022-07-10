from config import paths
from pony.orm import Database

# init db
db = Database()

# make db queries case insensitive
@db.on_connect(provider="sqlite")
def sqlite_case_sensitivity(db: Database, connection):
    cursor = connection.cursor()
    cursor.execute("PRAGMA case_sensitive_like = OFF")


# define table models
from .mu_models import *
from .storage_models import *
from .misc_models import *

# load db
db.bind(provider="sqlite", filename=str(paths.DB_FILE), create_db=True)
db.generate_mapping(create_tables=True)

# reset locks
with db_session:
    upsert(Locks, dict(name="series_scan"), dict(locked=False))
