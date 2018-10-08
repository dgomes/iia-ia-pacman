import pygame
import logging
from enum import Enum


WALL = 0xff000000
ENERGY = 0xffffd7d6
BOOST = 0xffff2600
PACMAN = 0xffd4fdd5
GHOST = 0xff00f900

class Tiles(Enum):
    ENERGY = 1
    BOOST = 3

class Map:
    def __init__(self, filename):
        self._filename = filename
        image = pygame.image.load(filename)
        self.pxarray = pygame.PixelArray(image)
        self.hor_tiles=len(self.pxarray)
        self.ver_tiles=len(self.pxarray[0])

        self._energy = []
        self._boost = []

        for x in range(self.hor_tiles):
            for y in range(self.ver_tiles):
                p = self.pxarray[x][y] 
                
                if p == ENERGY: 
                    self._energy.append((x,y))
                elif p == BOOST: 
                    self._boost.append((x,y))
                elif p == PACMAN:
                    self._pacman_spawn = (x, y)
                elif p == GHOST:
                    self._ghost_spawn = (x, y)

                #logging.debug("{}, {}   {:x}".format(x, y, p))


    @property
    def filename(self):
        return self._filename

    @property
    def size(self):
        return self.hor_tiles, self.ver_tiles 

    @property
    def energy(self):
        return self._energy

    @property
    def boost(self):
        return self._boost

    @property
    def pacman_spawn(self):
        return self._pacman_spawn

    @property
    def ghost_spawn(self):
        return self._ghost_spawn

    def is_wall(self, pos):
        x, y = pos
    #    logging.debug("{} {:x}".format(pos, self.pxarray[x][y] ))
        if self.pxarray[x][y] == WALL:
            return True
        return False

    def calc_pos(self, cur, direction):
        assert direction in "wasd"

        cx, cy = cur
        npos = cur
        if direction == 'w':
            npos = cx, cy-1
        if direction == 'a':
            npos = cx-1, cy
        if direction == 's':
            npos = cx, cy+1
        if direction == 'd':
            npos = cx+1, cy

        #wrap map
        nx, ny = npos
        if nx < 0:
            nx = self.hor_tiles-1
        if nx == self.hor_tiles:
            nx = 0
        if ny < 0:
            ny = self.ver_tiles-1
        if ny == self.ver_tiles:
            ny = 0
        npos = nx, ny 

        #test wall
        if self.is_wall(npos):
            return cur
   
        return npos
    
