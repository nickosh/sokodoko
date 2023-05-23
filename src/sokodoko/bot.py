import sanic
import telebot
import ujson

from sokodoko.config import BOT_ADMIN, BOT_TOKEN, WEB_HOST
from sokodoko.logger import LoggerHandler

# Init
bot = telebot.TeleBot(BOT_TOKEN)
server = sanic("SokoDoko")
# server.static("/.well-known", Path(staticdir, ".well-known"))
log: LoggerHandler = LoggerHandler.new(__name__)

# Telegram bot
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Hello, " + message.from_user.first_name)


# Webserver
@server.route(f"/wh{BOT_TOKEN}", methods=["POST"])
def webhook(request):
    if request.body is None:
        return ujson({"status": "broken request"}, 403)
    json_string = ujson.loads(request.body.decode("utf-8"))
    log.debug(f"WH body incoming: {json_string}")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return ujson({"status": "ok"}, 200)


# Webserver stuff
@server.listener("before_server_start")
async def before_start(app, loop):
    bot.remove_webhook()


@server.listener("after_server_start")
async def after_start(app, loop):
    bot.set_webhook(url=f"https://{WEB_HOST}/wh{BOT_TOKEN}")
    bot.send_message(BOT_ADMIN, "BOT STARTED")


@server.listener("before_server_stop")
async def before_stop(app, loop):
    bot.send_message(BOT_ADMIN, "BOT FINISHED")
