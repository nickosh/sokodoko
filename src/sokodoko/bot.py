from sanic import Sanic
from telebot.types import Update, Message
from telebot.async_telebot import AsyncTeleBot
from sanic.response import json, JSONResponse
from sanic.request import Request
from typing import Optional
from urllib.parse import quote
import re
from sanic_ext import Extend

from sokodoko.config import BOT_ADMIN, BOT_TOKEN, WEB_HOST
from sokodoko.logger import LoggerHandler
from sokodoko.db import Map
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
@bot.message_handler(regexp=google_maps_pattern)
async def parse(message: Message):
    text: Optional[str] = message.text
    if not text:
        return
    tags = re.findall(hashtag_pattern, text)
    map_url = re.search(google_maps_pattern, text)
    if map_url:
        map_url = map_url.group()
    comment = re.sub(hashtag_pattern, "", text)
    comment = re.sub(google_maps_pattern, "", comment)
    comment = comment.strip()

    tg_map = Map(message.chat.id)
    tg_points = tg_map.get_points()
    point = [point for point in tg_points if point['url'] == map_url][0]
    if not point:
        point = {"url": "map_url", "tags": [*tags], "comments": [comment]}
    else:
        point['tags'].extend(tags)
        point['comments'].append(comment)

    answer_msg: str = f"Thank you, dear {message.from_user.full_name}\n\nGoogle Maps link: {map_url}\n\nTags: {tags}\n\nCommentary:\n{comment}"
    await bot.reply_to(message, answer_msg)


# Folium map
@server.route("/", methods=["GET"])
def map_render():
    m = folium.Map()
    return m.get_root().render()


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
