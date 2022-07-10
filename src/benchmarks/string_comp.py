import gc
import json
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

CWD = Path(__file__).parent

### helpers


@dataclass
class TestResult:
    run_time: float

    # each match is a mapping from
    #   [query string] -> [list of candidates and their match scores]
    # where the candidates are sorted by best-score first
    matches: dict[str, list[tuple[str, float]]]


class TestFixture(ABC):
    name: str
    max_run_time = 30

    def __init__(self, titles: list[str], queries: list[str], *args, **kwargs):
        self.titles = titles
        self.queries = queries

    def run(self) -> TestResult:
        start = time.time()

        # process each query
        matches: dict[str, list[tuple[str, float]]] = dict()
        for i, x in enumerate(self.queries):
            # dump progress to std out
            elapsed = time.time() - start
            print(
                f"[{elapsed:.1f}s @ {1000 * elapsed / (i+1):.1f}ms] Processing {i} / {len(self.queries)}...",
                end="\r",
            )

            # quit if taking too long
            if elapsed > self.max_run_time:
                result = TestResult(run_time=elapsed, matches=matches)
                print(" " * 100, end="\r")
                raise TimeoutError(result)

            # save result
            matches[x] = self.match(x)

        # tidy up
        print(" " * 100, end="\r")
        elapsed = time.time() - start
        matches = {
            k: sorted(v, key=lambda pair: pair[1])[:10] for k, v in matches.items()
        }

        # return
        return TestResult(run_time=elapsed, matches=matches)

    @abstractmethod
    def match(self, query: str) -> list[tuple[str, float]]:
        pass

    def set_up(self) -> float:
        return 0

    def tear_down(self) -> float:
        start = time.time()
        gc.collect()
        elapsed = time.time() - start
        return elapsed


def random_string(n: int) -> str:
    pool = "abcdefghijklmnopqrstuvwxyz    "
    result = "".join(random.choices(pool, k=n))
    return result


### test cases

import sqlite3


class SqliteTest(TestFixture):
    name = "sqlite (editdist3)"
    db: sqlite3.Connection

    def set_up(self):
        start = time.time()

        # init db
        self.db = sqlite3.connect(":memory:")
        self.db.enable_load_extension(True)
        self.db.load_extension(str(CWD / "spellfix.so"))
        self.db.execute(
            """
            CREATE TABLE titles (
                name TEXT PRIMARY KEY
            )
        """
        )

        # insert data
        self.db.executemany(
            "INSERT OR IGNORE INTO titles VALUES (?)",
            [(x,) for x in self.titles],
        )

        return time.time() - start

    def match(self, query: str):
        return self.db.execute(
            """
                SELECT name, EDITDIST3(name, ?) AS dist FROM titles
                ORDER BY dist ASC
            """,
            (query,),
        ).fetchall()


from cfuzzyset import cFuzzySet


class FuzzySetTest(TestFixture):
    name = "FuzzySet"
    db: cFuzzySet

    def set_up(self):
        start = time.time()
        self.db = cFuzzySet(titles)
        return time.time() - start

    def match(self, query: str):
        results = self.db.get(query)
        results = [(r[1], r[0]) for r in results or []]
        return results


import textdistance


class TextDistanceTest(TestFixture):
    def __init__(self, *args, dist_fn, **kwargs):
        super().__init__(*args, **kwargs)
        self.dist_fn = dist_fn
        self.name = str(dist_fn)

    def match(self, query: str):
        result = [(x, self.dist_fn(query, x)) for x in self.titles]
        return result


import jellyfish


class JellyfishTest(TestFixture):
    def __init__(self, *args, dist_fn, **kwargs):
        super().__init__(*args, **kwargs)
        self.dist_fn = dist_fn
        self.name = str(dist_fn)

    def match(self, query: str):
        result = [(x, self.dist_fn(query, x)) for x in self.titles]
        return result


### data

with open(CWD / "queries.json") as file:
    # queries = json.load(file)
    queries = [random_string(40) for _ in range(10000)]
    random.shuffle(queries)
    queries = queries[:]
with open(CWD / "titles.json") as file:
    titles = json.load(file)
    random.shuffle(titles)

### run

if __name__ == "__main__":
    fixtures: list[TestFixture] = [
        JellyfishTest(titles, queries, dist_fn=jellyfish.damerau_levenshtein_distance),
        JellyfishTest(titles, queries, dist_fn=jellyfish.hamming_distance),
        JellyfishTest(titles, queries, dist_fn=jellyfish.jaro_similarity),
        JellyfishTest(titles, queries, dist_fn=jellyfish.jaro_winkler_similarity),
        JellyfishTest(titles, queries, dist_fn=jellyfish.levenshtein_distance),
        TextDistanceTest(titles, queries, dist_fn=textdistance.DamerauLevenshtein),
        TextDistanceTest(titles, queries, dist_fn=textdistance.Hamming),
        TextDistanceTest(titles, queries, dist_fn=textdistance.Jaro),
        TextDistanceTest(titles, queries, dist_fn=textdistance.JaroWinkler),
        TextDistanceTest(titles, queries, dist_fn=textdistance.Levenshtein),
        FuzzySetTest(titles, queries),
        SqliteTest(titles, queries),
    ]

    for fixture in fixtures:
        set_up_time = fixture.set_up()

        try:
            print(f"testing {fixture.name}...")
            r = fixture.run()
        except TimeoutError as e:
            r: TestResult = e.args[0]
            print(f"TIMEOUT")
        print(
            f"processed {len(r.matches)} queries in {r.run_time:.1f}s at {1000 * r.run_time / len(r.matches):.1f}ms per query."
        )

        tear_down_time = fixture.tear_down()
        print()
