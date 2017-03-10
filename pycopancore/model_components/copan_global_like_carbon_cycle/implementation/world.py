"""Jobst: write docstring."""
from pycopancore import Explicit, ODE
from .. import interface as I
import pycopancore.model_components.base.interface as base


class World (I.World):
    """Jobst: write docstring."""

    # standard methods:

    def __init__(self,
                 *,
                 atmospheric_carbon = 1,
                 ocean_carbon = 1,
                 surface_air_temperature = 0,
                 **kwargs
                 ):
        """Initialize an (typically the unique) instance of World."""
        super().__init__(**kwargs)
        # initial values:
        self.atmospheric_carbon = atmospheric_carbon
        self.ocean_carbon = ocean_carbon
        self.surface_air_temperature = surface_air_temperature

    # process-related methods:

    def convert_temperature(self, unused_t):
        """(see Anderies et al. 2013)"""
        self.surface_air_temperature = self.nature.temperature_offset \
            + self.nature.temperature_sensitivity_on_atmospheric_carbon \
              * self.atmospheric_carbon

    def preserve_carbon(self, unused_t):
        self.ocean_carbon = self.nature.total_carbon \
            - self.atmospheric_carbon \
            - self.terrestrial_carbon \
            - self.fossil_carbon

    def ocean_atmosphere_diffusion(self, unused_t):
        """(see Anderies et al. 2013)"""
        flow = self.nature.ocean_atmosphere_diffusion_coefficient * (
                self.nature.carbon_solubility_in_sea_water * self.ocean_carbon
                - self.atmospheric_carbon)
        self.d_ocean_carbon -= flow
        self.d_atmospheric_carbon += flow

    processes = [
                 Explicit("convert temperature",
                          [I.World.surface_air_temperature],
                          convert_temperature),
                 Explicit("carbon preservation",
                          [I.World.ocean_carbon],
                          preserve_carbon
#                          [I.Nature.total_carbon
#                           - I.World.atmospheric_carbon
#                           - base.World.terrestrial_carbon
#                           - base.World.fossil_carbon]
                          ),
                 ODE("ocean-atmosphere diffusion",
                     [I.World.ocean_carbon, I.World.atmospheric_carbon],
                     ocean_atmosphere_diffusion)
                 ]
