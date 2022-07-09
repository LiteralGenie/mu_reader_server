import uvicorn

from classes.models import db
from classes.app import app
from config import paths
from utils.logging import configure_logging

# setup logging
configure_logging()

# setup db
if db.provider is None:
    db.bind(provider="sqlite", filename=str(paths.DB_FILE))
    db.generate_mapping()


if __name__ == "__main__":
    # run server
    uvicorn.run(
        "run_server:app", host="0.0.0.0", port=9999, log_level="debug", reload=True
    )
