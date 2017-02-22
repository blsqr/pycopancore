"""Define base.cell class.

In this module the basic Cell mixing class is composed to set the basic
structure for the later in the model used Cell class. It Inherits from Cell_
in that basic variables and parameters are defined.
"""
# This file is part of pycopancore.
#
# Copyright (C) 2016 by COPAN team at Potsdam Institute for Climate Impact
# Research
#
# URL: <http://www.pik-potsdam.de/copan/software>
# License: MIT license

#
#  Imports
#

from pycopancore.model_components import abstract
from .interface import Cell_
#
#  Define class Cell
#


class Cell(Cell_, abstract.Cell):
    """Define properties of base.cell.

    Basic Cell mixin class that every model must use in composing their Cell
    class. Inherits from Cell_ as the interface with all necessary variables
    and parameters.
    """

    # standard methods:

    def __init__(self,
                 *,
                 location=(0, 0),
                 area=1,
                 society=None,
                 geometry=None,
                 **kwargs
                 ):
        """Initialize an instance of Cell.

        Parameters
        ----------
        location
        area
        society
        geometry
        kwargs
        """
        super().__init__(**kwargs)

        assert location is not None
        self.location = location

        assert area > 0, "area must be > 0"
        self.area = area

        self.society = society

        self.geometry = geometry


    # setters for references:
    
    @world.setter
    def world(self, w):
        assert isinstance(w, World_)
        if self.world is not None: self.world.cells.remove(self) 
        w.cells.add(self) 
        self.world = w


    processes = []
