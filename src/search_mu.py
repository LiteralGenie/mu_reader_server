import json
import logging
import random
import time
from pathlib import Path

import requests
from tinydb import TinyDB
from urlpath import URL

from config import paths
import utils

debug_file = paths.LOG_DIR / 'mu_search.log'
log = logging.basicConfig(
    filename=debug_file,
    filemode='w+',
    encoding='utf-8',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG
)


KOMGA_COOKIES = dict(SESSION='NDE2NDc5N2MtNDVlMy00NzcwLTliZmQtZGUzZDY4M2Y3MmIy')
KOMGA_API = URL('http://localhost:8080/api')


db_file = paths.DATA_DIR / 'search_db.json'
with open(db_file) as file:
    db = json.load(file)

komga_dir = Path('/media/anne/media_temp/kamgo_series')

MU_API = URL('https://api.mangaupdates.com/v1')

@utils.limit(calls=1, period=3, scope='mu')
def _search(name: str):
    ep = MU_API / 'series' / 'search'
    resp = requests.post(str(ep), json=dict(search=name))
    data = resp.json()
    assert resp.status_code == 200

    logging.debug(f'fetching [{name}] from [{ep}]')
    db[name] = dict(
        time=time.time(),
        ids=[x['record']['series_id'] for x in data['results']]
    )
    if random.random() < 0.05:
        logging.info('dumping db')
        with open(db_file, 'w+') as file:
            json.dump(db, file, indent=2)

    return data
def search(name: str):
    name = name.lower()
    logging.debug(f'Searching for [{name}]')

    if name in db:
        return db[name]
    else:
        logging.info(f'cache miss for [{name}]')
        return _search(name)

series_dir = Path('/home/anne/manga')
for s in series_dir.glob('*'):
    logging.info(f'processing [{s.name}]')
    
    try:
        assert s.is_dir()
        data = search(s.name)
        continue
    except Exception as e:
        logging.exception(e)



