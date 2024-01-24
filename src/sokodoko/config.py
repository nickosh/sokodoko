from pathlib import Path
from tinydb import TinyDB
from decouple import config

from logger import LoggerHandler

log: LoggerHandler = LoggerHandler(__name__)


workdir: Path = Path(__file__).resolve().parents[2]
datadir: Path = Path(workdir, "data")
datadir.mkdir(exist_ok=True)

db: TinyDB = TinyDB(
    Path(datadir, "maps.json"), sort_keys=True, indent=4, separators=(",", ": ")
)

try:
    BOT_TOKEN: str = config('BOT_TOKEN', default="")
    BOT_ADMIN: str = config('BOT_ADMIN', default="")
    WEB_HOST: str = config('WEB_HOST', default="")
    WEB_PORT: int = config('WEB_PORT', default=80, cast=int)
    WEB_LISTEN: str = config('WEB_LISTEN', default="0.0.0.0")
except Exception as e:
    log.error(f"Fail to load app params from env: {e}")
