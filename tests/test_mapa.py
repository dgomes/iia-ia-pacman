import pytest

from mapa import Map

def test_image_load():
    m = Map("data/map1.png")
    assert 19, 31 == m.size
    assert 3, 16 == m._pacman_start

