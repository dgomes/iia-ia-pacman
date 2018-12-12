"""
Ghost with multiple levels of digiculty:
    Level 0 (Easy):
     - Visibility of 2 (twice when running away)
     - When in Zombie runs away in a random direction
     - Ignores Memory (Buffer) when running away

    Level 1 (Medium):
     - Visibility of 4 (capable of maintaining chase even when the pacman changes direction)
     - Runs away in the oposite direction of the pacman
     - Maintains Memory of the previous positions

    Level 2 (Hard):
     - Visibility of 8 (twice the medium)
     - Runs away in the oposite direction of the pacman
     - Maintains memory of the previous positions
     - Gives priority to spreading (go away from other ghosts)
"""
__author__ = "Mário Antunes"
__version__ = "2.0"
__email__ = "mario.antunes@ua.pt"

import random
import math
import logging
from enum import Enum
from mapa import Map

logger = logging.getLogger('Ghost1')
logger.setLevel(logging.INFO)


def combine_scores(l, *args):
    scores = []
    for i in range(0, l):
        score = 1.0
        for a in args:
            score *= a[i]
        scores.append(score)
    return scores


def distance(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


# Enum of levels
class Level(Enum):
    Easy = 0
    Medium = 1
    Hard = 2

# position buffer
class Buffer:
    def __init__(self, _map, max_size=3):
        self.buff=[]
        self.max_size = max_size
        self.map = _map

    def scores(self, pos, dirs):
        scores = []
        for d in dirs:
            n_pos = self.map.calc_pos(pos, d)
            if n_pos == pos:
                scores.append(0.0)
            else:
                if len(self.buff) == 0:
                    scores.append(1.0)
                else:
                    m = max([x[1] for x in self.buff])
                    op = [x for x in self.buff if x[0] == n_pos]
                    if len(op) == 0:
                        scores.append(1.0)
                    else:
                        scores.append(1.0-(op[0][1]/m))
        return scores

    def add(self, pos):
        op = [x for x in self.buff if x[0] == pos]
        if len(op) == 0:
            self.buff.append((pos, 1))
        else:
            self.buff.remove(op[0])
            self.buff.append((op[0][0], op[0][1]+1.0))

        self.buff.sort(key=lambda x: x[1], reverse=True)
        if len(self.buff) > self.max_size:
            self.buff = self.buff[1:]

    def __str__( self ):
        return str(self.buff)

class Ghost:
    def __init__(self, id, mapa, level=1):
        self.map = mapa
        self.respawn()
        self.direction = ""
        self.buffer = Buffer(mapa, 16)
        self.identity = id

        if level <= 0:
            self.level = Level.Easy
            self.visibility = 2
        elif level == 1:
            self.level = Level.Medium
            self.visibility = 4
        else:
            self.level = Level.Hard
            self.visibility = 8

        self.wait = id
        self.zombie_timeout = 0

        logger.info("Ghost Level = %s ", self.level)
        logger.info("Ghost Visibility = %s", self.visibility)

    def respawn(self):
        x, y = self.map._ghost_spawn
        self.x = x
        self.y = y 
        self.zombie_timeout = 0

    def make_zombie(self, timeout):
        '''Ghost will be vulnerable during a timeout.'''
        self.zombie_timeout = timeout

    @property
    def zombie(self):
        return self.zombie_timeout > 0

    @property
    def pos(self):
        return self.x, self.y

    def directions(self, p_pos, g_pos):
        dirs = ['w', 's','a','d']

        visibility = 2*self.visibility if self.zombie else self.visibility

        if (not self.zombie and distance(p_pos, g_pos) > visibility) or (self.zombie and self.level is Level.Easy) or (self.zombie and distance(p_pos, g_pos) > visibility):
            theta = random.choice([0, 45, 90, 135, 180, -45, -90, -135, -180])
        else:
            theta = round(math.degrees(math.atan2((p_pos[1] - g_pos[1]), (p_pos[0] - g_pos[0]))))
        
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
                
        return self.reverse_directions(dirs) if self.zombie else dirs

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

    def ghost_scores(self, g_pos, dirs, lghosts):
        score_g = [1.0, 1.0, 1.0, 1.0]

        if len(lghosts) > 0:
            for d in dirs:
                n_pos = self.map.calc_pos(g_pos, d)
                score_g.append(min([distance(x, n_pos) for x in lghosts]))
            m = max(score_g)
            if m > 0:
                if self.level is Level.Hard:
                    score_g = [2.0 * (x/m) for x in score_g]
                else:
                    score_g = [x/m for x in score_g]
        return score_g 

    def scores(self, g_pos, dirs, lghosts):
        scores_d = [1.0, .5, .25, .125]
        scores_b = self.buffer.scores(g_pos, dirs)
        scores_g = self.ghost_scores(g_pos, dirs, lghosts)
        
        scores = []
        if self.zombie and self.level is Level.Easy:
            scores = combine_scores(4, scores_d, scores_g)
        else:
            scores = combine_scores(4, scores_d, scores_b, scores_g)

        logger.debug("GHOST SCORES = %s", scores)
        return scores
    
    def update(self, state, ghosts):
        if self.zombie:
            self.zombie_timeout-=1
            #if zombie we move at HALF speed by skipping steps
            if state['step'] % 2 == 0:
                return
        if self.wait > 0:
            self.wait -= 1
        else:
            if 'pacman' in state:
                p_pos = state['pacman']
                g_pos = (self.x, self.y)
                # Find the other ghosts
                #lghosts = [(x.x, x.y) for x in ghosts if x.identity != self.identity]
                lghosts = [x[0] for x in state['ghosts'] if x[0] != g_pos]
                logger.debug("GHOST L_GST = %s", lghosts)
                # Find the right direction
                dirs = self.directions(p_pos, g_pos)
                logger.debug("GHOST DIRS = %s", dirs)
                # Compute the scores of each direction based on the buffer
                scores = self.scores(g_pos, dirs, lghosts)
                # Use the maximum score
                idx = scores.index(max(scores))
                self.direction = dirs[idx]
                logger.debug("GHOST DIRS  = %s", self.direction)
                # Update new position
                self.buffer.add(g_pos)
                logger.debug("GHOST BUFF = %s", self.buffer)
                self.x, self.y = self.map.calc_pos((self.x, self.y), self.direction)
    
    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    __repr__ = __str__
