import logging

import requests
import urlpath
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pony import orm

from classes.models import db
from config import paths
from utils.logging import configure_logging

configure_logging()
app = FastAPI(debug=True)

if db.provider is None:
    db.bind(provider="sqlite", filename=str(paths.DB_FILE))
    db.generate_mapping()


@app.get("/series/ids")
def get_ids(offset: int = 0, limit: int = 100):
    with orm.db_session:
        result = orm.select(s.id for s in db.entities["Series"])[
            offset : offset + limit
        ]
    return list(result)


@app.get("/series/ids/{id}")
def get_series(id: int):

    with orm.db_session:
        result = orm.select(
            [
                s.id,
                s.name,
                s.description,
                s.year,
                s.bayesian_rating,
                s.licensed,
                s.completed,
                s.type.name,
                orm.group_concat(s.genres.name),
                orm.group_concat(s.categories.type.name),
                orm.group_concat(s.titles.name),
            ]
            for s in db.entities["Series"]
            if s.id == id
        )[:]

        author_result = orm.select(
            [a.name, a.type.name]
            for a in db.entities["SeriesAuthor"]
            if a.series.id == id
        )[:]

    if len(result) == 0:
        return HTTPException(404)

    resp = dict()

    keys = [
        "id",
        "title",
        "description",
        "year",
        "bayesian_rating",
        "licensed",
        "completed",
        "type",
        "genres",
        "categories",
        "titles",
    ]
    result = dict(zip(keys, result[0]))
    result["genres"] = (result["genres"] or "").split(",")
    result["categories"] = (result["categories"] or "").split(",")
    result["titles"] = (result["titles"] or "").split(",")
    resp.update(result)

    keys = [
        "name",
        "type",
    ]
    print(author_result)
    author_result = [zip(keys, r) for r in author_result]
    resp["authors"] = author_result

    return resp


@app.get("/series/images/{id}")
def get_image(id: int):
    with orm.db_session:
        result = orm.select(
            s.cover.original for s in db.entities["Series"] if s.id == id
        )[:]

    if len(result) == 0:
        return HTTPException(404)

    url = urlpath.URL(result[0])
    file = paths.COVER_DIR / url.parts[-1]
    if not file.exists():
        with open(file, "wb") as f:
            logging.info(f"fetching image [{url}]")
            content = requests.get(url).content
            f.write(content)

    return FileResponse(file)


@app.get("/series/genres")
def get_genres():
    with orm.db_session:
        result = orm.select(
            [g.name, len(s.name for s in g.series)] for g in db.entities["Genre"]
        )[:]

    keys = ["name", "count"]
    resp = [zip(keys, r) for r in result]

    return resp


@app.get("/series/categories")
def get_categories(count_min: int = 101):
    with orm.db_session:
        result = orm.select(
            [c.name, len(c.series_categories)] for c in db.entities["CategoryType"]
        ).order_by(orm.desc(2))[:]
    return result


@app.get("/series/search")
def get_search(
    title: str = None,
    author: str = None,
    year_start_min: int = None,
    year_start_max: int = None,
    score_min: int = None,
    licensed: bool = None,
    completed: bool = None,
    genres: list[str] = Query(None),
    genres_exclude: list[str] = Query(None),
    categories: list[str] = Query(None),
    categories_exclude: list[str] = Query(None),
    sort_by: str = None,
    ascending: bool = True,
):
    categories = categories or []
    categories_exclude = categories_exclude or []

    sort_key_map = {
        "title": db.entities["Series"].name,
        "year": db.entities["Series"].year,
        "score": db.entities["Series"].bayesian_rating,
        # "time": last_update,
    }

    with orm.db_session:
        result = orm.select(s for s in db.entities["Series"])

        # Filter title
        title = (title or "").split(" ")
        temp = db.entities["Title"]
        for word in title:
            temp = orm.select(t for t in temp if word in t.name)
        temp = orm.select(t.series for t in temp)
        result = orm.select(s for s in result if s in temp)

        # Filter author
        author = (author or "").split(" ")
        temp = db.entities["SeriesAuthor"]
        for word in author:
            temp = orm.select(a for a in temp if word in a.name)
        temp = orm.select(a.series for a in temp)
        result = orm.select(s for s in result if s in temp)

        # Filter year
        if year_start_min:
            result = orm.select(s for s in result if s.year >= year_start_min)
        if year_start_max:
            result = orm.select(s for s in result if s.year <= year_start_max)

        # Filter score
        if score_min:
            result = orm.select(s for s in result if s.bayesian_rating >= score_min)

        # Filter status
        if licensed is not None:
            result = orm.select(s for s in result if s.licensed == licensed)
        if completed is not None:
            result = orm.select(s for s in result if s.completed == completed)

        # Filter genres
        genres = genres or []
        for c in genres:
            result = orm.select(s for s in result if c in s.genres.name)
        genres_exclude = genres_exclude or []
        for c in genres_exclude:
            result = orm.select(s for s in result if c not in s.genres.name)

        # Filter categories
        categories = categories or []
        for c in categories:
            result = orm.select(s for s in result if c in s.categories.name)
        categories_exclude = categories_exclude or []
        for c in categories_exclude:
            result = orm.select(s for s in result if c not in s.categories.name)

        # Sort
        sort_key = sort_key_map.get(sort_by, sort_key_map["score"])
        if ascending:
            result = result.order_by(sort_key)
        else:
            result = result.order_by(orm.desc(sort_key))

        result = orm.select(s.id for s in result)
        result = list(result)

    return result


origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "run_server:app", host="0.0.0.0", port=9999, log_level="debug", reload=True
    )
