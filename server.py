import functools
import asyncio
import json
import logging
import websockets
import os.path

from game import Game

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('websockets')
logger.setLevel(logging.WARN)

class Game_server:
    def __init__(self, mapfile, ghosts):
        self.game = Game(mapfile, ghosts) 
        self.clients = set()
        self.highscores = [] 
        if os.path.isfile(mapfile+".score"):
            with open(mapfile+".score", 'r') as infile:
                self.highscores = json.load(infile)
        self.current_player_name = None

    async def incomming_handler(self, websocket, path):
        self.clients.add(websocket)
    
        try:
            async for message in websocket:
                data = json.loads(message)
                if data["cmd"] == "join":
                    map_info = self.game.info()
                    await asyncio.wait([websocket.send(map_info)])
                    
                    if path == "/player":
                        self.game.start() 
                
                        if "name" in data:
                            self.current_player_name = data["name"]

                if path == "/player" and data["cmd"] == "key":
                    self.game.keypress(data["key"][0])

        except websockets.exceptions.ConnectionClosed as c:
            logging.info("Client disconnected")
        finally:
            self.clients.remove(websocket)
            if not self.clients and self.game.running:
                logger.info("close the game")
                self.game.stop()

    async def state_broadcast_handler(self, websocket, path):
        while path == "/viewer" or not self.game.running:
            await asyncio.sleep(.1)
        while self.game.running:
            if path == "/player":
                await self.game.next_frame()
                if self.clients:       # asyncio.wait doesn't accept an empty list
                    await asyncio.wait([client.send(self.game.state) for client in self.clients])
                await asyncio.sleep(.1)
    
        #update highscores
        if path == "/player":
            logging.debug("Save highscores")
            self.highscores.append((self.current_player_name, self.game.score))
            self.highscores = sorted(self.highscores, key=lambda s: s[0])[:10]
    
            with open(self.game.map._filename+".score", 'w') as outfile:
                json.dump(self.highscores, outfile)
            return


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
    mapfile = "data/map1.bmp"
    g = Game_server(mapfile, 1)

    game_handler = functools.partial(client_handler, game=g)
    start_server = websockets.serve(game_handler, 'localhost', 8000)

    loop = asyncio.get_event_loop()
    
    loop.run_until_complete(start_server)
    loop.run_forever()

