import json
import logging

logger = logging.getLogger('Game')
logger.setLevel(logging.DEBUG)

class Game:
    def __init__(self):
        self.running = False
        self.step = 0
        logger.info("Game()")

    def reset_world(self):
        logger.debug("Reset world")

    def join(self, name, ws):
        logger.debug("Join {}".format(name))

    def next_frame(self):
        if not self.running:
            self.running = True
        self.step += 1
        logger.debug("Step {}", self.step) 

    def send(self, ws, *args):
        msg = json.dumps([args])
        ws.send_str(msg)


