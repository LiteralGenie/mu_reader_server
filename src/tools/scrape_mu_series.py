import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import traceback
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


def insert(id: int, data: dict) -> None:
    db.execute(
        "INSERT OR REPLACE INTO series VALUES (?, ?, ?)",
        (id, time.time(), json.dumps(data)),
    )


###

MU_API = URL("https://api.mangaupdates.com/v1")


@utils.limit(calls=1, period=1, scope="mu")
def search(id: int):
    logging.debug(f"fetching series [{id}]")

    ep = MU_API / "series" / str(id)
    resp = requests.get(str(ep))
    data = resp.json()
    assert resp.status_code == 200

    return data


###

id_patt = re.compile(r'"series_id": (\d+)')

###

# Get ids to fetch
unseen = set()
for x in search_db.values():
    unseen.update(x["ids"])
unseen = set(sorted(unseen))
seen = set()

# Fetch and insert into db
idx = 0
while len(unseen) > 0:
    print(f"{idx:06d} / {len(seen) + len(unseen)}", end="\r")

    id = unseen.pop()
    seen.add(id)
    idx += 1

    try:
        data = db.execute(f"SELECT data FROM series WHERE id={id}").fetchone()
        if data is None:
            data = search(id)
            insert(id, data)
            new_ids = d1 = set(
                x["series_id"]
                for grp in ["category_recommendations", "recommendations"]
                for x in data[grp]
            )
        else:
            new_ids = set(int(x) for x in id_patt.findall(data[0]))
            new_ids = set(x for x in new_ids if x > 100000)

        unseen.update(new_ids.difference(seen))
    except Exception as e:
        traceback.print_exc()
        logging.error(f"Error processing [{id=}]")
        logging.exception(e)

    if idx % 100 == 0:
        db.commit()

db.close()

###
