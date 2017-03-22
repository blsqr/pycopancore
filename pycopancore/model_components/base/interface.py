"""Base model component interface.

In this base interface module, variables for each entity are defined in
corresponding class as sympy objects . The corresponding classes are World_,
Cell_, Nature_, Individual_, Culture_, Society_, Metabolism_ and Model_.
"""

# This file is part of pycopancore.
#
# Copyright (C) 2017 by COPAN team at Potsdam Institute for Climate
# Impact Research
#
# URL: <http://www.pik-potsdam.de/copan/software>
# License: MIT license

from ... import Variable, ReferenceVariable, SetVariable
from ... import master_data_model as D
from ...data_model.master_data_model import NAT, MET, CUL, W, S, C, I


# model component:


class Model (object):
    """Basic Model component interface."""

    # metadata:
    name = "copan:CORE Base"
    description = "Basic model component only providing basic relationships between " \
                  "entity types."
    requires = []


# process taxa:


class Nature (object):
    """Basic Nature interface.

    It contains all variables specified as mandatory ("base variables").
    """

    geographic_network = NAT.geographic_network


class Metabolism (object):
    """Basic Metabolism interface.

    It contains all variables specified as mandatory ("base variables").
    """

    pass


class Culture (object):
    """Basic Culture interface.

    It contains all variables specified as mandatory ("base variables").
    """

    acquaintance_network = CUL.acquaintance_network


# entity types:


class World (object):
    """Basic World interface.

    It contains all variables specified as mandatory ("base variables").
    """

    # references:
    nature = ReferenceVariable("nature",
                               "Nature taxon working on this world",
                               type=Nature)
    metabolism = ReferenceVariable("metabolism",
                                   "Metabolism taxon working on this world",
                                   type=Metabolism)
    culture = ReferenceVariable("culture",
                                "Culture taxon working on this world",
                                type=Culture)

    population = W.population
    # TODO: make sure it is no smaller than aggregate top-level societies'

    atmospheric_carbon = W.atmospheric_carbon
    surface_air_temperature = W.surface_air_temperature
    ocean_carbon = W.ocean_carbon
    terrestrial_carbon = W.terrestrial_carbon
    fossil_carbon = W.fossil_carbon

    # attributes storing redundant information (backward references):
    societies = SetVariable("societies",
                            "set of all Societies on this world")
    top_level_societies = SetVariable(
                            "top level societies",
                            "set of top-level Societies on this world")
    cells = SetVariable("cells", "set of Cells on this world")
    individuals = SetVariable("individuals",
                              "set of Individuals residing on this world")


class Society (object):
    """Basic Society interface.

    It contains all variables specified as mandatory ("base variables").
    """

    # references:
    world = ReferenceVariable("world", "", type=World)
    next_higher_society = ReferenceVariable("next higher society", "optional",
                                            allow_none=True)

    # other variables:
    # population is explicitly allowed to be non-integer so that we can use
    # ODEs:
    # TODO: replace by suitable CETSVariable!
    population = S.population
    # TODO: make sure it is no smaller than
    # aggregate next_lower_level societies'

    # read-only attributes storing redundant information:
    nature = ReferenceVariable("nature", "", type=Nature)
    metabolism = ReferenceVariable("metabolism", "", type=Metabolism)
    culture = ReferenceVariable("culture", "", type=Culture)
    higher_societies = SetVariable(
                                "higher societies",
                                "upward list of (in)direct super-Societies")
    next_lower_societies = SetVariable(
                                "next lower societies",
                                "set of sub-Societies of next lower level")
    lower_societies = SetVariable(
                                "lower societies",
                                "set of all direct and indirect sub-Societies")
    direct_cells = SetVariable("direct cells", "set of direct territory Cells")
    cells = SetVariable("cells", "set of direct and indirect territory Cells")
    direct_individuals = SetVariable(
                            "direct individuals",
                            "set of resident Individuals not in subsocieties")
    individuals = SetVariable("individuals",
                              "set of direct or indirect resident Individuals")

# specified only now to avoid recursion:
Society.next_higher_society.type = Society
Society.higher_societies.type = Society
Society.next_lower_societies.type = Society
Society.lower_societies.type = Society
World.societies.type = Society
World.top_level_societies.type = Society


class Cell (object):
    """Basic Cell interface.

    It contains all variables specified as mandatory ("base variables").
    """

    # references:
    world = ReferenceVariable("world", "", type=World)
    society = ReferenceVariable("society",
                                "optional lowest-level soc. cell belongs to",
                                type=Society, allow_none=True)

    # other variables:
    location = Variable("location", "pair of coordinates?")
    land_area = Variable("land area", "", unit=D.square_kilometers,
                         strict_lower_bound=0)

    terrestrial_carbon = C.terrestrial_carbon
    fossil_carbon = C.fossil_carbon

    # attributes storing redundant information:
    nature = ReferenceVariable("nature", "", type=Nature)
    metabolism = ReferenceVariable("metabolism", "", type=Metabolism)
    culture = ReferenceVariable("culture", "", type=Culture)
    societies = SetVariable(
                    "societies",
                    "upward list of Societies it belongs to (in)directly",
                    type=Society)
    individuals = SetVariable("individuals",
                              "set of resident Individuals")

# specified only now to avoid recursion:
World.cells.type = Cell
Society.direct_cells.type = Cell
Society.cells.type = Cell

class Individual (object):
    """Basic Individual interface.

    It contains all variables specified as mandatory ("base variables").
    """

    # references:
    cell = ReferenceVariable("cell", "cell of residence", type=Cell)

    # other variables:
    relative_weight = \
        Variable("relative representation weight",
                 "relative representation weight for society's population",
                 unit=D.unity, lower_bound=0, default=1)

    # attributes storing redundant information:
    world = ReferenceVariable("world", "", type=World)
    nature = ReferenceVariable("nature", "", type=Nature)
    metabolism = ReferenceVariable("metabolism", "", type=Metabolism)
    culture = ReferenceVariable("culture", "", type=Culture)
    society = ReferenceVariable(
                        "society", 
                        "lowest level Society this individual is resident of", 
                        type=Society)
    societies = SetVariable(
                    "societies",
                    "upward list of all Societies it is resident of",
                    type=Society)
    acquaintances = SetVariable("acquaintances",
                                "set of Individuals this is acquainted with")

    population_share = None
    """share of society's direct population represented by this individual"""
    represented_population = None
    """absolute population represented by this individual"""

# specified only now to avoid recursion:
World.individuals.type = Individual
Society.direct_individuals.type = Individual
Society.individuals.type = Individual
Cell.individuals.type = Individual
Individual.acquaintances.type = Individual
