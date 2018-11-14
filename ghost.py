import random
import math
import logging
from mapa import Map

logger = logging.getLogger('Ghost')
logger.setLevel(logging.DEBUG)

class Ghost:
    def __init__(self, mapa, wait=10, buff_size=9, visibility_radius=3):
        self.map = mapa
        self.respawn()
        self.direction = ""
        self.wait = random.randint(0, wait)
        self.buff_size = buff_size
        self.buff_pos = []
        self.visibility_radius = visibility_radius 

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

    def buffer_scores(self, g_pos, dirs):
        score = []

        for d in dirs:
            n_pos = self.map.calc_pos(g_pos, d)
            if n_pos == g_pos:
                score.append(0.0)
            else:
                if len(self.buff_pos) == 0:
                    score.append(1.0)
                else:
                    m = max([x[1] for x in self.buff_pos])
                    op = [x for x in self.buff_pos if x[0] == n_pos]
                    if len(op) == 0:
                        score.append(1.0)
                    else:
                        score.append(1.0-(op[0][1]/m))
        return score

    def dirs_scores(self, g_pos, dirs):
        score_d = [1.0, .5, .25, .125]
        score_b = self.buffer_scores(g_pos, dirs)
        return [x*y for x,y in zip(*([score_d, score_b]))]

    def ghosts_scores(self, g_pos, dirs, lghosts, scores):
        score_g = []
            
        if len(lghosts) > 0:
            for d in dirs:
                n_pos = self.map.calc_pos(g_pos, d)
                score_g.append(min([self.distance(x, n_pos) for x in lghosts]))
            m = max(score_g)
            if m > 0:
                score_g = [x/m for x in score_g]
        else:
            return scores
        return [x*y for x,y in zip(*([scores, score_g]))]

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

    def distance(self, p_pos, g_pos):
        return abs(p_pos[0] - g_pos[0]) + abs(g_pos[1] - g_pos[1])

    def update(self, state):
        if self.wait > 0:
            self.wait -= 1
        else:
            if 'pacman' in state:
                p_pos = state['pacman']
                g_pos = (self.x, self.y)

                # Search other ghosts
                lghosts = state['ghosts']
                logger.debug("GHOST L_GST = "+str(lghosts))
                if g_pos in lghosts: 
                    lghosts.remove(g_pos)
                
                # Distance to the Ghost
                logger.debug("GHOST DSTC = "+str(self.distance(p_pos, g_pos)))

                if self.distance(p_pos, g_pos) <= self.visibility_radius:
                    # Find the right direction
                    dirs = self.directions(p_pos, g_pos)
                    if state['super'] is True:
                        #dirs = self.reverse_directions(dirs)
                        logger.debug("GHOST RUN AWAY...")
                        dirs = ['w','s','a','d']
                        random.shuffle(dirs)
                    logger.debug("GHOST DIRS = "+str(dirs))
                    # Compute the scores of each direction based on the buffer
                    scores = self.dirs_scores(g_pos, dirs)
                    logger.debug("GHOST COSC = "+str(scores))
                else:
                    # Compute the scores based only on the buffer
                    dirs = ['w','s','a','d']
                    random.shuffle(dirs)
                    scores = self.buffer_scores(g_pos, dirs)
                # Run away from other ghosts
                scores = self.ghosts_scores(g_pos, dirs, lghosts, scores)
                logger.debug("GHOST SCRS = "+str(scores))
                # Use the maximum score
                idx = scores.index(max(scores))
                self.direction = dirs[idx]
                logger.debug("GHOST DIRS  = "+self.direction)
                # Update new position
                self.update_buffer(g_pos)
                logger.debug("GHOST BUFF = "+str(self.buff_pos))
                self.x, self.y = self.map.calc_pos((self.x, self.y), self.direction)
    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    __repr__ = __str__
