import time


class Timer:
    def __init__(self, precision=1):
        self.start = time.time()
        self.precision = precision

    def __enter__(self) -> "Timer":
        self.start = time.time()
        return self

    def print(self, *texts: str, **kwargs) -> None:
        print(f"[{round(self.elapsed, self.precision)}s]", *texts, **kwargs)

    @property
    def elapsed(self) -> float:
        return time.time() - self.start

    def __exit__(*args, **kwargs):
        pass
