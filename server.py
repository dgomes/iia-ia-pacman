import functools
import asyncio
import json
import logging
import websockets
import os.path
from collections import namedtuple
from game import Game

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
wslogger = logging.getLogger('websockets')
wslogger.setLevel(logging.WARN)

logger = logging.getLogger('Server')
logger.setLevel(logging.DEBUG)

Player = namedtuple('Player', ['name', 'ws']) 

class Game_server:
    def __init__(self, mapfile, ghosts, lives, timeout):
        self.game = Game(mapfile, ghosts, lives, timeout) 
        self.hotseat = asyncio.Lock()
        self.viewers = set()
        self.current_player = None 

    async def incomming_handler(self, websocket, path):
        try:
            async for message in websocket:
                data = json.loads(message)
                if data["cmd"] == "join":
                    map_info = self.game.info()
                    await asyncio.wait([websocket.send(map_info)])
                    
                    if path == "/player":
                        while self.game.running:
                            logger.debug("Wait for current game end")
                            await asyncio.sleep(1)

                        logger.debug("Start Game")
                        await self.hotseat.acquire()
                        self.current_player = Player(data["name"], websocket)
                        self.game.start(self.current_player.name)
                    
                    if path == "/viewer":
                        self.viewers.add(websocket)

                if data["cmd"] == "key" and path == "/player":
                    logger.debug((self.current_player.name, data))
                    self.game.keypress(data["key"][0])

        except websockets.exceptions.ConnectionClosed as c:
            logger.info("Client disconnected")
        finally:
            if websocket in self.viewers:
                self.viewers.remove(websocket)
            if self.game.running and self.current_player.ws == websocket:
                logger.info("stop game, player has left")
                self.game.stop()

    async def state_broadcast_handler(self, websocket, path):
        while path == "/viewer" or not self.game.running or not self.current_player.ws == websocket:
            await asyncio.sleep(.1)
        
        try:
            while self.game.running:
                #player is the only responsible for triggering game updates
                if path == "/player" and self.current_player.ws == websocket:
                    await self.game.next_frame()
                    await asyncio.wait([self.current_player.ws.send(self.game.state)])
                    if self.viewers:
                        await asyncio.wait([client.send(self.game.state) for client in self.viewers])

        finally:
            #make sure we release the hotseat no matter what
            self.hotseat.release()


async def client_handler(websocket, path, game):
    incomming_task = asyncio.ensure_future(
        game.incomming_handler(websocket, path))
    state_broadcast_task = asyncio.ensure_future(
        game.state_broadcast_handler(websocket, path))
    done, pending = await asyncio.wait(
        [incomming_task, state_broadcast_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", help="IP address to bind to", default="localhost")
    parser.add_argument("--port", help="TCP port", type=int, default=8000)
    parser.add_argument("--ghosts", help="Number of ghosts", type=int, default=1)
    parser.add_argument("--lives", help="Number of lives", type=int, default=3)
    parser.add_argument("--timeout", help="Timeout after this amount of steps", type=int, default=3000)
    parser.add_argument("--map", help="path to the map bmp", default="data/map1.bmp")
    args = parser.parse_args()

    g = Game_server(args.map, args.ghosts, args.lives, args.timeout)

    game_handler = functools.partial(client_handler, game=g)
    start_server = websockets.serve(game_handler, args.bind, args.port)

    loop = asyncio.get_event_loop()
    
    loop.run_until_complete(start_server)
    loop.run_forever()

