import math
import os
import asyncio
import json
import logging
from ghost1 import Ghost as Ghost1
from ghost2 import Ghost as Ghost2
from mapa import Map, Tiles

logger = logging.getLogger('Game')
logger.setLevel(logging.DEBUG)

GHOSTS = 3
LIVES = 3
POINT_ENERGY = 1
POINT_BOOST = 10
POINT_GHOST = 50
POINT_TIME_BONUS = 1
BOOST_TIMEOUT = 30
INITIAL_SCORE = 0
TIME_BONUS_STEPS = 5
TIMEOUT = 3000 
GAME_SPEED = 10 
MAX_HIGHSCORES = 10


class Game:
    def __init__(self, mapfile, n_ghosts=GHOSTS, l_ghosts=1, lives=LIVES, timeout=TIMEOUT):
        logger.info("Game({}, {}, {}, {})".format(mapfile, n_ghosts, l_ghosts, lives))
        self._running = False
        self._timeout = timeout
        self._state = {}
        self._n_ghosts = n_ghosts
        self._l_ghosts = l_ghosts
        self._initial_lives = lives
        self.map = Map(mapfile)
        
        self._highscores = [] 
        if os.path.isfile(mapfile+".score"):
            with open(mapfile+".score", 'r') as infile:
                self._highscores = json.load(infile)

    def info(self):
        return json.dumps({"map": self.map.filename,
                           "ghosts": self._n_ghosts,
                           "ghosts_level": self._l_ghosts,
                           "fps": GAME_SPEED,
                           "timeout": TIMEOUT,
                           "lives": LIVES,
                           "points": {"energy": POINT_ENERGY,
                                      "boost": POINT_BOOST,
                                      "ghost": POINT_GHOST,
                                      "time_bonus": POINT_TIME_BONUS},
                           "boost_timeout": BOOST_TIMEOUT,
                           "highscores": self.highscores,
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

    @property
    def highscores(self):
        return self._highscores

    def start(self, player_name):
        logger.debug("Reset world")
        self._player_name = player_name
        self._running = True
        
        self.map = Map(self.map.filename)
        self._step = 0
        if self._l_ghosts <=2:
            Ghost = Ghost1
        else:
            Ghost = Ghost2
        self._ghosts = [Ghost(i, self.map, level=self._l_ghosts) for i in range(0,self._n_ghosts)]
        self._pacman = self.map.pacman_spawn
        self._energy = self.map.energy
        self._boost = self.map.boost
        self._lastkeypress = "d" 
        self._score = INITIAL_SCORE 
        self._lives = self._initial_lives 

    def stop(self):
        logger.info("GAME OVER")
        self.save_highscores()
        self._running = False

    def quit(self):
        logger.debug("Quit")
        self._running = False

    def save_highscores(self):
        #update highscores
        logger.debug("Save highscores")
        logger.info("FINAL SCORE <%s>: %s", self._player_name, self.score)
        self._highscores.append((self._player_name, self.score))
        self._highscores = sorted(self._highscores, key=lambda s: -1*s[1])[:MAX_HIGHSCORES]
    
        with open(self.map._filename+".score", 'w') as outfile:
            json.dump(self._highscores, outfile)

    def keypress(self, key):
        self._lastkeypress = key

    def update_pacman(self):
        try:
            self._pacman = self.map.calc_pos(self._pacman, self._lastkeypress) 
        except AssertionError:
            logger.error("Invalid key <%s> pressed", self._lastkeypress)

        c = self.consume(self._pacman)
        if c == Tiles.ENERGY:
            self._score += POINT_ENERGY
        elif c == Tiles.BOOST:
            self._score += POINT_BOOST
            for g in self._ghosts:
                g.make_zombie(BOOST_TIMEOUT)

        if len(self._energy) + len(self._boost) == 0:
            logger.info("Level completed")
            self._score += ((self._timeout - self._step) // TIME_BONUS_STEPS) * POINT_TIME_BONUS 
            self.stop()

    def in_range(self, p1, p2, d):
        px, py = p1
        gx, gy = p2
        distance = math.hypot(px-gx, py-gy)
        return distance <= d

    def collision(self):
        for g in self._ghosts:
            if g.pos == self._pacman and self._running:
                if g.zombie:
                    self._score += POINT_GHOST
                    g.respawn()
                else:
                    logger.info("PACMAN has died")
                    if self._lives:
                        self._lives -= 1
                        self._pacman = self.map.pacman_spawn
                        g.respawn()
                        [gg.respawn() for gg in self._ghosts if self.in_range(self._pacman, gg.pos, 2)]
                    if not self._lives:
                        self.stop()
                        return

    async def next_frame(self):
        await asyncio.sleep(1./GAME_SPEED)

        if not self._running:
            logger.info("Waiting for player 1")
            return

        self._step += 1
        if self._step == self._timeout:
            self.stop()

        if self._step % 100 == 0:
            logger.debug("[{}] SCORE {} - LIVES {}".format(self._step, self._score, self._lives))
  
        self.update_pacman()
        self.collision()
       
        for ghost in self._ghosts:
            ghost.update(self._state, self._ghosts)
        self.collision()
        
        self._state = {"step": self._step,
                       "player": self._player_name,
                       "score": self._score,
                       "lives": self._lives,
                       "pacman": self._pacman,
                       "ghosts": [(g.pos, g.zombie, g.zombie_timeout) for g in self._ghosts],
                       "energy": self._energy,
                       "boost": self._boost,
                       }

    @property
    def state(self):
        return json.dumps(self._state)
