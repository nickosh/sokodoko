SokoDoko Bot
============

:star2: [Features](#star2-features) | :pushpin: [What and why](#pushpin-what-and-why) | :gear: [Run and configuration](#gear-run-and-configuration) | :spiral_notepad: [To do](#spiral\_notepad-to-do) | :scroll: [License](#scroll-license)

Easy way to keep your map point collection and see it on map. SokoDoko bot will parse Google Maps place links from chat messages, keep them and then show point collection on interactive map.

<!-- Features -->
:star2: Features
---------------

- Easy way to collect map points;
- Collected points can be easily viewed on interactive map with additional information;
- Bot automatically parses map link and extracts comment, tags and username info;
- You can send links directly to SokoDoko or invite bot to your group chat;

<!-- What and why -->
:pushpin: What and why
---------------

Invite the SokoDoko bot to chat or send messages directly to the bot.
If message contains map link, it will be parsed and saved.
All stored link collection can be viewed on interactive map.
Use '/sokodoko' command in chat to receive map link.

When bot is started it establishes connection with messenger endpoints and starts to parse incoming messages. If bot detects map link pattern, it started to process this message. When bot invites to group chat, it starts to parse all incoming chat messages for map link. 

If map link was found this message will be split into meaningful parts and saved to DB (JSON format based on TinyDB module used for now), then bot will confirm processing with reply message. Map link will be checked with GET request for validation, name of place and coordinates will be parsed from this request. Tags from message will be saved as list and all other text in message will be saved as comment. If same map link already exists in DB for current chat, only tags and comments will be added to existing data.

After each new successful DB update, geojson file for chat will be generated. Interactive map is dynamically generated from this geojson file during request.

Please note that the bot currently supports only Telegram messenger and parses links in messages that look like 'google.com/maps/place/Tokyo+Station/@35.6801278,139.7666594,17z/' - link should contain name of place and coordinates.

<!-- Run and configuration -->
:gear: Run and configuration
---------------

1. Fill config.ini with your information (bot_admin_user param is optional and can be skipped).
2. Start app with containers (using Dockerfile or docker-compose.yml). App can be started without container - use /src/sokodoko/main.py

Please note that Telegram requires valid https certificate to raise WebHook. Docker Compose configuration includes a Traefik config sample.

<!-- To do -->
:spiral_notepad: To do
---------------

- [ ] Fixing bugs and QoL changes
- [ ] LINE messenger support
- [ ] Support of links from another map services
- [ ] Support of different types of Google Maps links

<!-- License -->
:scroll: License
---------------

Distributed under the [MIT License](https://spdx.org/licenses/MIT.html) license. See LICENSE for more information.
