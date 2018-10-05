import json
import logging

logger = logging.getLogger('Game')
logger.setLevel(logging.DEBUG)

class Game:
    def __init__(self):
        self.running = False
        self.step = 0
        logger.info("Game()")
        self.player = None

    def reset_world(self):
        logger.debug("Reset world")

    def join(self, name, ws):
        logger.debug("Join {}".format(name))
        self.player = ws

    async def next_frame(self):
        if not self.running:
            self.running = True
        self.step += 1
        logger.debug("Step {}".format(self.step))
        await self.send(self.player, {"Step": self.step}) 

    async def send(self, ws, *args):
        msg = json.dumps([args])
        await ws.send_str(msg)


