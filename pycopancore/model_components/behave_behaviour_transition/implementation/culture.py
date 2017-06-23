"""Culture process taxon mixing class template.

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
# sure that's right?
import numpy as np
import igraph
import networkx as nx


class Culture (I.Culture):
    """Culture process taxon mixin implementation class."""

    # standard methods:

    # NEEDED?
    __background_proximity = None
    __interaction_network = None

    def __kolmogorov_smirnov_test(self):

        pass


    def __init__(self,
                 # *,  # TODO: uncomment when adding named args behind here
                 # degree_preference=None, social_influence,
                 # model_parameters (including number of individuals, might not be necessary),
                 # social_distance_function
                 **kwargs):
        """Initialize the unique instance of Culture."""
        super().__init__(**kwargs)  # must be the first line
        # TODO: add custom code here:

        # exception
        #if not callable()

        # set intern variables

        self.n_individual = model_parameters.n_individual
        self.mean_degree_pref = model_parameters.mean_degree_pref
        self.std_degree_pref = model_parameters.std_degree_pref
        self.p_rew = model_parameters.p_rew
        self.social_distance = social_distance_function
        self.char_weight = model_parameters.char_weight


        # create nodes list from acquaintance network
        self.__nodes = self.acquaintance_network.nodes()

        # initialise background proximity network
        proximity_network = igraph.GraphBase.Lattice([self.n_individual], nei=int(float(self.mean_degree_pref)/2.0),
                                                     directed=False, mutual=True, circular=True)
        proximity_network.rewire(int(self.p_rew * self.n_individual * self.mean_degree_pref))
        small_world_distance_matrix = np.asarray(proximity_network.shortest_paths())

        # Generate random noise
        random_prox_noise = np.random.random((self.n_individual,self.n_individual))
        random_prox_noise = (random_prox_noise + random_prox_noise.transpose()) * .5

        # Derive the background proximity matrix with added noise to generate a continuum
        __background_proximity = (1 - .1 * (small_world_distance_matrix-1) - 0.1 *
                             random_prox_noise)

        # Introduce a proximity offset
        # For high degrees of separation there is no proximity difference anymore
        __background_proximity[np.where(__background_proximity <= 0.2)] = 0.2

        # make sure there are no self-loops
        for k in range(__background_proximity.shape[0]):
            __background_proximity[k,k] = 0




        pass

    # process-related methods:


    # NEED TO IMPLEMENT GET CHARACTERISTICS FUNCTION IN INDIVIDUAL!
    # IS NUMPY ARRAY APPROPRIATE DATA TYPE?
    def get_agents_characteristics(self):

        agent_characteristics = np.array([self.n_individual])

        for i in range(self.n_individual):
            agent_characteristics[i] = self.__nodes[i].get_characteristics()

        return agent_characteristics



    # IS THERE A FASTER WAY FOR THIS?
    # char_weight not yet defined
    def get_proximity_matrix(self):

        distances = np.zeros(self.n_individual, self.n_individual)

        for i in range(self.n_individual):
            for j in range(self.n_individual):
                distances[i][j] = self.char_weight[0] * np.abs(np.abs(
                    self.social_distance(self.__nodes[i],self.__nodes[j])) - 1)

        # char_weight not yet defined!
        return distances + self.char_weight[1] * self.__background_proximity



    def generate_interaction_network(self):

        # correct this line!
        distance_metric_matrix = nx.to_numpy_matrix(self.acquaintance_network.path_lengths())

        #define p_ai and interaction_offset
        exp_dec = (self.p_ai - self.interaction_offset) * \
                  np.exp(-(distance_metric_matrix - 1) / 2.)

        distmax = distance_metric_matrix[np.isfinite(distance_metric_matrix)].max()

        histo_bins = np.arange(1, distmax)

        histo_range = [histo_bins.min(), histo_bins.max()]
        distribution = np.histogram(distance_metric_matrix.flatten(), histo_bins, range=histo_range)

        for i in distribution[1][:-1]:
            exp_dec[distance_metric_matrix == i] *= (float(distribution[0][0]) / distribution[0][i - 1])


        exp_dec += L.interaction_offset

        return exp_dec


    def update_social_influence(self):
        pass

    def update_contact_network(self):
        pass

    def one_step(self):
        pass



    # TODO: add some if needed...

    processes = []  # TODO: instantiate and list process objects here
