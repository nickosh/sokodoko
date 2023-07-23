from logger import LoggerHandler
from sokodoko.config import datadir
from sokodoko.db import PointInfo, PointCoord
import json
from pathlib import Path

log: LoggerHandler = LoggerHandler(__name__)


def create_geojson(token: str, points: list):
    def add_linebreaks(string, n):
        return '\n'.join(string[i : i + n] for i in range(0, len(string), n))

    features: list = []
    for point in points:
        point_info: PointInfo = PointInfo(
            point.get("place"),
            PointCoord(point.get("coords").get("lat"), point.get("coords").get("long")),
            point.get("url"),
            point.get("tags"),
            point.get("comments"),
        )
        comments: str = "".join(
            [
                '<p>' + add_linebreaks(string.replace("\n", " "), 55) + '</p>'
                for string in point_info.comments
            ]
        )
        feature_dict: dict = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [point_info.coords.lat, point_info.coords.long],
            },
            "properties": {
                "name": f'<strong>{point_info.place}</strong>',
                "url": f'<a href="{point_info.url}" target="_blank">See on Google Maps</a>',
                "tags": f'Tags: {point_info.tags}',
                "comments": comments,
            },
        }
        features.append(feature_dict)

        geojson_dict: dict = {"type": "FeatureCollection", "features": features}
        with Path(datadir, f"{token}.json").open("w") as file:
            json.dump(geojson_dict, file)
