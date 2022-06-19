from pathlib import Path


SRC_DIR = Path(__file__).parent.parent

CACHE_DIR = SRC_DIR / 'cache'
CONFIG_DIR = SRC_DIR / 'config'
DATA_DIR = SRC_DIR / 'data'

LOG_DIR = CACHE_DIR / 'logs'
COVER_DIR = CACHE_DIR / 'covers'

DB_FILE = DATA_DIR / 'db.sqlite'

for p in [
    CACHE_DIR,
    COVER_DIR,
    CONFIG_DIR,
    DATA_DIR,
    LOG_DIR,
]:
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)