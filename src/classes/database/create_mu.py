import sqlite3


def create_tables(cursor: sqlite3.Cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series (
            id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT,
            description TEXT,
            year_start INTEGER,
            year_end INTEGER,
            bayesian_rating INTEGER,
            rating_votes INTEGER,
            latest_chapter REAL,
            forum_id INTEGER,
            status TEXT,
            licensed BOOLEAN,
            completed BOOLEAN,
            last_updated INTEGER
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS titles (
            series_id INTEGER,
            title TEXT,
            FOREIGN KEY (series_id) REFERENCES series(id),
            UNIQUE (series_id, title)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            series_id INTEGER UNIQUE,
            original TEXT,
            thumb TEXT,
            height INTEGER,
            width INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS types (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_types (
            series_id INTEGER,
            types_id INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id),
            FOREIGN KEY (types_id) REFERENCES types(id),
            UNIQUE (series_id, types_id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_genres (
            series_id INTEGER,
            genres_id INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id),
            FOREIGN KEY (genres_id) REFERENCES genres(id),
            UNIQUE (series_id, genres_id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_categories (
            series_id INTEGER,
            categories_id INTEGER,
            votes INTEGER,
            votes_plus INTEGER,
            votes_minus INTEGER,
            user_id INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id),
            FOREIGN KEY (categories_id) REFERENCES categories(id),
            UNIQUE (series_id, categories_id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS relations_types (
            id INTEGER PRIMARY KEY,
            name TEXT,
            UNIQUE (name)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_relations (
            series_1 INTEGER,
            series_2 INTEGER,
            relations_types_id INTEGER,
            triggered_by_relation_id INTEGER,
            FOREIGN KEY (series_1) REFERENCES series(id),
            FOREIGN KEY (series_2) REFERENCES series(id),
            FOREIGN KEY (relations_types_id) REFERENCES relations_types(id),
            UNIQUE (series_1, series_2, relations_types_id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY,
            name TEXT
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS authors_types (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_authors (
            series_id INTEGER,
            authors_id INTEGER,
            authors_types_id INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id),
            FOREIGN KEY (authors_id) REFERENCES authors(id),
            FOREIGN KEY (authors_types_id) REFERENCES authors_types(id),
            UNIQUE (series_id, authors_id, authors_types_id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS publishers (
            id INTEGER PRIMARY KEY,
            name TEXT
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS publishers_types (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_publishers (
            series_id INTEGER,
            publishers_id INTEGER,
            publishers_types_id INTEGER,
            notes TEXT,
            FOREIGN KEY (series_id) REFERENCES series(id),
            FOREIGN KEY (publishers_id) REFERENCES publishers(id),
            FOREIGN KEY (publishers_types_id) REFERENCES publishers_types(id),
            UNIQUE (series_id, publishers_id, publishers_types_id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_publications (
            series_id INTEGER,
            publishers_id INTEGER,
            name TEXT,
            FOREIGN KEY (series_id) REFERENCES series(id),
            FOREIGN KEY (publishers_id) REFERENCES publishers(id),
            UNIQUE (series_id, publishers_id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_recommendations (
            series_id INTEGER,
            other_series_id INTEGER,
            weight INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id),
            FOREIGN KEY (other_series_id) REFERENCES series(id),
            UNIQUE (series_id, other_series_id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_category_recommendations (
            series_id INTEGER,
            other_series_id INTEGER,
            weight INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id),
            FOREIGN KEY (other_series_id) REFERENCES series(id),
            UNIQUE (series_id, other_series_id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_anime (
            series_id INTEGER,
            start TEXT,
            end TEXT,
            FOREIGN KEY (series_id) REFERENCES series(id),
            UNIQUE (series_id, start, end)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_rank (
            series_id INTEGER PRIMARY KEY,
            position_week INTEGER,
            position_month INTEGER,
            position_three_months INTEGER,
            position_six_months INTEGER,
            position_year INTEGER,
            old_position_week INTEGER,
            old_position_month INTEGER,
            old_position_three_months INTEGER,
            old_position_six_months INTEGER,
            old_position_year INTEGER,
            lists_reading INTEGER,
            lists_wish INTEGER,
            lists_complete INTEGER,
            lists_unfinished INTEGER,
            lists_custom INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id)
        )"""
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS series_meta (
            series_id INTEGER PRIMARY KEY,
            last_fetch INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id)
        )"""
    )
