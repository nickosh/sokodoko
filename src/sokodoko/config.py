from configparser import ConfigParser
from pathlib import Path

from logger import LoggerHandler

log: LoggerHandler = LoggerHandler(__name__)


workdir: Path = Path(__file__).resolve().parents[0]
datadir: Path = Path(workdir, "data")
datadir.mkdir(exist_ok=True)


def config_init():
    global config, config_path

    config: ConfigParser = ConfigParser()
    config_path: Path = Path(workdir, "config.ini")
    if config_path.exists():
        config.read(config_path)
    else:
        msg: str = "Can't find config.ini file"
        log.error(msg)
        raise EnvironmentError(msg)


def config_load():
    if config:
        global cfg_bot
        cfg_bot: dict = config["bot"]


def config_save():
    with config_path.open("w") as configfile:
        config.write(configfile)


config_init()
config_load()

try:
    BOT_TOKEN: str = cfg_bot["bot_api_key"]
    BOT_ADMIN: str = cfg_bot["bot_admin_user"]
    WEB_HOST: str = cfg_bot["web_host"]
    WEB_PORT: int = cfg_bot.getint("web_port")
    WEB_LISTEN: str = cfg_bot["web_listen"]
except Exception as e:
    log.error(f"Fail to load app params from config file: {e}")
