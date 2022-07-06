import sys
from pathlib import Path
import time
from typing import TypeVar

sys.path.append(str(Path(__file__).parent.parent))

import json
import logging
import re
import sqlite3

from classes.models import db, mu_models
from config import paths
from pony import orm
from utils.logging import configure_logging

###

configure_logging(lambda d: f"insert_mu_{d['time']}_{d['pid']}.log")

###

db_file = paths.DB_FILE
db.bind(provider="sqlite", filename=str(db_file), create_db=True)
db.generate_mapping(create_tables=True)
# orm.set_sql_debug(True)

raw_db_file = paths.DATA_DIR / "raw_mu.sqlite"
raw_db = sqlite3.connect(raw_db_file)

###


def parse_year(text: str = None) -> tuple[int, int]:
    raw = text or ""
    raw = re.sub(r"[;–.]", "-", raw)
    raw = raw.strip()
    if len(raw) == 0:
        return [None, None]

    years = raw.split("-")
    if raw == "n/a":
        years = [None, None]
    elif len(years) == 2:
        # yyyy-yyyy
        years = [int(x) for x in years]
    elif len(years) == 1:
        # yyyy
        years = [int(years[0]), "NULL"]
    elif len(years) == 3 and re.search(r"\d{4}-\d{1,2}-\d{1,2}", raw):
        # mm-dd-yyyy
        logging.warning(f"Ignoring month + day in [{text}]")
        years = [int(years[0]), "NULL"]
    else:
        # ???
        logging.warning(f"Unable to parse date from [{text}]")
        raise ValueError

    return years


T = TypeVar("T")


def upsert(cls: T, key: dict, data: dict = None) -> T:
    data = data or dict()

    obj = cls.get(**key)
    if obj is None:
        obj = cls(**key, **data)
    else:
        obj.set(**data)
    return obj


###

data = raw_db.execute("SELECT data FROM series")
data = [r[0] for r in data.fetchall()]
data = [json.loads(r) for r in data]


print(f"Found {len(data)} series.")
logging.info(f"Processing {len(data)} series.")


def main():
    with orm.db_session:
        start = time.time()
        for i, r in enumerate(data):
            if i % 5000 == 0:
                orm.commit()
            print(
                f"[{time.time()-start:.0f}s] Phase 1 - {i:05d} / {len(data)}...",
                end="\r",
            )

            typ = upsert(mu_models.Type, dict(name=r["type"]))

            try:
                year = parse_year(r["year"])[0]
            except:
                year = None

            series = upsert(
                mu_models.Series,
                dict(
                    id=r["series_id"],
                ),
                dict(
                    bayesian_rating=r["bayesian_rating"],
                    completed=r["completed"],
                    description=r["description"] or "",
                    forum_id=r["forum_id"],
                    last_updated=r["last_updated"]["timestamp"],
                    latest_chapter=r["latest_chapter"],
                    licensed=r["licensed"],
                    name=r["title"],
                    rating_votes=r["rating_votes"],
                    status=r["status"] or "",
                    year=year,
                    type=typ,
                ),
            )

            if r["anime"]["start"] and series.anime is None:
                anime = upsert(
                    mu_models.Anime,
                    dict(
                        start=r["anime"]["start"], end=r["anime"]["end"], series=series
                    ),
                )

            for a in r["authors"]:
                if a["author_id"] is None:
                    logging.warning(
                        f'Skipping author [{a["name"]}] without id for series [{r["title"]} ({r["series_id"]})].'
                    )
                    continue

                author_type = upsert(mu_models.AuthorType, dict(name=a["type"]))

                author = None
                if a["author_id"] is not None:
                    author = upsert(
                        mu_models.Author,
                        dict(
                            id=a["author_id"],
                        ),
                        dict(name=a["name"]),
                    )

                series_author = upsert(
                    mu_models.SeriesAuthor,
                    dict(
                        type=author_type, name=a["name"], author=author, series=series
                    ),
                )

            for c in r["categories"]:
                category_type = upsert(mu_models.CategoryType, dict(name=c["category"]))
                category = upsert(
                    mu_models.Category,
                    dict(
                        series=series,
                        type=category_type,
                    ),
                    dict(
                        votes=c["votes"],
                        votes_minus=c["votes_minus"],
                        votes_plus=c["votes_plus"],
                    ),
                )

            if r["image"]["url"]["original"] is not None:
                im = r["image"]
                cover = upsert(
                    mu_models.Cover,
                    dict(series=series),
                    dict(
                        height=im["height"],
                        original=im["url"]["original"],
                        thumbnail=im["url"]["thumb"],
                        width=im["height"],
                    ),
                )

            for g in r["genres"]:
                genre = upsert(mu_models.Genre, dict(name=g["genre"])).series.add(
                    series
                )

            for p in r["publishers"]:
                if p["publisher_id"] is None:
                    logging.warning(
                        f'Skipping publisher [{p["publisher_name"]}] without id for [id={r["series_id"]}] has no id.'
                    )
                    continue

                publisher = upsert(
                    mu_models.Publisher,
                    dict(
                        id=p["publisher_id"],
                    ),
                    dict(name=p["publisher_name"]),
                )
                publisher_type = upsert(mu_models.PublisherType, dict(name=p["type"]))
                series_publisher = upsert(
                    mu_models.SeriesPublisher,
                    dict(
                        series=series,
                        publisher=publisher,
                        publisher_type=publisher_type,
                    ),
                    dict(
                        notes=p["notes"] or "",
                    ),
                )

            l = r["rank"]["lists"]
            op = r["rank"]["old_position"]
            p = r["rank"]["position"]
            rank = upsert(
                mu_models.Rank,
                dict(series=series),
                dict(
                    lists_custom=l["custom"],
                    lists_reading=l["reading"],
                    lists_unfinished=l["unfinished"],
                    lists_wish=l["wish"],
                    old_position_week=op["week"],
                    old_position_month=op["month"],
                    old_position_three_months=op["three_months"],
                    old_position_six_months=op["six_months"],
                    old_position_year=op["year"],
                    position_week=p["week"],
                    position_month=p["month"],
                    position_three_months=p["three_months"],
                    position_six_months=p["six_months"],
                    position_year=p["year"],
                ),
            )

            for t in r["associated"] + [r]:
                title = upsert(mu_models.Title, dict(name=t["title"], series=series))

        print(f"Phase 1 - done in {time.time()-start:.1f}s")
        start = time.time()

        for i, r in enumerate(data):
            if i % 5000 == 0:
                orm.commit()
            print(f"Phase 2 - {i:05d} / {len(data)}...", end="\r")

            series = mu_models.Series[r["series_id"]]

            for cr in r["category_recommendations"]:
                try:
                    recommendation = mu_models.Series[cr["series_id"]]
                except orm.ObjectNotFound:
                    logging.warning(
                        f"Failed to find series [id={cr['series_id']}] recommended (by category) for [id={r['series_id']}]"
                    )
                    continue

                    cat_rec = upsert(
                        mu_models.CategoryRecommendation,
                        dict(base_series=series, recommendation=recommendation),
                        dict(weight=cr["weight"]),
                    )

            for rec in r["recommendations"]:
                try:
                    recommendation = mu_models.Series[rec["series_id"]]
                except orm.ObjectNotFound:
                    logging.warning(
                        f"Failed to find series [id={rec['series_id']}] recommended for [id={r['series_id']}]"
                    )
                    continue

                cat_rec = upsert(
                    mu_models.CategoryRecommendation,
                    dict(base_series=series, recommendation=recommendation),
                    dict(weight=rec["weight"]),
                )

            for rl in r["related_series"]:
                try:
                    series_2 = mu_models.Series[rl["related_series_id"]]
                except orm.ObjectNotFound:
                    logging.warning(
                        f"Failed to find series [id={rl['related_series_id']}] related to [id={r['series_id']}]"
                    )
                    continue

                relation_type = upsert(
                    mu_models.RelationType, dict(name=rl["relation_type"])
                )

                relation = upsert(
                    mu_models.Relation,
                    dict(
                        series_1=series, series_2=series_2, relation_type=relation_type
                    ),
                )

            for p in r["publications"]:
                if p["publisher_id"] is None:
                    logging.warning(
                        f"No publisher id for [{p=}] for series [id={r['series_id']}]"
                    )
                    continue

                try:
                    publisher = mu_models.Publisher[p["publisher_id"]]
                except orm.ObjectNotFound:
                    logging.warning(
                        f"Failed to find publisher [id={p['publisher_id']}] for series [id={r['series_id']}]"
                    )
                    continue

                publication = upsert(
                    mu_models.Publication,
                    dict(
                        name=p["publication_name"], publisher=publisher, series=series
                    ),
                )

    print(f"[{time.time()-start:.0f}s] Phase 2 - done in {time.time()-start:.1f}s")


import cProfile

cProfile.run("main()", "create.profile")
