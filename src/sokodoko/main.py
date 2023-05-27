# SokoDoko Bot

# Copyright © 2022 Nikolay Shishov. All rights reserved.
# SPDX-License-Identifier: MIT

from sokodoko.bot import server
from sokodoko.config import WEB_LISTEN, WEB_PORT

if __name__ == "__main__":
    server.run(host=str(WEB_LISTEN), port=int(WEB_PORT))
