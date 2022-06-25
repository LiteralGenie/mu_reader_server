import logging
import sqlite3
import time

import requests
import urlpath
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
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
    with sqlite3.connect(paths.DB_FILE) as con:
        db = con.cursor()

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
