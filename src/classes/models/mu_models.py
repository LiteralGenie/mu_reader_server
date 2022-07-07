from typing import Union
from pony.orm import *

from . import db


class Series(db.Entity):
    id: int = PrimaryKey(int, auto=False, size=64)

    bayesian_rating: float | None = Optional(float)
    completed: bool = Required(bool)
    description: str = Optional(str)
    forum_id: int = Required(int, size=64)
    last_updated: float = Required(float)
    latest_chapter: float = Required(float)
    licensed: bool = Required(bool)
    name: str = Required(str)
    rating_votes: int = Required(int)
    status: str = Optional(str)
    year: int | None = Optional(int)

    anime: Union["Anime", None] = Optional("Anime")
    authors = Set("SeriesAuthor")
    categories = Set("Category")
    cat_recs = Set("CategoryRecommendation")
    cat_recs_for = Set("CategoryRecommendation")
    cover = Optional("Cover")
    genres = Set("Genre")
    publications = Set("Publication")
    publishers = Set("SeriesPublisher")
    rank = Optional("Rank")
    recs_1 = Set("Recommendation")
    recs_2 = Set("Recommendation")
    relations_1 = Set("Relation")
    relations_2 = Set("Relation")
    titles = Set("Title")
    type = Required("Type")


class Anime(db.Entity):
    start = Required(str)
    end = Optional(str)

    series = Required(Series)

    composite_key(start, end, series)


class Author(db.Entity):
    id = PrimaryKey(int, auto=False, size=64)

    name = Required(str)

    series = Set("SeriesAuthor")


class AuthorType(db.Entity):
    name = PrimaryKey(str)

    authors = Set("SeriesAuthor")


class Category(db.Entity):
    votes = Required(int)
    votes_minus = Required(int)
    votes_plus = Required(int)

    series = Required(Series)
    type = Required("CategoryType")

    composite_key(series, type)


class CategoryType(db.Entity):
    name = PrimaryKey(str)

    series_categories = Set(Category)


class CategoryRecommendation(db.Entity):
    weight = Required(int)

    base_series = Required(Series, reverse="cat_recs")
    recommendation = Required(Series, reverse="cat_recs_for")

    composite_key(base_series, recommendation)


class Cover(db.Entity):
    height = Required(int)
    original = Required(str)
    thumbnail = Required(str)
    width = Required(int)

    series = PrimaryKey(Series)


class Genre(db.Entity):
    name = PrimaryKey(str)

    series = Set(Series)


class Publication(db.Entity):
    name = Required(str)

    publisher = Optional("Publisher")
    series = Required(Series)

    composite_key(name, publisher, series)


class Publisher(db.Entity):
    id = PrimaryKey(int, auto=False, size=64)

    name = Required(str)

    publications = Set(Publication)
    series = Set("SeriesPublisher")


class PublisherType(db.Entity):
    name = Required(str)

    series = Set("SeriesPublisher")


class Rank(db.Entity):
    lists_custom = Optional(int)
    lists_reading = Optional(int)
    lists_unfinished = Optional(int)
    lists_wish = Optional(int)
    old_position_week = Optional(int)
    old_position_month = Optional(int)
    old_position_three_months = Optional(int)
    old_position_six_months = Optional(int)
    old_position_year = Optional(int)
    position_week = Optional(int)
    position_month = Optional(int)
    position_three_months = Optional(int)
    position_six_months = Optional(int)
    position_year = Optional(int)

    series = PrimaryKey(Series)


class Recommendation(db.Entity):
    weight = Required(int)

    series_1 = Required(Series, reverse="recs_1")
    series_2 = Required(Series, reverse="recs_2")

    composite_key(series_1, series_2)


class Relation(db.Entity):
    series_1 = Required(Series, reverse="relations_1")
    series_2 = Required(Series, reverse="relations_2")
    relation_type = Required("RelationType")

    composite_key(series_1, series_2, relation_type)


class RelationType(db.Entity):
    name = PrimaryKey(str)

    relations = Set(Relation)


class SeriesAuthor(db.Entity):
    type = Required(AuthorType)
    name = Required(str)

    author = Optional(Author)
    series = Required(Series)

    composite_key(type, name, author, series)


class SeriesPublisher(db.Entity):
    notes = Optional(str)

    series = Required(Series)
    publisher = Required(Publisher)
    publisher_type = Required(PublisherType)

    composite_key(series, publisher, publisher_type)


class Title(db.Entity):
    name = Required(str)

    series = Required(Series)

    composite_key(name, series)


class Type(db.Entity):
    name = PrimaryKey(str)

    series = Set(Series)
