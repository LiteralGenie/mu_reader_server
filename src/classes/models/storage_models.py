from pony.orm import *
from . import db


class BookFile(db.Entity):
    name = PrimaryKey(str)

    path = Required(str)

    series = Required("SeriesFolder")


class SeriesFolder(db.Entity):
    name = PrimaryKey(str)

    path = Required(str)

    books = Set(BookFile)
    series = Optional("Series")
    series_score = Optional(float)
