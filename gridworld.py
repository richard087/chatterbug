from dataclasses import dataclass
import logging
import json
from typing import List, Tuple, Any, AnyStr
import jsonpickle

class Grid:
    '''A playing grid. A puzzle room, or a chess board, etc.'''
    def __init__(self, width:int=1, height:int=1):
        if width < 1 or height < 1:
            raise ValueError(f"Minimum value for dimensions is 1. Received width={width} and height={height}")
        self._grid = [[self.Tile(tile_colour='white', contains=None, coordinates=(x,y)) for y in range(height)] for x in range(width)]

    def _transpose(self) -> List[List]:
        '''return row-wise'''
        result = []
        for y in range(len(self._grid[0])): # grid is rectangular so this is safe
            row = []
            for x in range(len(self._grid)):
                row.append(self._grid[x][y])
            result.append(row)
        return result
    
    def add_object(self, coords:Tuple[int,int], object):
        '''Put an object on a particular position on the board. Each position may only have one object'''
        if self._grid[coords[0]][coords[1]].contains is not None:
            raise Exception(f"Position {coords} already has an object {self._grid[coords[0]][coords[1]].contains}")
        self._grid[coords[0]][coords[1]].contains = object
    
    def move_object(self, from_coords:Tuple[int,int], to_coords:Tuple[int,int]):
        '''Move an object in one position, to some other position, on the grid.'''
        self.add_object(to_coords, self._grid[from_coords[0]][from_coords[1]].contains)
        self.remove_object(from_coords)
    
    def remove_object(self, coords:Tuple[int,int]):
        '''Replaces an object at a location on the grid with None'''
        self._grid[coords[0]][coords[1]].contains = None
    
    def get_object(self, coords:Tuple[int,int]):
        '''Returns a refernce to the object at a location on the grid'''
        return self._grid[coords[0]][coords[1]].contains
    
    def set_tile_colour(self, coords:Tuple[int,int], colour):
        '''Sets the colour of a given position on the grid. Often used to communicate something about this location.'''
        self._grid[coords[0]][coords[1]].tile_colour = colour
    
    def where_is(self, something) -> List[Tuple[int,int]]:
        '''Linear search of the grid for all occurences of "something"'''
        result = []
        for x in range(len(self._grid)):
            for y in range(len(self._grid[x])):
                if self._grid[x][y].contains is something:
                    result.append((x,y))
        return result

    def to_json(self) -> AnyStr:
        return jsonpickle.encode(self._transpose(), unpicklable = False)

    @dataclass
    class Tile:
        coordinates:Tuple[int,int] = (0,0)
        classname:str = 'Tile'
        tile_colour:str = 'white'
        contains:Any = None


    @dataclass
    class Door:
        '''An object with a colour (default = 'white') and a state (default = 'closed')'''
        classname:str = 'Door'
        colour:str = 'white'
        state:str = 'closed'
        classname:str = 'Door'


    @dataclass
    class Player:
        '''An object with a name (default = 'anonymous')'''
        classname:str = 'Player'
        name:str = 'anonymous'


if __name__ == '__main__':
    g = Grid(height=3, width=2)
    p = g.Player(name='Bob')
    g.add_object((0, 0), g.Door(colour='blue'))
    g.add_object((1, 2), p)
    g.set_tile_colour((0, 2), 'blue')
    person_coords = g.where_is(p)[0]
    #g.move_object(person_coords, (0, 0)) # should throw an exception
    print(g.to_json())
    #print(person_coords)
