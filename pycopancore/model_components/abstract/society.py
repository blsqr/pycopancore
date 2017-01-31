"""Abstract class which all Soiety mixin classes must implement."""

# This file is part of pycopancore.
#
# Copyright (C) 2016 by COPAN team at Potsdam Institute for Climate Impact
# Research
#
# URL: <http://www.pik-potsdam.de/copan/software>
# License: MIT license

from pycopancore.private import _AbstractEntityMixin


class Society (_AbstractEntityMixin):
    """Abstract class which all Soiety mixin classes must implement."""

    def __init__(self):
        """Initialize object."""
        super().__init__()

    processes = []
