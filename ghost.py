"""
Ghost with multiple levels of difficulty:
    Level 0 (Easy):
     - Visibility of 8 (twice when running away)
     - When in Zombie runs away in a random direction
     - Ignores Memory (Buffer) when running away

    Level 1 (Medium):
     - Visibility of 16 (capable of maintaining chase even when the pacman changes direction)
     - Runs away in the opposite direction of the pacman
     - Maintains Memory of the previous positions

    Level 2 (Hard):
     - Visibility of 32 (twice the medium)
     - Runs away in the opposite direction of the pacman
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

logger = logging.getLogger('Ghost')
logger.setLevel(logging.INFO)


def scaling(scores, a=0.01, b=1.0):
    minimum = min(scores)
    maximum = max(scores)
    d = (maximum - minimum)
    if d > 0:
        for i in range(len(scores)):
            scores[i] = (b - a) * ((scores[i] - minimum) / d) + a
    else:
        for i in range(len(scores)):
            scores[i] = (b - a) * (scores[i] - minimum) + a
    return scores


def distance_2_score(distances):
    maximum = max(distances)
    for i in range(len(distances)):
        distances[i] = maximum - distances[i]
    return scaling(distances)


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
    Ultra = 3

class Buffer:
    def __init__(self, _map, max_size=32):
        self.buff=[]
        self.max_size = max_size
        self.map = _map
        
    def scores(self, pos, dirs):
        scores = [1.0, 1.0, 1.0, 1.0]

        if len(self.buff) > 0:
            distances = [0, 0, 0, 0]
            for i in range(len(dirs)):
                npos = self.map.calc_pos(pos, dirs[i])
                if npos == pos:
                    scores[i] = 0.0
                else:
                    value = [x[1] for x in self.buff if x[0] == npos]
                    if len(value) > 0:
                        distances[i] = value[0]
            distances = distance_2_score(distances)
            for i in range(len(dirs)):
                if scores[i] > 0.0:
                    scores[i] = distances[i]
        else:
            for i in range(len(dirs)):
                npos = self.map.calc_pos(pos, dirs[i])
                if npos == pos:
                    scores[i] = 0.0
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
    def __init__(self, mapa, level=1, wait_max=20, respawn_dist=3):
        self.map = mapa
        self.respawn()
        self.direction = ""
        self.respawn_dist = respawn_dist
        self.buffer = Buffer(mapa)
        self.plan = []

        if level <= 0:
            self.level = Level.Easy
            self.visibility = 8
        elif level == 1:
            self.level = Level.Medium
            self.visibility = 16
        else:
            self.level = Level.Hard
            self.visibility = 32

        self.wait = random.randint(0, wait_max)
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

    def visible(self, g_pos, p_pos):
        visibility = 2*self.visibility if self.zombie else self.visibility
        return distance(p_pos, g_pos) <= visibility

    def directions(self, p_pos, g_pos):
        dirs = ['w', 's','a','d']

        if (not self.zombie and not self.visible(g_pos, p_pos)) or (self.zombie and self.level is Level.Easy) or (self.zombie and not self.visible(g_pos, p_pos)):
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
        if len(lghosts) > 1:
            distance_ghosts = []
            for d in dirs:
                n_pos = self.map.calc_pos(g_pos, d)
                distance_ghosts.append(min([distance(x, n_pos) for x in lghosts]))
            score_g = scaling(distance_ghosts)
        return score_g

    def find_exit(self, pos, actlist, visited):
        dirs = ['w', 's', 'a', 'd']
        dist = distance(pos, self.map.ghost_spawn)

        if dist > self.respawn_dist:
            return actlist
        else:
            random.shuffle(dirs)
            visited += [pos]
            for d in dirs:
                npos = npos = self.map.calc_pos(pos, d)
                if npos != pos and not npos in visited:
                    rv = self.find_exit(npos, actlist + [d], visited)
                    if rv is not None:
                        return rv
            return None

    def wall_scores(self, g_pos, dirs):
        scores = [1.0, 1.0, 1.0, 1.0]
        for i in range(len(dirs)):
            npos = self.map.calc_pos(g_pos, dirs[i])
            if npos == g_pos:
                scores[i] = 0.0
        return scores
                
    def scores(self, g_pos, p_pos, dirs, lghosts):
        logger.debug("PACMAN DIRS = %s", dirs)
        scores_d = [1.0, .75, .5, .25]
        scores_g = self.ghost_scores(g_pos, dirs, lghosts)
        logger.debug("GHOST SCORES = %s", scores_g)
        
        if self.zombie:
            scores_w = self.wall_scores(g_pos, dirs)
            logger.debug("WALL SCORES = %s", scores_w)
            scores = combine_scores(4, scores_d, scores_w)
        else:
            scores_b = self.buffer.scores(g_pos, dirs)
            logger.debug("BUFFER SCORES = %s", scores_b)
            scores = combine_scores(4, scores_d, scores_b, scores_g)

        logger.debug("FINAL SCORES = %s", scores)
        return scores
    
    def update(self, state):
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
                lghosts = [x[0] for x in state['ghosts'] if x[0] != g_pos]
                logger.debug("GHOST L_GST = %s", lghosts)
                
                if distance(g_pos, self.map.ghost_spawn) <= self.respawn_dist and distance(p_pos, self.map.ghost_spawn) > self.respawn_dist:
                    logger.debug("Ghost State = Close to respawn")
                    if len(self.plan) == 0:
                        self.plan = self.find_exit(g_pos, [], [])
                    self.direction = self.plan.pop(0)
                else:
                    logger.debug("Ghost State = Track")
                    # Find the right direction
                    dirs = self.directions(p_pos, g_pos)
                    # Compute the scores of each direction based on the buffer
                    scores = self.scores(g_pos, p_pos, dirs, lghosts)
                    # Use the maximum score
                    idx = scores.index(max(scores))
                    self.direction = dirs[idx]
                    self.buffer.add(g_pos)

                logger.debug("GHOST FINAL DIRS  = %s", self.direction)
                logger.debug("")
                # Update new position
                self.x, self.y = self.map.calc_pos((self.x, self.y), self.direction)
    
    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    __repr__ = __str__
