from pony.orm import *

from . import db


class Series(db.Entity):
    id = PrimaryKey(int, auto=False)

    bayesian_rating = Optional(float)
    completed = Required(bool)
    description = Required(str)
    forum_id = Required(int)
    last_updated = Required(float)
    latest_chapter = Required(float)
    licensed = Required(bool)
    rating_votes = Required(int)
    status = Optional(str)
    name = Required(str)
    year_start = Optional(int)

    anime = Optional("Anime")
    authors = Set("Author")
    categories = Set("SeriesCategory")
    cat_recs_1 = Set("CategoryRecommendation")
    cat_recs_2 = Set("CategoryRecommendation")
    covers = Optional("Cover")
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


class Author(db.Entity):
    id = PrimaryKey(int, auto=False)

    name = Required(str)

    author_type = Set("AuthorType")
    series = Set(Series)


class AuthorType(db.Entity):
    name = Required(str)

    authors = Required(Author)


class CategoryType(db.Entity):
    name = Required(str)

    series_categories = Set("SeriesCategory")


class CategoryRecommendation(db.Entity):
    weight = Required(int)

    series_1 = Required(Series, reverse="cat_recs_1")
    series_2 = Required(Series, reverse="cat_recs_2")


class Cover(db.Entity):
    original = Required(str)
    height = Required(int)
    thumbnail = Required(str)
    width = Required(int)

    series = Required(Series)


class Genre(db.Entity):
    name = Required(str)

    series = Set(Series)


class Publisher(db.Entity):
    id = PrimaryKey(int, auto=False)

    name = Required(str)

    publications = Set("Publication")
    series = Set("SeriesPublisher")


class PublisherType(db.Entity):
    name = Required(str)

    series = Set("SeriesPublisher")


class RelationType(db.Entity):
    name = Required(str)

    relations = Set("Relation")


class Relation(db.Entity):
    series_1 = Required(Series, reverse="relations_1")
    series_2 = Required(Series, reverse="relations_2")
    relation_type = Required(RelationType)


class Publication(db.Entity):
    name = Required(str)

    publisher = Optional(Publisher)
    series = Required(Series)


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

    series = Required(Series)


class Recommendation(db.Entity):
    weight = Required(int)

    series_1 = Required(Series, reverse="recs_1")
    series_2 = Required(Series, reverse="recs_2")


class Category(db.Entity):
    votes = Required(int)
    votes_minus = Required(int)
    votes_plus = Required(int)

    series = Required(Series)
    type = Required(CategoryType)


class SeriesPublisher(db.Entity):
    notes = Optional(str)

    series = Required(Series)
    publisher = Required(Publisher)
    publisher_type = Required(PublisherType)


class Title(db.Entity):
    name = Required(str)

    series = Required(Series)


class Type(db.Entity):
    name = Required(str)

    series = Set(Series)
