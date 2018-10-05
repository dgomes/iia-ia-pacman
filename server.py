import os
import asyncio
import json
import logging
from aiohttp import web
from game import Game

GAME_SPEED = 1

async def handle(request):
    """
    Serves files for the GUI
    """
    ALLOWED_FILES = ["map", "pacman.png", "ghost.png"]
    name = request.match_info.get('name')
    if name in ALLOWED_FILES:
        try:
            with open(name, 'rb') as index:
                return web.Response(body=index.read(), content_type='image/png')
        except FileNotFoundError:
            pass
    return web.Response(status=404)

async def wshandler(request):
    """
    Handle agents commands
    """
    logging.debug("New Agent connected")
    
    app = request.app
    game = app["game"]
   
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player = None
    while True:
        msg = await ws.receive()
        if msg.type == web.WSMsgType.TEXT:
            logging.debug("Got message %s" % msg.data)

            data = json.loads(msg.data)
            if data["cmd"] == "join":
                if not game.running:
                    game.reset_world()

                    logging.debug("Starting game loop")
                    asyncio.ensure_future(game_loop(game))

                game.join(player,ws)

        elif msg.type == web.WSMsgType.CLOSE:
            break

    if player:
        game.player_disconnected(player)

    logging.debug("Agent disconnected")
    return ws

async def game_loop(game):
    logging.info("Starting game")
    while True:
        await game.next_frame()
        if not game.running:
            break
        await asyncio.sleep(1./GAME_SPEED)
    logging.info("Stopping game")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    event_loop = asyncio.get_event_loop()

    app = web.Application()

    app["game"] = Game()

    app.router.add_route('GET', '/connect', wshandler)
    app.router.add_route('GET', '/', handle)

    port = int(os.environ.get('PORT', 8000))
    web.run_app(app, port=port)
