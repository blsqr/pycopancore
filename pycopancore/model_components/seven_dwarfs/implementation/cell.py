"""Cell entity type mixing class template.

TODO: adjust or fill in code and documentation wherever marked by "TODO:",
then remove these instructions
"""
# This file is part of pycopancore.
#
# Copyright (C) 2017 by COPAN team at Potsdam Institute for Climate
# Impact Research
#
# URL: <http://www.pik-potsdam.de/copan/software>
# License: MIT license

from .. import interface as I
from pycopancore import Event
import numpy as np

# from .... import master_data_model as D


class Cell (I.Cell):
    """Cell entity type mixin implementation class."""

    # standard methods:

    def __init__(self,
                 *,
                 eating_stock=100,
                 **kwargs):
        """Initialize an instance of Cell."""
        super().__init__(**kwargs)
        self.eating_stock = eating_stock

        # Following method is defined in abstract_entity_mixin which is
        # inherited only by mixing in the model:
        self.assert_valid()

    # process-related methods:

    def snow_white_arrival(t):
        """Calculate snow white's arrival."""
        return t + np.random.exponential(14.)

    def snow_white_eating(self, unused_t):
        """Party hard."""
        print('Snow white arrives and has the munchies.')
        self.eating_stock = self.eating_stock / 2.

    processes = [
        Event("snow_white",
              [I.Cell.eating_stock],
              ["time", snow_white_arrival, snow_white_eating]
              )
    ]
