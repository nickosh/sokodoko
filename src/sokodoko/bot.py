from sanic import Sanic
from telebot.types import Update, Message
from telebot.async_telebot import AsyncTeleBot
from sanic.response import json, JSONResponse
from sanic.request import Request
from typing import Optional
import re

from sokodoko.config import BOT_ADMIN, BOT_TOKEN, WEB_HOST
from sokodoko.logger import LoggerHandler

hashtag_pattern = r"(#\w+)"
google_maps_pattern = r"(https?://)?(www\.)?((google\.com/maps/)|(maps\.google\.com/)|(goo\.gl/maps/)|(maps\.app\.goo\.gl/))[^\s]+"

# Init
bot = AsyncTeleBot(BOT_TOKEN)
server = Sanic("SokoDoko")
# server.static("/.well-known", Path(staticdir, ".well-known"))
log: LoggerHandler = LoggerHandler(__name__)

# Telegram bot
@bot.message_handler(regexp=google_maps_pattern)
async def start(message:Message):
    text: Optional[str] = message.text
    if not text:
        return
    tags = re.findall(hashtag_pattern, text)
    map_url = re.search(google_maps_pattern, text)
    if map_url:
        map_url = map_url.group()
    comment = re.sub(hashtag_pattern, "", text)
    comment = re.sub(google_maps_pattern, "", comment)

    answer_msg: str = f"Thank you, dear {message.from_user.full_name}/n/nGoogle Maps link: {map_url}/n/nTags: {tags}/n/nCommentary:/n{comment}"
    await bot.reply_to(message, answer_msg)

# Webserver
@server.route(f"/wh{BOT_TOKEN}", methods=["POST"])
async def webhook(request: Request) -> JSONResponse:
    if request.body is None:
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
    await bot.set_webhook(url=f"https://{WEB_HOST}/wh{BOT_TOKEN}")
    if BOT_ADMIN:
        await bot.send_message(BOT_ADMIN, "BOT STARTED")


@server.listener("before_server_stop")
async def before_stop(app, loop):
    if BOT_ADMIN:
        await bot.send_message(BOT_ADMIN, "BOT FINISHED")
