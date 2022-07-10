from utils.timer import Timer
import logging
from dataclasses import dataclass, field
from pathlib import Path

from cfuzzyset import cFuzzySet
from pony import orm

from classes.models.mu_models import Series, Title
from classes.models.storage_models import SeriesFolder
from classes.settings import Settings

log = logging.getLogger(__name__)


@dataclass
class BookInfo:
    name: str
    path: Path


@dataclass
class SeriesInfo:
    name: str
    path: Path
    books: list[BookInfo] = field(default_factory=list)


class FileManager:
    def __init__(self):
        self.settings = Settings.load()

    def scan(self) -> list[SeriesInfo]:
        """
        List series on disk.
        """
        log.info("Scanning for series")

        result: list[SeriesInfo] = []
        timer = Timer()

        # Find series folders
        folders: list[Path] = []
        for dir in self.settings.series_dirs:
            [folders.append(x) for x in dir.iterdir() if x.is_dir()]

        # Find book files for each series
        for folder in folders:
            series = SeriesInfo(name=folder.name, path=folder.absolute())

            files = [x for x in folder.iterdir() if "." in x.name]
            for file in files:
                book = BookInfo(name=file.stem, path=file.absolute())
                series.books.append(book)

            result.append(series)

        log.info(f"Found {len(result)} folders in {timer.elapsed:.1f}s")
        return result

    def update_db(self, series: list[SeriesInfo], update=False) -> None:
        timer = Timer()

        with orm.db_session:
            # Get MU title data
            titles = orm.select([t.name, t.series.id] for t in Title)[:]
            title_map = {t[0].lower(): t[1] for t in titles}
            title_set = cFuzzySet([t[0].lower() for t in titles])

            for s in series:
                # Link folder to a MU series
                sf = SeriesFolder.get(name=s.name)
                if sf is None or update:
                    # Search for matching title
                    results = title_set.get(s.name.lower())
                    if results is None:
                        log.warning(f"No metadata for [{s.name}]")
                        series_match = None
                        dist = None
                    else:
                        [dist, title] = results[0]
                        series_match = Series[title_map[title]]

                    # Create or update SeriesFolder in db
                    data = dict(
                        name=s.name,
                        path=str(s.path),
                        series=series_match,
                        series_score=dist,
                    )

                    if sf is None:
                        sf = SeriesFolder(**data)
                    else:
                        sf.set(**data)

        log.info(f"Processed {len(series)} SeriesFolders in {timer.elapsed:.1f}s")