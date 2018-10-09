import asyncio
import json
import logging
from ghost import Ghost
from mapa import Map, Tiles

logger = logging.getLogger('Game')
logger.setLevel(logging.DEBUG)

GHOSTS = 3
LIVES = 3
POINT_ENERGY = 1
POINT_BOOST = 10
POINT_GHOST = 50
BOOST_TIMEOUT = 30
INITIAL_SCORE = 10000
GAME_SPEED = 5 

class Game:
    def __init__(self, mapfile, n_ghosts=GHOSTS, lives=LIVES):
        logger.info("Game()")
        self._running = False
        self._state = {}
        self._n_ghosts = n_ghosts
        self._initial_lives = lives
        self.map = Map(mapfile)

    def info(self):
        return json.dumps({"map": self.map.filename,
                           "ghosts": self._n_ghosts,
                            })

    def consume(self, pos):
        """Update map at position."""
        if pos in self._energy:
            self._energy.remove(pos)
            return Tiles.ENERGY 
        if pos in self._boost:
            self._boost.remove(pos)
            return Tiles.BOOST

    @property
    def running(self):
        return self._running

    @property
    def score(self):
        return self._score

    def start(self):
        logger.debug("Reset world")
        self._running = True
        
        self.map = Map(self.map.filename)
        self._step = 0
        self._ghosts = [Ghost(self.map) for g in range(0,self._n_ghosts)]
        self._pacman = self.map.pacman_spawn
        self._energy = self.map.energy
        self._boost = self.map.boost
        self._super = False
        self._lastkeypress = "d" 
        self._score = INITIAL_SCORE 
        self._lives = self._initial_lives 

    def stop(self):
        logging.info("GAME OVER")
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

    def collision(self):
        for g in self._ghosts:
            if g.pos == self._pacman:
                if self._super:
                    self._score += POINT_GHOST
                    g.respawn()
                else:
                    logging.info("DEAD")
                    if self._lives:
                        self._lives -= 1
                        self._pacman = self.map.pacman_spawn
                        g.respawn()
                    if not self._lives:
                        self.stop()
                        return

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
        self.collision()
       
        for ghost in self._ghosts:
            ghost.update(self._state)
        self.collision()
        
        self._state = {"step": self._step,
                       "score": self._score,
                       "lives": self._lives,
                       "super": self._super > 0,  # True -> pacman can eat ghosts
                       "pacman": self._pacman,
                       "ghosts": [g.pos for g in self._ghosts],
                       "energy": self._energy,
                       "boost": self._boost,
                       }

    @property
    def state(self):
        return json.dumps(self._state)
