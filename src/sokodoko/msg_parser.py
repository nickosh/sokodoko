import re
from urllib.parse import unquote, urlparse

import requests
from dataclasses import dataclass

from sokodoko.logger import LoggerHandler

log: LoggerHandler = LoggerHandler(__name__)

@dataclass
class RegexpPatterns:
    google_maps = r"(https?://)?(www\.)?((google\.[\w\.-]+/maps/)|(maps\.google\.[\w\.-]+/)|(goo\.gl/maps/)|(maps\.app\.goo\.gl/))[^\s]+"
    hashtag = r"(#\w+)"

def get_final_url(url):
    response = requests.head(url, allow_redirects=True)
    return response.url


def extract_place_name(url):
    parsed_url = urlparse(url)
    path_components = parsed_url.path.split("/")

    place = None
    if "place" in path_components:
        place_index = path_components.index("place") + 1
        if place_index < len(path_components):
            place = unquote(path_components[place_index]).replace("+", " ")
    return place


def extract_lat_long(url):
    # Define the regular expression pattern
    pattern = r'@(-?\d+\.\d+),(-?\d+\.\d+)'

    # Search for the pattern in the URL
    match = re.search(pattern, url)

    if match:
        # Extract latitude and longitude values
        latitude = float(match.group(2))
        longitude = float(match.group(1))

        return latitude, longitude
    else:
        # Pattern not found in the URL
        return None, None


def str_clean(input_string: str):
    # This regex will match any character that is not a letter, number, or space
    pattern = re.compile(r'[^a-zA-Z0-9 \nа-яА-ЯёЁ.]')
    # Substituting the matched characters with nothing
    string = input_string.replace("\n", " ").strip()
    return pattern.sub('', string)

@dataclass
class ParsedText:
    map_url: str
    place: str
    latitude: float
    longitude: float
    comment: str
    tags: list

def text_parser_google_map(text: str) -> ParsedText:
    tags = re.findall(RegexpPatterns.hashtag, text)
    tags = [str_clean(tag) for tag in tags]

    map_url = re.search(RegexpPatterns.google_maps, text)
    if not map_url:
        answer_msg: str = "No Google Map pattern was found in url!"
        log.error(answer_msg)
        raise ValueError(answer_msg)
    map_url = get_final_url(map_url.group())
    log.debug(f"Expanded link is: {map_url}")

    place = str_clean(extract_place_name(map_url))
    latitude, longitude = extract_lat_long(map_url)
    if not place or not latitude or not longitude:
        answer_msg: str = "Sorry, right now I only understand links that look like google.com/maps/place/*\nPlease try again with a different link."
        log.error(answer_msg)
        raise ValueError(answer_msg)

    comment = re.sub(RegexpPatterns.hashtag, "", text)
    comment = re.sub(RegexpPatterns.google_maps, "", comment)
    comment = str_clean(comment)

    return ParsedText(map_url, place, latitude, longitude, comment, tags)


