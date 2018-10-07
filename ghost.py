import random
import logging

logger = logging.getLogger('Ghost')
logger.setLevel(logging.DEBUG)

class Ghost:
    def __init__(self, pos):
        x, y = pos
        self.x = x
        self.y = y

    @property
    def pos(self):
        return self.x, self.y

    def update(self, state):

        #TODO avoid walls
        #TODO seek and destroy pacman
        #TODO runaway
        nx, ny = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
        self.x, self.y = self.x + nx, self.y + ny

    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    __repr__ = __str__
