import random
import logging
from mapa import Map

logger = logging.getLogger('Ghost')
logger.setLevel(logging.DEBUG)

class Ghost:
    def __init__(self, pos, mapa):
        x, y = pos
        self.x = x
        self.y = y
        self.map = mapa
        self.direction = "a"
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
