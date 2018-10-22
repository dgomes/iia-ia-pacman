import functools
import asyncio
import json
import logging
import websockets
import os.path

from game import Game

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
wslogger = logging.getLogger('websockets')
wslogger.setLevel(logging.WARN)

class Game_server:
    def __init__(self, mapfile, ghosts, lives):
        self.game = Game(mapfile, ghosts, lives) 
        self.clients = set()
        self.hotseat = asyncio.Condition() 
        self.highscores = [] 
        if os.path.isfile(mapfile+".score"):
            with open(mapfile+".score", 'r') as infile:
                self.highscores = json.load(infile)
        self.current_player = None, None 

    async def incomming_handler(self, websocket, path):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                logging.debug(data)
                if data["cmd"] == "join":
                    map_info = self.game.info()
                    await asyncio.wait([websocket.send(map_info)])
                    
                    if path == "/player":
                        if self.game.running:
                            logging.debug("Wait for hotseat")
                            await self.hotseat.wait()

                        if not self.game.running:
                            if self.current_player != (None,None): 
                                self.hotseat.release()
                            logging.debug("Start Game")
                            self.current_player = data["name"], websocket
                            self.game.start(self.current_player[0])
                            await self.hotseat.acquire()
                        
                if data["cmd"] == "key" and path == "/player":
                    self.game.keypress(data["key"][0])

        except websockets.exceptions.ConnectionClosed as c:
            logging.info("Client disconnected")
        finally:
            if websocket in self.clients:
                logging.debug("remove client")
                self.clients.remove(websocket)
            if not self.clients and self.game.running:
                logging.info("close the game")
                self.game.stop()
            self.hotseat.notify()    

    async def state_broadcast_handler(self, websocket, path):
        while path == "/viewer" or not self.game.running:
            await asyncio.sleep(.1)
        while self.game.running:
            if path == "/player" and self.current_player[1] == websocket:
                await self.game.next_frame()
                if self.clients:       # asyncio.wait doesn't accept an empty list
                    await asyncio.wait([client.send(self.game.state) for client in self.clients])
    
        #update highscores
        if path == "/player":
            logging.debug("Save highscores")
            self.highscores.append((self.current_player[0], self.game.score))
            self.highscores = sorted(self.highscores, key=lambda s: -1*s[1])[:10]
    
            with open(self.game.map._filename+".score", 'w') as outfile:
                json.dump(self.highscores, outfile)


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
    parser.add_argument("--map", help="path to the map bmp", default="data/map1.bmp")
    args = parser.parse_args()

    g = Game_server(args.map, args.ghosts, args.lives)

    game_handler = functools.partial(client_handler, game=g)
    start_server = websockets.serve(game_handler, args.bind, args.port)

    loop = asyncio.get_event_loop()
    
    loop.run_until_complete(start_server)
    loop.run_forever()

