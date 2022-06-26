import sys
from pathlib import Path
import traceback

sys.path.append(str(Path(__file__).parent.parent))

import json
import logging
import sqlite3
import sys
import time

import requests
import utils
from config import paths
from urlpath import URL
from utils.logging import configure_logging

###

"""
Fetch series data from the mu api. Basically stores the response as a json, no other fanciness.
"""

###

configure_logging(
    name_fn=lambda d: f"mu-fetch-series_{int(time.time())}_{d['pid']}.log"
)

###

search_db_file = paths.DATA_DIR / "search_db.json"
with open(search_db_file) as file:
    search_db = json.load(file)

###

db_file = paths.DATA_DIR / "raw_mu.sqlite"
db = sqlite3.connect(db_file)

db.execute(
    """
    CREATE TABLE IF NOT EXISTS series (
        id              INTEGER         PRIMARY KEY,
        last_fetch      REAL            NOT NULL,
        data            TEXT            NOT NULL
    )
    """
)


def read(id: int) -> bool:
    result = db.execute(
        f"""
        SELECT id FROM series WHERE id={id}
        """
    )

    return result.fetchone() is None


def insert(id: int, data: dict) -> None:
    db.execute(
        "INSERT OR REPLACE INTO series VALUES (?, ?, ?)",
        (id, time.time(), json.dumps(data)),
    )


###

MU_API = URL("https://api.mangaupdates.com/v1")


@utils.limit(calls=1, period=2, scope="mu")
def search(id: int):
    logging.debug(f"fetching series [{id}]")

    ep = MU_API / "series" / str(id)
    resp = requests.get(str(ep))
    data = resp.json()
    assert resp.status_code == 200

    return data


###

# Get ids to fetch
ids = set()
for x in search_db.values():
    ids.update(x["ids"])
ids = list(ids)
ids.sort()

# Fetch and insert into db
for (idx, id) in enumerate(ids):
    print(f"{idx:05d} / {len(ids)}", end="\r")

    try:
        result = db.execute(f"SELECT id FROM series WHERE id={id}").fetchone()
        if result is None:
            data = search(id)
            insert(id, data)
    except Exception as e:
        traceback.print_exc()
        logging.error(f"Error processing [{id=}]")
        logging.exception(e)

    if idx % 100 == 0:
        db.commit()

db.close()

###
