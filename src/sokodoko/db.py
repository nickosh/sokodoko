from sokodoko.config import db
from secrets import token_urlsafe
from datetime import datetime
from tinydb import Query
from typing import List, Optional
from dataclasses import dataclass, asdict

from logger import LoggerHandler

log: LoggerHandler = LoggerHandler(__name__)


@dataclass
class PointCoord:
    lat: float
    long: float


@dataclass
class PointInfo:
    place: str
    coords: PointCoord
    url: str
    tags: list
    comments: list


@dataclass
class MapInfo:
    tg_group: int
    url_token: str
    lang: str
    init_coords: PointCoord
    points: list
    creation_date: str = str(datetime.now())
    update_date: str = str(datetime.now())


class MapDB:
    def __init__(self, tg_group: int, point_coord: Optional[PointCoord] = None) -> None:
        self.tg_group: int = tg_group
        self.db: dict = self._get_map(point_coord)
        assert self.db, "DB no found and new one not created!"
        self.url_token = self.db["url_token"]

    @property
    def points(self) -> list[dict]:
        self.sync()
        return self.db['points']

    def sync(self) -> None:
        self.db = self._get_map()

    def _get_map(self, point_coord: Optional[PointCoord] = None) -> dict:
        Map = Query()
        map_db = db.search(Map.tg_group == self.tg_group)
        if map_db:
            return map_db[0]
        # No map found in DB, let's create new one
        if not point_coord:
            raise ValueError("Going to create new map but no info provided")
        db.insert(
            asdict(
                MapInfo(
                    tg_group=self.tg_group,
                    url_token=token_urlsafe(10),
                    lang="en",
                    init_coords=point_coord,
                    points=[],
                )
            )
        )
        return db.search(Map.tg_group == self.tg_group)[0]

    def add_points(self, points: List[dict]) -> None:
        Map = Query()
        db.update(
            {'points': points, 'update_date': str(datetime.now())},
            Map.tg_group == self.tg_group,
        )
        self.sync()
