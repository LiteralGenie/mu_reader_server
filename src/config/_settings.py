from pathlib import Path
from typing import TypedDict, cast
from . import paths
import toml


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
        data = cast(SettingsInterface, toml.load(paths.CONFIG_DIR / "settings.toml"))
        return Settings(data)

    def validate(self) -> bool:
        """
        Validate each attr.
        """

        for x in self.series_dirs:
            if not x.exists():
                raise ValueError

        return True
