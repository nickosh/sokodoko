from configparser import ConfigParser, SectionProxy
from pathlib import Path
from tinydb import TinyDB

from logger import LoggerHandler

log: LoggerHandler = LoggerHandler(__name__)


workdir: Path = Path(__file__).resolve().parents[0]
datadir: Path = Path(workdir, "data")
datadir.mkdir(exist_ok=True)

db: TinyDB = TinyDB(
    Path(datadir, "maps.json"), sort_keys=True, indent=4, separators=(",", ": ")
)


def config_init() -> tuple[ConfigParser, Path]:
    config: ConfigParser = ConfigParser()
    config_path: Path = Path(workdir, "config.ini")
    print(config_path.resolve())
    if config_path.exists():
        config.read(config_path)
    else:
        msg: str = "Can't find config.ini file"
        log.error(msg)
        raise EnvironmentError(msg)

    return config, config_path


def config_load(config: ConfigParser) -> SectionProxy:
    if config:
        return config["bot"]
    raise EnvironmentError("Can't load bot config!")


def config_save():
    with config_path.open("w") as configfile:
        config.write(configfile)


config, config_path = config_init()
cfg_bot = config_load(config)

try:
    BOT_TOKEN: str = cfg_bot["bot_api_key"]
    BOT_ADMIN: str = cfg_bot["bot_admin_user"]
    WEB_HOST: str = cfg_bot["web_host"]
    WEB_PORT: int = cfg_bot.getint("web_port")
    WEB_LISTEN: str = cfg_bot["web_listen"]
except Exception as e:
    log.error(f"Fail to load app params from config file: {e}")
