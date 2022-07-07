from pony.orm import Database

db = Database()


@db.on_connect(provider="sqlite")
def sqlite_case_sensitivity(db, connection):
    cursor = connection.cursor()
    cursor.execute("PRAGMA case_sensitive_like = OFF")


from .mu_models import *
