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

from sokodoko.config import BOT_ADMIN, BOT_TOKEN, WEB_HOST
from sokodoko.logger import LoggerHandler
from sokodoko.db import MapDB
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


@bot.message_handler(regexp=google_maps_pattern)
async def parse(message: Message):
    text: Optional[str] = message.text
    if not text:
        return
    tags = re.findall(hashtag_pattern, text)

    map_url = re.search(google_maps_pattern, text)
    if not map_url:
        log.error("No Google Map pattern was found in url!")
    map_url = get_final_url(map_url.group())
    log.debug(f"Expanded link is: {map_url}")
    parsed_url = urlparse(map_url)
    path_components = parsed_url.path.split("/")

    place = None
    if "place" in path_components:
        place_index = path_components.index("place") + 1
        if place_index < len(path_components):
            place = unquote(path_components[place_index]).replace("+", " ")
    else:
        answer_msg: str = (
            "Seems like your GMaps link is incorrect and do not lead to place"
        )
        await bot.reply_to(message, answer_msg)
        return

    latitude, longitude = None, None
    if "@" in path_components:
        coordinates_index = path_components.index(
            [i for i in path_components if "@" in i][0]
        )
        if coordinates_index < len(path_components):
            coordinates = path_components[coordinates_index].split(",")[1:3]
            if len(coordinates) == 2:
                latitude, longitude = map(float, coordinates)

    comment = re.sub(hashtag_pattern, "", text)
    comment = re.sub(google_maps_pattern, "", comment)
    comment = comment.strip()

    log.debug(f"{map_url=}, {place=}, {latitude=}, {longitude=}, {comment=}, {tags=}")

    tg_map_db = MapDB(
        message.chat.id, {"place": place, "lat": latitude, "long": longitude}
    )
    tg_points = tg_map_db.get_points()
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
        point = {"url": map_url, "tags": [*tags], "comments": [comment]}
        tg_points.append(point)
    tg_map_db.add_points(tg_points)

    answer_msg: str = f"Thank you, dear {message.from_user.full_name}\n\nGoogle Maps link: {map_url}\n\nTags: {tags}\n\nCommentary:\n{comment}"
    await bot.reply_to(message, answer_msg)


# Folium map
@server.route("/", methods=["GET"])
def map_render(request: Request):
    m = folium.Map()
    render = m.get_root().render()
    return html(render)


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
