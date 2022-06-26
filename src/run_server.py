import logging
import sqlite3
import time

import requests
import urlpath
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from config import paths
from utils.logging import configure_logging

configure_logging()
app = FastAPI()

def get_db():
    db = sqlite3.connect(paths.DB_FILE)
    cursor = db.cursor()
    try:
        yield cursor
    finally:
        db.commit()
        db.close()

@app.get('/series/ids')
def get_ids(
    offset: int = 0,
    limit: int = 100
):
    with sqlite3.connect(paths.DB_FILE) as db:
        result = db.execute("""
            SELECT id FROM series
            ORDER BY bayesian_rating DESC
            LIMIT ?
            OFFSET ?
        """, (limit, offset))
        result = result.fetchall()
        result = [r[0] for r in result]

        return result

@app.get('/series/ids/{id}')
def get_series(
    id: int
):
    with sqlite3.connect(paths.DB_FILE) as db:
        resp = dict()

        # basic info
        result = db.execute("""
            SELECT
                series.id,
                series.title,
                series.description,
                series.year_start,
                series.bayesian_rating,
                series.licensed,
                series.completed,
                types.name as type
            FROM series
            INNER JOIN series_types ON series_types.series_id = series.id
            INNER JOIN types ON types.id = series_types.types_id
            WHERE series.id = ?
        """, (id,))
        keys = [x[0] for x in result.description]
        data = result.fetchone()
        resp.update({ k:v for k,v in zip(keys, data) })

        # authors
        result = db.execute("""
            SELECT authors.name, authors.id FROM authors
            INNER JOIN series_authors ON series_authors.authors_id = authors.id
            WHERE series_authors.series_id = ?
        """, (id,))
        keys = [x[0] for x in result.description]
        data = result.fetchall()
        resp['authors'] = [
            { k:v for k,v in zip(keys, d) }
            for d in data
        ]

        # genres
        result = db.execute("""
            SELECT genres.name FROM genres
            INNER JOIN series_genres ON series_genres.genres_id = genres.id
            WHERE series_genres.series_id = ?
        """, (id,))
        data = [r[0] for r in result.fetchall()]
        resp['genres'] = data

        # categories
        result = db.execute("""
            SELECT categories.name FROM categories
            INNER JOIN series_categories ON series_categories.categories_id = categories.id
            WHERE series_categories.series_id = ?
        """, (id,))
        data = [r[0] for r in result.fetchall()]
        resp['categories'] = data

        # title
        result = db.execute("""
            SELECT title FROM titles
            WHERE series_id = ?
        """, (id,))
        data = [r[0] for r in result.fetchall()]
        resp['titles'] = data

        # typing
        resp['licensed'] = bool(resp['licensed'])
        resp['completed'] = bool(resp['completed'])

        return resp

@app.get('/series/images/{id}')
def get_image(
    id: int
):
    with sqlite3.connect(paths.DB_FILE) as db:
        result = db.execute("""
            SELECT original FROM images
            WHERE series_id = ?
        """, (id,))
        result = result.fetchone()

        if result is None:
            raise HTTPException(404)
        
        url = urlpath.URL(result[0])
        file = paths.COVER_DIR / url.parts[-1]
        if not file.exists():
            with open(file, 'wb') as f:
                logging.info(f'fetching image [{url}]')
                content = requests.get(url).content
                f.write(content)
            
        return FileResponse(file)

@app.get('/series/genres')
def get_genres():
    with sqlite3.connect(paths.DB_FILE) as db:
        result = db.execute("""
            SELECT series_genres.genres_id as id, genres.name as name, COUNT(*) as count FROM series_genres
            INNER JOIN genres ON genres.id = series_genres.genres_id
            GROUP BY series_genres.genres_id
            ORDER BY count DESC
        """)

        keys = [x[0] for x in result.description]
        values = result.fetchall()
        
        resp = [zip(keys,v) for v in values]
        resp = [{ k:v for k,v in it } for it in resp]

        return resp

@app.get('/series/categories')
def get_categories(count_min: int = 101):
    with sqlite3.connect(paths.DB_FILE) as db:
        result = db.execute("""
            SELECT * FROM (
                SELECT series_categories.categories_id as id, categories.name as name, COUNT(*) as count FROM series_categories
                INNER JOIN categories ON categories.id = series_categories.categories_id
                GROUP BY series_categories.categories_id
                ORDER BY count DESC
            )
            WHERE count > ?
        """, [count_min])

        keys = [x[0] for x in result.description]
        values = result.fetchall()
        
        resp = [zip(keys,v) for v in values]
        resp = [{ k:v for k,v in it } for it in resp]

        return resp

sort_key_map = {
    'title': 'series.title',
    'year': 'series.year_start',
    'score': 'series.bayesian_rating',
    'time': 'series.last_update'
}

@app.get('/series/search')
def post_search(
    title: str = None,
    author: str = None,
    year_start_min: int = None,
    year_start_max: int = None,
    score_min: int = None,
    licensed: bool = None,
    completed: bool = None,
    genres: list[int] = Query(None),
    genres_exclude: list[int] = Query(None),
    categories: list[int] = Query(None),
    categories_exclude: list[int] = Query(None),
    sort_by: str = None,
    ascending: bool = True
):
    genres = genres or []
    categories = categories or []

    with sqlite3.connect(paths.DB_FILE) as db:
        subs = []

        sort_condition = f"ORDER BY {sort_key_map.get(sort_by, 'series.bayesian_rating')} { 'ASC' if ascending else 'DESC' }"

        q_data = f"""
            SELECT
                series.id, series.title, group_concat(authors.name) as authors, series.year_start, series.bayesian_rating, series.licensed, series.completed
            FROM series
            INNER JOIN series_authors ON series_authors.series_id = series.id
            INNER JOIN authors ON authors.id = series_authors.authors_id
            GROUP BY series.id
            {sort_condition}
        """

        if genres or genres_exclude:
            conditions = []

            if genres:
                conditions.append(f"series_genres.genres_id IN ({','.join(['?' for x in genres])})")
                subs.extend(genres)

            if genres_exclude:
                conditions.append(f"series_genres.genres_id NOT IN ({','.join(['?' for x in genres_exclude])})")
                subs.extend(genres_exclude)

            q_data = f"""
                SELECT * FROM ({q_data})
                INNER JOIN series_genres ON series_genres.series_id = id
                WHERE ({' AND '.join(conditions)})
                GROUP BY id
            """

            if genres:
                q_data = f"""
                    {q_data}
                    HAVING COUNT(DISTINCT(series_genres.genres_id)) = {len(genres)}
                """

        if categories:
            conditions = []

            if categories:
                conditions.append(f"series_categories.categories_id IN ({','.join(['?' for x in categories])})")
                subs.extend(categories)

            if categories_exclude:
                conditions.append(f"series_categories.categories_id NOT IN ({','.join(['?' for x in categories_exclude])})")
                subs.extend(categories_exclude)

            q_data = f"""
                SELECT * FROM ({q_data})
                INNER JOIN series_categories ON series_categories.series_id = id
                WHERE ({' AND '.join(conditions)})
                GROUP BY id
            """

            if categories:
                q_data = f"""
                    {q_data}
                    HAVING COUNT(DISTINCT(series_genres.genres_id)) = {len(categories)}
                """

        conditions = []

        if title:
            cs = []
            words = title.lower().strip().split()
            for w in words:
                cs.append('instr(lower(title), ?)')
                subs.append(w)
            conditions.append(f"({' AND '.join(cs)})")

        if author:
            cs = []
            words = author.lower().strip().split()
            for w in words:
                cs.append('instr(lower(authors), ?)')
                subs.append(w)
            conditions.append(f"({' AND '.join(cs)})")

        if year_start_min:
            conditions.append(f'year_start >= ? OR year_start IS NULL')
            subs.append(year_start_min)
        if year_start_max:
            conditions.append(f'(year_start <= ? OR year_start IS NULL)')
            subs.append(year_start_max)

        if score_min is not None:
            conditions.append(f'bayesian_rating >= ?')
            subs.append(score_min)
        
        if licensed is not None:
            conditions.append(f'licensed = ?')
            subs.append(int(licensed))
        
        if completed is not None:
            conditions.append(f'completed = ?')
            subs.append(int(completed))

        q_cond = f"WHERE ({') AND ('.join(conditions)})" if len(conditions) > 0 else ""
        q = f"""
            SELECT id FROM ({q_data})
            {q_cond}
        """
        result = db.execute(q, subs)

        resp = [x[0] for x in result.fetchall()]
        return resp

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run('run_server:app', host='0.0.0.0', port=9999, log_level='debug', reload=True)
