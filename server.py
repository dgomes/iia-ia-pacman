import functools
import asyncio
import json
import logging
import websockets

from game import Game

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('websockets')
logger.setLevel(logging.WARN)

class Game_server:
    def __init__(self):
        self.game = Game() 
        self.clients = set()

    async def keyprocess_handler(self, websocket, path):
        self.clients.add(websocket)
    
        try:
            async for message in websocket:
                data = json.loads(message)
                if data["cmd"] == "join":
                    logging.info("Restart game")
                    self.game.start() 
                if data["cmd"] == "key":
                    self.game.keypress(data["key"])

        except websockets.exceptions.ConnectionClosed as c:
            logging.info("Client disconnected")
        finally:
            self.clients.remove(websocket)
            if not self.clients:
                self.game.stop()

    async def state_broadcast_handler(self, websocket, path):
        while self.game:
            if path == "/player":
                await self.game.next_frame()
                if self.clients:       # asyncio.wait doesn't accept an empty list
                    await asyncio.wait([client.send(self.game.state) for client in self.clients])
            else:
                await asyncio.sleep(.1)

async def client_handler(websocket, path, game):
    keyprocess_task = asyncio.ensure_future(
        game.keyprocess_handler(websocket, path))
    state_broadcast_task = asyncio.ensure_future(
        game.state_broadcast_handler(websocket, path))
    done, pending = await asyncio.wait(
        [keyprocess_task, state_broadcast_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

if __name__ == "__main__":
    g = Game_server()

    game_handler = functools.partial(client_handler, game=g)
    start_server = websockets.serve(game_handler, 'localhost', 8000)

    loop = asyncio.get_event_loop()
    
    loop.run_until_complete(start_server)
    loop.run_forever()

