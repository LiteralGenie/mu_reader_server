from pony.orm import *

from utils.misc import upsert
from . import db


class Locks(db.Entity):
    name = PrimaryKey(str)

    data = Optional(Json)
    locked = Required(bool)
