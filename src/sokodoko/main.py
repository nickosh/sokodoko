# SokoDoko Bot

# Copyright © 2022 Nikolay Shishov. All rights reserved.
# SPDX-License-Identifier: MIT

import ssl
from pathlib import Path

from sokodoko.bot import server
from sokodoko.config import WEB_LISTEN, WEB_PORT, workdir

if __name__ == "__main__":
    context: ssl.SSLContext = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(
        Path(workdir, "fullchain.pem").resolve(),
        keyfile=Path(workdir, "privkey.pem").resolve(),
    )
    server.run(host=str(WEB_LISTEN), port=int(WEB_PORT), ssl=context)
