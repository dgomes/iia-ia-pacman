import random
import logging
from mapa import Map

logger = logging.getLogger('Ghost')
logger.setLevel(logging.DEBUG)

class Ghost:
    def __init__(self, mapa):
        self.map = mapa
        self.respawn()
        self.direction = "a"

    def respawn(self):
        x, y = self.map._ghost_spawn
        self.x = x
        self.y = y 

    @property
    def pos(self):
        return self.x, self.y

    def update(self, state):

        #TODO seek and destroy pacman
        #TODO runaway
        n_pos = self.map.calc_pos((self.x, self.y), self.direction)
        if n_pos == (self.x, self.y):
            self.direction = random.choice("wasd")
        else:
            self.x, self.y = n_pos
    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    __repr__ = __str__
