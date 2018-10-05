import os
import asyncio
import json
import logging
from aiohttp import web
from game import Game

GAME_SPEED = 1

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

async def wshandler(request):
    _LOGGER.debug("Connected")
    app = request.app
    game = app["game"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player = None
    while True:
        msg = await ws.receive()
        if msg.type == web.WSMsgType.TEXT:
            _LOGGER.debug("Got message %s" % msg.data)

            data = json.loads(msg.data)
            if data["cmd"] == "join":
                if not game.running:
                    game.reset_world()

                    _LOGGER.debug("Starting game loop")
                    asyncio.ensure_future(game_loop(game))

                game.join(player,ws)

        elif msg.type == web.WSMsgType.CLOSE:
            break

    if player:
        game.player_disconnected(player)

    _LOGGER.debug("Closed connection")
    return ws

async def game_loop(game):
    _LOGGER.info("Starting game")
    while True:
        game.next_frame()
        if not game.running:
            break
        await asyncio.sleep(1./GAME_SPEED)
    _LOGGER.info("Stopping game")



event_loop = asyncio.get_event_loop()
event_loop.set_debug(True)

app = web.Application()

app["game"] = Game()

app.router.add_route('GET', '/connect', wshandler)
#app.router.add_route('GET', '/', handle)

port = int(os.environ.get('PORT', 8000))
web.run_app(app, port=port)
