from dataclasses import asdict
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import folium
from sanic import Sanic
from sanic.request import Request
from sanic.response import JSONResponse, html, json
from sanic_ext import Extend
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, Update

from sokodoko.config import BOT_ADMIN, BOT_TOKEN, WEB_HOST, datadir
from sokodoko.db import MapDB, PointCoord, PointInfo, location_from_token
from sokodoko.geojson import create_geojson
from sokodoko.logger import LoggerHandler
from sokodoko.msg_parser import (
    ParsedText,
    RegexpPatterns,
    str_clean,
    text_parser_google_map,
)

# Init
bot = AsyncTeleBot(BOT_TOKEN)
server = Sanic("SokoDoko")
# server.static("/.well-known", Path(staticdir, ".well-known"))
log: LoggerHandler = LoggerHandler(__name__)
Extend(server)
server.config.LOGGING = True


# Telegram bot
@bot.message_handler(regexp=RegexpPatterns.google_maps)
async def parse(message: Message):
    text: Optional[str] = message.text
    if not text:
        return

    try:
        ptext: ParsedText = text_parser_google_map(text)
    except ValueError as e:
        await bot.reply_to(message, str(e))
        return
    ptext.comment = f"[{str_clean(message.from_user.full_name)}]: {ptext.comment}"

    log.debug(f"{ptext.map_url=}, {ptext.place=}, {ptext.latitude=}, {ptext.longitude=}, {ptext.comment=}, {ptext.tags=}")

    point_coord: PointCoord = PointCoord(lat=ptext.latitude, long=ptext.longitude)
    tg_map_db = MapDB(message.chat.id, point_coord)
    tg_points = tg_map_db.points
    point_exist: bool = False
    for point in tg_points:
        if point['url'] == ptext.map_url:
            point_exist = True
            for tag in ptext.tags:
                if tag not in point['tags']:
                    point['tags'].append(tag)
            if ptext.comment not in point['comments']:
                point['comments'].append(ptext.comment)
            break
    if not point_exist:
        point = PointInfo(
            place=ptext.place,
            url=ptext.map_url,
            tags=[*ptext.tags],
            comments=[ptext.comment],
            coords=point_coord,
        )
        tg_points.append(asdict(point))
    tg_map_db.add_points(tg_points)
    create_geojson(tg_map_db.url_token, tg_points)

    answer_msg: str = f"Thank you, dear {message.from_user.full_name}! Point is saved!\n\nPlace name: {ptext.place}\nCoordinates: {ptext.latitude}, {ptext.longitude}\nTags: {ptext.tags}\nGoogle Maps link: {ptext.map_url}\nCommentary:\n{ptext.comment}\n\nCheck point collection here: https://{WEB_HOST}/{tg_map_db.url_token}"
    await bot.reply_to(message, answer_msg)


@bot.message_handler(commands=['sokodoko'])
async def get_map_url(message: Message):
    tg_map_db = MapDB(message.chat.id)
    answer_msg: str = (
        f"View the SokoDoko map for this chat: https://{WEB_HOST}/{tg_map_db.url_token}"
    )
    await bot.reply_to(message, answer_msg)


@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await bot.reply_to(
        message,
        """\
こんにちはございます, I am SokoDoko bot. Your humble map helper!

If you invite me to chat, I will collect all the links that lead to map points, and then display your point collection on the map.
You can also send me links directly. So far I only understand links that look like google.com/maps/place/*.

Send the command [ /sokodoko ] in chat and I will give you a link where you can see the map with your point collection. Open the map, click on any point and you will see a popup with additional information.
\
""",
    )


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
    return html(
        '<p>Hello! Here live the <a href="https://t.me/sokodoko_bot">@sokodoko_bot</a>.</p>'
    )


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
