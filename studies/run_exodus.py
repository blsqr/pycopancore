"""This is the test script for the seven dwarfs step by step tutorial.

In this version only the Step-process 'aging' of entitytype 'Individual' is
implemented, such that the only relevant attributes of 'Individual' are 'age'
and 'cell'.
"""

import random
from scipy import stats
from time import time
import datetime as dt
import numpy as np
import networkx as nx
import pickle, json

import plotly.offline as py
import plotly.graph_objs as go
from matplotlib.pyplot import plot, gca, show, savefig

import pycopancore.models.exodus as M
from pycopancore.runners.runner import Runner


# setting timeinterval for run method 'Runner.run()'
timeinterval = 200
# setting time step to hand to 'Runner.run()'
timestep = .1

nm = 2  # number of municipalities, also cities
nc = 2  # number of counties, also farmland_cells
nf = 20  # number of farmers
nt = 20  # number of townsmen


model = M.Model()

# instantiate process taxa culture:
# In this certain case we need 'M.Culture()' for the acquaintance network.
culture = M.Culture()
metabolism = M.Metabolism(market_frequency=1)

# instantiate world:
world = M.World(culture=culture, metabolism=metabolism,
                water_price=1, max_utility=1)
# Instantiate Societies:
municipalities = [M.Society(world=world,
                            municipality_like=True,
                            base_mean_income=1000)
                  for m in range(nm)
                  ]

counties = [M.Society(world=world,
                      municipality_like=False)
            for c in range(nc)
            ]
# Instantiate farmland cells:
farmland_cells = []
county_allocation = list(counties)
for fc in range(nc):
    # chose county:
    county = random.choice(county_allocation)
    county_allocation.remove(county)
    farmland_cells.append(M.Cell(world=world,
                                 society=county,
                                 characteristic='farmland',
                                 land_area= 0.01 * (nf + nt),  # in square kilometers
                                 average_precipitation=0.75))
# Instantiate city cells:
city_cells = []
municipality_allocation = list(municipalities)

for cc in range(nm):
    # chose county:
    municipality = random.choice(municipality_allocation)
    municipality_allocation.remove(municipality)
    city_cells.append(M.Cell(world=world,
                             society=municipality,
                             characteristic='city',
                             average_precipitation=0))

# Instantiate farmers:
farmers = []
for f in range(nf):
    # Chose cell
    farmland = random.choice(farmland_cells)
    # determine liquidity before first market:
    liq = stats.lognorm.rvs(scale=300, s=0.34, loc=0)
    farmers.append(M.Individual(cell=farmland,
                                profession='farmer',
                                outspokensess=1,
                                liquidity=liq,
                                nutrition=1000))
# Instantiate townsmen:
townsmen = []
for t in range(nt):
    # Chose cell
    city = random.choice(city_cells)
    # determine liquidity before first market:
    liq = stats.lognorm.rvs(scale=700, s=0.34, loc=0)
    townsmen.append(M.Individual(cell=city,
                                 profession='townsman',
                                 outspokensess=1,
                                 liquidity=liq,
                                 nutrition=100))

# Create Network:
expected_degree = 5

# from run_adaptive_voter_model:


def erdosrenyify(graph, p=0.5):
    """Create a ErdosRenzi graph from networkx graph.

    Take a a networkx.Graph with nodes and distribute the edges following the
    erdos-renyi graph procedure.
    """
    assert not graph.edges(), "your graph has already edges"
    nodes = graph.nodes()
    for i, n1 in enumerate(nodes[:-1]):
        for n2 in nodes[i+1:]:
            if random.random() < p:
                graph.add_edge(n1, n2)


# set the initial graph structure to be an erdos-renyi graph
print("erdosrenyifying the graph ... ", end="", flush=True)
start = time()
erdosrenyify(culture.acquaintance_network, p=expected_degree / (nf + nt))
print("done ({})".format(dt.timedelta(seconds=(time() - start))))

start = time()
# Calculate societies variables before run:
for soc in M.Society.instances:
    soc.calculate_mean_income_or_farmsize(0)
    soc.calc_population(0)
    soc.calculate_average_liquidity(0)
# Calculate other stuff:
for ind in M.Individual.instances:
    ind.calculate_harvest(0)
    ind.calculate_utility(0)
# Run market clearing once:
metabolism.do_market_clearing(0)
culture.calculate_modularity(0)
print("done ({})".format(dt.timedelta(seconds=(time() - start))))

termination_conditions = [[M.Culture.check_for_split, culture]]

print('\n runner starting')
# Runner is instantiated
r = Runner(model=model, termination_calls=termination_conditions)

start = time()
# run the Runner and saving the return dict in traj
traj = r.run(t_1=timeinterval, dt=timestep)
runtime = dt.timedelta(seconds=(time() - start))
print('runtime: {runtime}'.format(**locals()))

# Plotting:
t = np.array(traj['t'])
# for key, val in traj.items():
#     print('key', key,)
plot(t, traj[M.World.water_price][world], "b", lw=3)
plot(t, traj[M.World.total_gross_income][world], "m:", lw=3)
plot(t, traj[M.World.total_harvest][world], "m--", lw=3)
# plot(t, traj[M.Culture.network_clustering][culture], "r--", lw=3)
plot(t, traj[M.Culture.modularity][culture], "r:", lw=3)

for soc in municipalities:
    plot(t, traj[M.Society.population][soc], "r", lw=3)
for soc in counties:
    plot(t, traj[M.Society.population][soc], "k", lw=3)
for ind in M.Individual.instances:
    plot(t, traj[M.Individual.utility][ind], "y", lw=0.5)
gca().set_yscale('symlog')

# savefig('20_ag_4_soc.png', dpi=150)
# show()

network_data = traj[M.Culture.acquaintance_network][culture]
G = network_data[-1]

# Make list to have colors according to profession:
professions = {}
for ind in M.Individual.instances:
    if ind.profession == 'farmer':
        professions[ind] = 'yellow'
    else:
        professions[ind] = 'red'
colors = [professions.get(node) for node in G.nodes()]
# Make second list to have labels according to society:
societies = {}
for ind in M.Individual.instances:
    societies[ind] = str(ind.society._uid)
nx.draw(G, node_color=colors,
        labels=societies,
        pos=nx.spring_layout(G))
# show()

# traj.save(filename='data')

#with open('data.pickle', 'rb') as f:
#    trajectory = pickle.load(f)

# alternative plotting:
# city_population = np.array([traj[M.Society.population][soc]
#                            for soc in municipalities])
# county_population = np.array([traj[M.Society.population][soc]
#                              for soc in counties])
# utilities = np.array([traj[M.Individual.utility][ind]
#                      for ind in M.Individual.instances])
# population_data = []
# for i, s in enumerate(municipalities):
#     population_data.append(go.Scatter(
#         x=t,
#         y=city_population[i],
#         name='population of municipality {}'.format(i),
#         mode='lines',
#         line=dict(color="green", width=4)
#     ))
#
# for i, c in enumerate(counties):
#     population_data.append(go.Scatter(
#         x=t,
#         y=county_population[i],
#         name='population of county {}'.format(i),
#         mode='lines',
#         line=dict(color="red", width=4)
#     ))
# price = traj[M.World.water_price][world]
# price_data = []
# price_data.append(go.Scatter(
#     x=t,
#     y=price,
#     name='price of water',
#     mode='lines',
#     line=dict(color="blue", width=4)
# ))
# utilities_data = []
# for i, ind in enumerate(M.Individual.instances):
#     utilities_data.append(go.Scatter(
#         x=t,
#         y=utilities[i],
#         name='utility of citizen {}'.format(i),
#         mode='lines',
#         line=dict(color="green", width=4)
#     ))
#
# layout = dict(title='Exodus',
#               xaxis=dict(title='time [yr]'),
#               yaxis=dict(title='value'),
#               )
#
# fig = dict(data=[population_data[i] for i, soc in enumerate(
#     [municipalities + counties])],
#            layout=layout)
# fig2 = dict(data=[price_data[0]],
#             layout=layout)
# fig3 = dict(data=[utilities_data[i] for i, ind in enumerate(M.Individual.instances)],
#             layout=layout)
#
# py.plot(fig, filename='Exodus populations.html')
# py.plot(fig2, filename='Exodus water price.html')
# py.plot(fig3, filename='Exodus utilities.html')
