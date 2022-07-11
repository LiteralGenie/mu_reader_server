import time

# https://gist.github.com/JBlond/2fea43a3049b38287e5e9cefc87b2124
COLOR_MAP = dict(
    BLACK=30, RED=31, GREEN=32, YELLOW=33, BLUE=34, PURPLE=35, CYAN=36, WHITE=37
)
STYLE_MAP = dict(
    REGULAR=lambda color: f"\033[0;{color}m",
    BOLD=lambda color: f"\033[1;{color}m",
    UNDERLINE=lambda color: f"\033[4;{color}m",
    BACKGROUND=lambda color: f"\033[{color + 10}m",
    INTENSE=lambda color: f"\033[0;{color + 60}m",
    BOLD_INTENSE=lambda color: f"\033[1;{color + 60}m",
    VERY_INTENSE=lambda color: f"\033[0;{color + 70}m",
)


class Timer:
    color = None
    style = "REGULAR"

    def __init__(self, precision=1):
        self.start = time.time()
        self.precision = precision

    def __enter__(self) -> "Timer":
        self.start = time.time()
        return self

    def print(
        self, *texts, color: str | None = None, style: str | None = None, **kwargs
    ) -> None:
        color = color or self.color
        style = style or self.style

        color = str(color).upper()
        color = COLOR_MAP.get(color, None)

        msgs = [f"[{round(self.elapsed, self.precision)}s]"] + [str(x) for x in texts]
        if color:
            style = str(style).upper()
            style_fn = STYLE_MAP.get(style, STYLE_MAP["REGULAR"])
            msgs = [style_fn(color) + x + "\033[0m" for x in msgs]

        print(*msgs, **kwargs)

    @property
    def elapsed(self) -> float:
        return time.time() - self.start

    def __exit__(*args, **kwargs):
        pass
