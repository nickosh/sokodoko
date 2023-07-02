from sokodoko.config import db
from secrets import token_urlsafe
from datetime import datetime
from tinydb import Query
from typing import List

from logger import LoggerHandler

log: LoggerHandler = LoggerHandler(__name__)


class Map:
    def __init__(self, tg_group: int) -> None:
        self.tg_group: int = tg_group
        self.db: dict = self.get_map(tg_group)

    def get_map(self, tg_group: int) -> dict:
        Map = Query()
        map_db = db.search(Map.tg_group == tg_group)
        if map_db:
            return map_db[0]
        db.insert(
            {
                'tg_group': tg_group,
                'url_token': token_urlsafe(10),
                'lang': "en",
                'points': [],
                'creation_date': str(datetime.now()),
                'update_date': str(datetime.now()),
            }
        )
        return db.search(Map.tg_group == tg_group)[0]

    def add_points(self, points: List[dict]) -> None:
        Map = Query()
        db.update(
            {'points': points, 'update_date': str(datetime.now())},
            Map.tg_group == self.tg_group,
        )
        self.get_points()

    def get_points(self) -> list[dict]:
        self.db = self.get_map(self.tg_group)
        return self.db['points']
