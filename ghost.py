import random
import math
import logging
from mapa import Map

logger = logging.getLogger('Ghost')
logger.setLevel(logging.DEBUG)

class Ghost:
    def __init__(self, mapa, buff_size=9, wait_max=10):
        self.map = mapa
        self.respawn()
        self.direction = ""
        self.buff_size = buff_size
        self.buff_pos = []
        self.wait = random.randint(0, wait_max)

    def respawn(self):
        x, y = self.map._ghost_spawn
        self.x = x
        self.y = y 

    @property
    def pos(self):
        return self.x, self.y

    def directions(self, p_pos, g_pos):
        theta = round(math.degrees(math.atan2((p_pos[1] - g_pos[1]),
            (p_pos[0] - g_pos[0]))))
        if theta >= 45 and theta < 135:
            if theta <= 90:
                dirs = ['s','d','a','w']
            else:
                dirs = ['s','a','d','w']
        elif theta >= -135 and theta < -45:
            if theta >= -90:
                dirs = ['w', 'd', 'a', 's']
            else:
                dirs = ['w', 'a', 'd', 's']
        elif theta > 135:
            dirs = ['a', 's', 'w', 'd']
        elif theta < -135:
            dirs = ['a', 'w', 's', 'd']
        elif theta < 45:
            dirs = ['d', 's', 'w', 'a']
        else:
            dirs = ['d', 'w', 's', 'a']
        return dirs

    def scores(self, g_pos, dirs):
        score_d = [1.0, .5, .25, .125]
        score_b = []

        for d in dirs:
            n_pos = self.map.calc_pos(g_pos, d)
            if n_pos == g_pos:
                # WALL
                score_b.append(0.0)
            else:
                if len(self.buff_pos) == 0:
                    score_b.append(1.0)
                else:
                    m = max([x[1] for x in self.buff_pos])
                    op = [x for x in self.buff_pos if x[0] == n_pos]
                    if len(op) == 0:
                        score_b.append(1.0)
                    else:
                        score_b.append(1.0-(op[0][1]/m))
                        #score_b.append(1.0/(op[0][1]+1))
        logger.debug("GHOST SCBU = "+str(score_b))
        return [x*y for x,y in zip(*([score_d, score_b]))]
        #return [(x+y)/2.0 for x,y in zip(*([score_d, score_b]))]

    def update_buffer(self, g_pos):
        n_pos = self.map.calc_pos(g_pos, self.direction)
        op = [x for x in self.buff_pos if x[0] == n_pos]
        if len(op) == 0:
            self.buff_pos.append((n_pos, 1))
        else:
            self.buff_pos.remove(op[0])
            self.buff_pos.append((op[0][0], op[0][1]+1.0))

        self.buff_pos.sort(key=lambda x: x[1], reverse=True)
        if len(self.buff_pos) > self.buff_size:
            self.buff_pos = self.buff_pos[1:]

    def reverse_directions(self, dirs):
        rv = []
        for x in dirs:
            if x == 'w':
                rv.append('s')
            elif x == 'a':
                rv.append('d')
            elif x == 's':
                rv.append('w')
            else:
                rv.append('a')
        return rv


    def update(self, state):
        if self.wait > 0:
            self.wait -= 1
        else:
            if 'pacman' in state:
                p_pos = state['pacman']
                g_pos = (self.x, self.y)
                # Find the right direction
                dirs = self.directions(p_pos, g_pos)
                if state['super'] is True:
                    dirs = self.reverse_directions(dirs)
                    logging.debug("GHOST RUN AWAY...")
                logger.debug("GHOST DIRS = "+str(dirs))
                # Compute the scores of each direction based on the buffer
                scores = self.scores(g_pos, dirs)
                logger.debug("GHOST COSC = "+str(scores))
                # Use the maximum score
                idx = scores.index(max(scores))
                self.direction = dirs[idx]
                logger.debug("GHOST DIR  = "+self.direction)
                # Update new position
                self.update_buffer(g_pos)
                logger.debug("GHOST BUFF = "+str(self.buff_pos))
                self.x, self.y = self.map.calc_pos((self.x, self.y), self.direction)
    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    __repr__ = __str__
