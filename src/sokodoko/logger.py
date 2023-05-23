import logging
import sys

from telebot import logger as botlogger

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
botlogger.setLevel(logging.WARNING)


class LoggerHandler:
    def __init__(self, name: str = "mainlogger", level: str = "debug"):
        """Create new logger object.
        Args:
            name (str): name of logger.
            level (str): set lever for logger, can be "info", "warn", "error" or "debug".
            parent (str): set parent dearpygui window
        Raises:
            ValueError: if logger level is unknown.
        Returns:
            obj: return logger object.
        """
        self.pylog: logging.Logger = logging.getLogger(name)
        if level == "info":
            self.pylog.setLevel(logging.INFO)
        elif level == "warn":
            self.pylog.setLevel(logging.WARNING)
        elif level == "error":
            self.pylog.setLevel(logging.ERROR)
        elif level == "debug":
            self.pylog.setLevel(logging.DEBUG)
        else:
            raise ValueError("Unknown logger level")

    def debug(self, message: str):
        self.pylog.debug(message)

    def info(self, message: str):
        self.pylog.info(message)

    def warning(self, message: str):
        self.pylog.warning(message)

    def error(self, message: str):
        self.pylog.error(message)

    def critical(self, message: str):
        self.pylog.critical(message)
