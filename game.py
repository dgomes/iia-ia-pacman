import asyncio
import json
import logging
from ghost import Ghost
from mapa import Map, Tiles

logger = logging.getLogger('Game')
logger.setLevel(logging.DEBUG)

POINT_ENERGY = 1
POINT_BOOST = 10
POINT_GHOST = 50
BOOST_TIMEOUT = 30
GAME_SPEED = 5 

class Game:
    def __init__(self):
        logger.info("Game()")
        self._running = False
        self._state = {}
        
        self.map = Map("data/map1.bmp")
       

    def consume(self, pos):
        """Update map at position."""
        if pos in self._energy:
            self._energy.remove(pos)
            return Tiles.ENERGY 
        if pos in self._boost:
            self._boost.remove(pos)
            return Tiles.BOOST

    def __nonzero__(self):
        return self._running

    def start(self):
        logger.debug("Reset world")
        self._running = True
        
        self._step = 0
        self._ghosts = [Ghost(self.map.ghost_spawn, self.map) for g in range(0,2)]
        self._pacman = self.map.pacman_spawn
        self._energy = self.map.energy
        self._boost = self.map.boost
        self._super = False
        self._lastkeypress = "d" 
        self._score = 10000
        self._lives = 3

    def stop(self):
        self._running = False

    def quit(self):
        logger.debug("Quit")
        self._running = False

    def keypress(self, key):
        self._lastkeypress = key

    def update_pacman(self):
        self._pacman = self.map.calc_pos(self._pacman, self._lastkeypress) 
        c = self.consume(self._pacman)
        if c == Tiles.ENERGY:
            self._score += POINT_ENERGY
        elif c == Tiles.BOOST:
            self._score += POINT_BOOST
            self._super = BOOST_TIMEOUT

        if self._pacman in self._ghosts:
            if self._super > 0:
                logging.debug("Ghost eaten")
                self._score += POINT_GHOST
                self._ghosts.remove(self._pacman)
                self._ghosts.add(Ghost(self.map.ghost_spawn))
            else:
                logging.debug("Dead")
                self._lives -= 1
                self.pacman = self.map.pacman_spawn

                #Avoid spawning on top of a ghost
                if self._pacman in self._ghosts:
                    self._ghosts.remove(self._pacman)
                    self._ghosts.add(Ghost(self.map.ghost_spawn))
        
    async def next_frame(self):
        await asyncio.sleep(1./GAME_SPEED)
        
        if not self._running:
            logging.info("Waiting for player 1")
            return

        self._step += 1
        if self._super > 0:
            self._super -= 1

        if self._step % 100 == 0:
            logger.debug("[{}] SCORE {} - LIVES {}".format(self._step, self._score, self._lives))
  
        self.update_pacman()
        for ghost in self._ghosts:
            ghost.update(self._state)

        self._state = {"step": self._step,
                       "score": self._score,
                       "super": self._super > 0,  # True -> pacman can eat ghosts
                       "pacman": self._pacman,
                       "ghosts": [g.pos for g in self._ghosts],
                       "energy": self._energy,
                       "boost": self._boost,
                       }

    @property
    def state(self):
        return json.dumps(self._state)
