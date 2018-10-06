import asyncio
import json
import logging
from ghost import Ghost

logger = logging.getLogger('Game')
logger.setLevel(logging.DEBUG)

class Game:
    def __init__(self):
        self._running = False
        self._step = 0
        logger.info("Game()")
        self._state = {}
        self.GAME_SPEED = 2
        self.size = (32, 24)
        self.pac = (0, 0)
        self._key = None

    def __nonzero__(self):
        return self._running

    def start(self):
        logger.debug("Reset world")
        self._running = True
        self._step = 0
        #TODO init state with energy and boosts
        self._ghosts = [Ghost(32/2, 24/2, self._state) for g in range(0,2)]

    def stop(self):
        self._running = False

    def quit(self):
        logger.debug("Quit")
        self._running = False

    def keypress(self, key):
        logger.debug("Key = {}".format(key))
        self._key = key

    def update_pacman(self):
        x, y = self.pac
        if self._key == "w":
            y-=1
        elif self._key == "a":
            x-=1
        elif self._key == "s":
            y+=1
        elif self._key == "d":
            x+=1

        #TODO stop on walls
        self.pac = (x, y)

    async def next_frame(self):
        await asyncio.sleep(1./self.GAME_SPEED)
        
        if not self._running:
            logging.info("Waiting for player 1")
            return

        self._step += 1
        logger.debug("Step {}".format(self._step))
  
        self.update_pacman()
        for ghost in self._ghosts:
            ghost.update(self._state)

        self._state = {"Step": self._step,
                       "pacman": self.pac,
                       "ghosts": [g.pos for g in self._ghosts],
                       "energy": [],
                       "boost": [],
                       }

    @property
    def state(self):
        return json.dumps(self._state)
