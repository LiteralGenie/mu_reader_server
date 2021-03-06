from pathlib import Path
from typing import TypedDict, cast

import toml
from config import paths


class SettingsInterface(TypedDict):
    series_dirs: list[str]


class Settings:
    series_dirs: list[Path]

    def __init__(self, data: SettingsInterface):
        self.series_dirs = []
        for x in data["series_dirs"]:
            self.series_dirs.append(Path(x))

        self.validate()

    @classmethod
    def load(cls) -> "Settings":
        data = toml.load(paths.CONFIG_DIR / "settings.toml")
        data = cast(SettingsInterface, data)
        return Settings(data)

    def dump(self) -> None:
        data = dict(series_dirs=[str(x) for x in self.series_dirs])
        toml.dump(data, open(paths.CONFIG_DIR / "settings.toml", "w"))

    def validate(self) -> bool:
        """
        Validate each attr.
        """

        for x in self.series_dirs:
            if not x.exists():
                raise ValueError

        return True
