import asyncio
import json
import logging

logger = logging.getLogger('Game')
logger.setLevel(logging.DEBUG)

class Game:
    def __init__(self):
        self._running = False
        self._step = 0
        logger.info("Game()")
        self._state = {}
        self.GAME_SPEED = 2 
        self.pac = (0, 0)

    def __nonzero__(self):
        return self._running

    def start(self):
        logger.debug("Reset world")
        self._running = True
        self._step = 0 

    def stop(self):
        self._running = False

    def quit(self):
        logger.debug("Quit")
        self._running = False

    def keypress(self, key):
        logger.debug("Key = {}".format(key))
        x, y = self.pac
        if key == "w":
            y-=1
        elif key == "a":
            x-=1
        elif key == "s":
            y+=1
        elif key == "d":
            x+=1
        self.pac = (x, y)

    async def next_frame(self):
        await asyncio.sleep(1./self.GAME_SPEED)
        
        if not self._running:
            logging.info("Waiting for player 1")
            return

        self._step += 1
        logger.debug("Step {}".format(self._step))
   
        self._state = {"Step": self._step, "pacman": self.pac, "ghosts": [(10, 10), (3,5)]}

    @property
    def state(self):
        return json.dumps(self._state)
