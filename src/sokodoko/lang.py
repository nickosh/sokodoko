# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass
class Language:
    en: dict = {
        # Welcome message
        "welcome_message": "Welcome to SokoDoko!"
    }
    ru: dict = {
        # Приветственное сообщение
        "welcome_message": "Добро пожаловать в SokoDoko!",
    }
