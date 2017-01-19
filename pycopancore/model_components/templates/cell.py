# This file is part of pycopancore.
#
# Copyright (C) 2016 by COPAN team at Potsdam Institute for Climate
# Impact Research
#
# URL: <http://www.pik-potsdam.de/copan/software>
# License: MIT license

"""
In this module a template for the Cell mixing class is composed to give an
example of the basic structure for the in the model used Cell class. It
Inherits from Cell_ in which variables and parameters are defined.
"""

#
#  Imports
#


from .interface import Cell_
from pycopancore.model_components import abstract

#
#  Define class Cell
#


class Cell(Cell_, abstract.Cell):
    """
    A template for the basic structure of the Cell mixin class that every model
    must use to compose their Cell class. Inherits from Cell_ as the interface
    with all necessary variables and parameters.
    """

    #
    #  Definitions of internal methods
    #

    def __init__(self,
                 # ,*,
                 **kwargs):
        """
        Initialize an instance of Cell.
        Possible variables are something like resources of some kind, lokal
        weather variables...
        """
        super().__init__(**kwargs)

    processes = []

    #
    #  Definitions of further methods
    #
