"""Society entity type mixing class template.

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
# from .... import master_data_model as D

from .... import Explicit

import operator


class Society (I.Society):
    """Society entity type mixin implementation class."""

    # standard methods:

    def __init__(self,
                 # *,  # TODO: uncomment when adding named args behind here
                 **kwargs):
        """Initialize an instance of Society."""
        super().__init__(**kwargs)  # must be the first line
        # TODO: add custom code here:
        pass

    def deactivate(self):
        """Deactivate a society."""
        # TODO: add custom code here:
        pass
        super().deactivate()  # must be the last line

    def reactivate(self):
        """Reactivate a society."""
        super().reactivate()  # must be the first line
        # TODO: add custom code here:
        pass

    # process-related methods:

    def get_majority_opinion(self, t):
        opinion_count = {}
        for op in self.culture.possible_opinions:
            opinion_count[op] = sum(1 for _ in filter(
                lambda ind: ind.opinion == op, self.individuals))

        self.opinion = max(opinion_count.items(),
                           key=operator.itemgetter(1))[0]

    processes = [
        Explicit(
            "identification of majority opinion",
            [I.Society.opinion],
            get_majority_opinion
        )
    ]
