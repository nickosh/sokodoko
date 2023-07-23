from sanic import Sanic
from telebot.types import Update, Message
from telebot.async_telebot import AsyncTeleBot
from sanic.response import json, JSONResponse, html
from sanic.request import Request
from typing import Optional
from urllib.parse import quote
import re
from sanic_ext import Extend
import requests
from urllib.parse import urlparse, unquote
from dataclasses import asdict
from pathlib import Path

from sokodoko.config import BOT_ADMIN, BOT_TOKEN, WEB_HOST, datadir
from sokodoko.logger import LoggerHandler
from sokodoko.db import MapDB, PointInfo, PointCoord, location_from_token
from sokodoko.geojson import create_geojson
import folium

hashtag_pattern = r"(#\w+)"
google_maps_pattern = r"(https?://)?(www\.)?((google\.com/maps/)|(maps\.google\.com/)|(goo\.gl/maps/)|(maps\.app\.goo\.gl/))[^\s]+"

# Init
bot = AsyncTeleBot(BOT_TOKEN)
server = Sanic("SokoDoko")
# server.static("/.well-known", Path(staticdir, ".well-known"))
log: LoggerHandler = LoggerHandler(__name__)
Extend(server)
server.config.LOGGING = True


# Telegram bot
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

def str_clean(input_string):
    # This regex will match any character that is not a letter, number, or space
    pattern = re.compile(r'[^a-zA-Z0-9 ]')
    # Substituting the matched characters with nothing
    return pattern.sub('', input_string)

@bot.message_handler(regexp=google_maps_pattern)
async def parse(message: Message):
    text: Optional[str] = message.text
    if not text:
        return
    tags = re.findall(hashtag_pattern, text)
    tags = [str_clean(tag) for tag in tags]

    map_url = re.search(google_maps_pattern, text)
    if not map_url:
        answer_msg: str = "No Google Map pattern was found in url!"
        log.error(answer_msg)
        await bot.reply_to(message, answer_msg)
        return
    map_url = get_final_url(map_url.group())
    log.debug(f"Expanded link is: {map_url}")

    place = str_clean(extract_place_name(map_url))
    latitude, longitude = extract_lat_long(map_url)
    if not place or not latitude or not longitude:
        answer_msg: str = (
            "Sorry, right now I understand only links whick looks like google.com/maps/place/*\nPlease try again."
        )
        log.error(answer_msg)
        await bot.reply_to(message, answer_msg)
        return

    comment = re.sub(hashtag_pattern, "", text)
    comment = re.sub(google_maps_pattern, "", comment)
    comment = f'{str_clean(message.from_user.full_name)}: {str_clean(comment.strip())}'

    log.debug(f"{map_url=}, {place=}, {latitude=}, {longitude=}, {comment=}, {tags=}")

    point_coord: PointCoord = PointCoord(lat=latitude, long=longitude)
    tg_map_db = MapDB(message.chat.id, point_coord)
    tg_points = tg_map_db.points
    point_exist: bool = False
    for point in tg_points:
        if point['url'] == map_url:
            point_exist = True
            for tag in tags:
                if tag not in point['tags']:
                    point['tags'].append(tag)
            if comment not in point['comments']:
                point['comments'].append(comment)
            break
    if not point_exist:
        point = PointInfo(
            place=place,
            url=map_url,
            tags=[*tags],
            comments=[comment],
            coords=point_coord,
        )
        tg_points.append(asdict(point))
    tg_map_db.add_points(tg_points)
    create_geojson(tg_map_db.url_token, tg_points)

    answer_msg: str = f"Thank you, dear {message.from_user.full_name}! Point is saved!\n\nPlace name: {place}\nCoordinates: {latitude}, {longitude}\nTags: {tags}\nGoogle Maps link: {map_url}\nCommentary:\n{comment}\n\nCheck it on map: https://{WEB_HOST}/{tg_map_db.url_token}"
    await bot.reply_to(message, answer_msg)


@bot.message_handler(commands=['sokodoko'])
async def map_url(message: Message):
    tg_map_db = MapDB(message.chat.id)
    answer_msg: str = (
        f"SokoDoko map for this chat: https://{WEB_HOST}/{tg_map_db.url_token}"
    )
    await bot.reply_to(message, answer_msg)

@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await bot.reply_to(message, """\
こんにちはございます, I am SokoDoko bot.
When you invite me to the chat I will collect all links which lead to map points and then will show your point collection on map.
You can send links directly to me as well. So far I understand only links which looks like google.com/maps/place/*.

Send command [ /sokodoko ] to the chat and I will give you link where you can see the map with your point collection. Click on any point and you will see popup with additional information.
\
""")

# Folium map
@server.route("/<url_token>", methods=["GET"])
async def map_render(request: Request, url_token: str):
    location: PointCoord = location_from_token(url_token)
    if not location:
        return html("<p>Oops! Seems this map not exist!</p>")
    geojson_file = Path(datadir, f"{url_token}.json")
    map = folium.Map(location=[location.long, location.lat], zoom_start=12)
    folium.GeoJson(
        data=geojson_file.open("r", encoding="utf-8-sig").read(),
        popup=folium.features.GeoJsonPopup(
            fields=['name', 'url', 'tags', 'comments'],
            aliases=['', '', '', ''],
            labels=False,
        ),
        tooltip=folium.features.GeoJsonTooltip(fields=['name', 'tags']),
    ).add_to(map)
    render = map.get_root().render()
    return html(render)


@server.route("/", methods=["GET"])
async def home_page(request: Request):
    return html("<p>Hello! Here live the <a href="https://t.me/sokodoko_bot">@sokodoko_bot</a>.</p>")


# Webserver
@server.route(f"/wh{BOT_TOKEN}", methods=["POST"])
async def webhook(request: Request) -> JSONResponse:
    if request.json is None:
        return json({"status": "bad request"}, 400)
    log.debug(f"WH body incoming: {request.json}")
    update: Optional[Update] = Update.de_json(request.json)
    if not update:
        return json({"status": "unprocessed Update from json"}, 422)
    await bot.process_new_updates([update])
    return json({"status": "ok"}, 200)


# Webserver stuff
@server.listener("before_server_start")
async def before_start(app, loop):
    await bot.remove_webhook()


@server.listener("after_server_start")
async def after_start(app, loop):
    await bot.set_webhook(url=f"https://{quote(WEB_HOST)}/wh{quote(BOT_TOKEN)}")
    log.debug(await bot.get_webhook_info())
    if BOT_ADMIN:
        await bot.send_message(BOT_ADMIN, "BOT STARTED")


@server.listener("before_server_stop")
async def before_stop(app, loop):
    await bot.remove_webhook()
    if BOT_ADMIN:
        await bot.send_message(BOT_ADMIN, "BOT FINISHED")
