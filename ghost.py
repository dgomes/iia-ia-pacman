"""
Ghost with multiple levels of difficulty:
    Level 0 (Easy):
     - Visibility of 3 (twice when running away)
     - When in Zombie runs away in a random direction
     - Ignores Memory (Buffer) when running away

    Level 1 (Medium):
     - Visibility of 6 (capable of maintaining chase even when the pacman changes direction)
     - Runs away in the opposite direction of the pacman
     - Maintains Memory of the previous positions

    Level 2 (Hard):
     - Visibility of 9 (twice the medium)
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
    def __init__(self, max_size=8):
        self.buff = []
        self.max_size = max_size
        
    def valid(self, pos):
        return len([x for x in self.buff if x == pos]) == 0

    def add(self, pos):
        if self.valid(pos):
            self.buff += [pos]

        if len(self.buff) > self.max_size:
            self.buff = self.buff[1:]

    def __str__( self ):
        return str(self.buff)


class Ghost:
    def __init__(self, id, mapa, level=1, respawn_dist=3):
        self.map = mapa
        self.respawn()
        self.direction = ""
        self.respawn_dist = respawn_dist
        self.buffer = Buffer()
        self.plan = []
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

    def visible(self, g_pos, p_pos):
        visibility = 2*self.visibility if self.zombie else self.visibility
        return distance(p_pos, g_pos) <= visibility

    def directions(self, p_pos, g_pos):
        dirs = ['w', 's','a','d']
        
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
                
        return dirs

    def reverse_directions(self, p_pos, g_pos):
        dirs = self.directions(p_pos, g_pos)
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

    def find_exit(self, pos, actlist, visited):
        dirs = ['w', 's', 'a', 'd']
        dist = distance(pos, self.map.ghost_spawn)

        if dist > self.respawn_dist:
            return actlist
        else:
            random.shuffle(dirs)
            visited += [pos]
            for d in dirs:
                npos = self.map.calc_pos(pos, d)
                if npos != pos and not npos in visited:
                    rv = self.find_exit(npos, actlist + [d], visited)
                    if rv is not None:
                        return rv
            return None

    def find_path(self, pos, target, lghosts, depth, max_depth, actlist, visited, close=3):        
        visited += [pos]

        if pos in lghosts:
            dirs = reverse_directions(target, pos)
        else:
            dirs = self.directions(target, pos)


        if pos == target:
            return actlist
        elif depth > (max_depth/2) and distance(pos, target) < close:
            return actlist
        elif depth >= max_depth:
            return []
        else:
            for d in dirs:
                npos = self.map.calc_pos(pos, d)
                if npos != pos and not npos in visited and npos not in lghosts:
                    rv = self.find_path(npos, target, lghosts, depth+1, max_depth, actlist + [d], visited)
                    if len(rv) > 0:
                        return rv
            return []

    def random_valid_direction(self, pos, lghosts):
        direction = self.direction
        npos = self.map.calc_pos(pos, direction)
        if npos != pos and npos not in lghosts:
            return direction
        else:
            dirs = ['w', 's', 'a', 'd']
            random.shuffle(dirs)
            for d in dirs:
                npos = self.map.calc_pos(pos, d)
                if npos != pos and npos not in lghosts:
                    return d
            return dirs[0]

    def reverse_valid_direction(self, g_pos, p_pos, lghosts):
        dirs = self.reverse_directions(p_pos, g_pos)
        for d in dirs:
            npos = self.map.calc_pos(g_pos, d)
            if npos != g_pos and npos not in lghosts:
                return d
        return dirs[0]  
    
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
                    logger.debug("Ghost State = Leaving")
                    if len(self.plan) == 0:
                        self.plan = self.find_exit(g_pos, [], [])
                    self.direction = self.plan.pop(0)
                elif self.zombie:
                    logger.debug("Ghost State = Zombie")
                    if self.level == Level.Easy:
                        self.direction = self.random_valid_direction(g_pos, lghosts)
                    else:
                        self.direction = self.reverse_valid_direction(g_pos, p_pos, lghosts)
                elif self.visible(p_pos, g_pos) and not self.zombie:
                    logger.debug("Ghost State = Tracking")
                    mdepth = int(distance(g_pos, p_pos) * 1.5)
                    self.plan = self.find_path(g_pos, p_pos, lghosts, 0, mdepth, [], [])
                    logger.debug("Plan = %s", self.plan)
                    if len(self.plan) > 0:
                        self.direction = self.plan.pop(0)
                    else:
                        self.direction = self.random_valid_direction(g_pos, lghosts)
                else:
                    logger.debug("Ghost State = Looking")
                    self.direction = self.random_valid_direction(g_pos, lghosts)
                
                logger.debug("Ghost Direction = %s", self.direction)
                self.buffer.add(self.map.calc_pos((self.x, self.y), self.direction))
                # Update new position
                self.x, self.y = self.map.calc_pos((self.x, self.y), self.direction)
    
    def __str__(self):
        return "({}, {})".format(self.x, self.y)

    __repr__ = __str__
