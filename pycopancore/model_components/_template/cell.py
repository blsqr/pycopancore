"""Cell mixing class template.

It is composed to give an
example of the basic structure for the in the model used Cell class. It
Inherits from Cell_ in which variables and parameters are defined.
"""
# This file is part of pycopancore.
#
# Copyright (C) 2016 by COPAN team at Potsdam Institute for Climate
# Impact Research
#
# URL: <http://www.pik-potsdam.de/copan/software>
# License: MIT license

from .interface import * # import all interface classes since one typically wants to cross-ref variables between entity types (this is the whole point of having an interface in the first place)
from pycopancore.model_components import abstract


class Cell(Cell_, abstract.Cell):
    """Define your Cell class.

    A template for the basic structure of the Cell mixin class that every
    component may use to compose their Cell class.
    Inherits from Cell_ as the interface
    with all necessary variables and parameters.
    """

    # standard methods:
    
    def __init__(self,
                 # ,*,
                 **kwargs):
        """Initialize an instance of Cell."""
        super().__init__(**kwargs)
        # add custom code here:
        pass

    def __deactivate(self):
        """Deactivate a cell."""
        # add custom code here:
        pass
        super().__deactivate()

    def __reactivate(self):
        """Reactivate a cell."""
        super().__reactivate()
        # add custom code here:
        pass


    # process-related methods:

    # TODO: add some if needed...
    
    processes = [] # TODO: instantiate and list process objects here
