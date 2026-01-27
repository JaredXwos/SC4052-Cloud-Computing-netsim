import random
import networkx as nx
from Components.topology.utils import get_capacity

def no_multipath(weight):
    def policy(topology: nx.Graph, src, dst):
        return nx.shortest_path(topology, src, dst, weight=weight)
    return policy

def ecmp(weight):
    def policy(topology: nx.Graph, src, dst):
        paths = list(nx.all_shortest_paths(topology, src, dst, weight=weight))
        return random.choice(paths)
    return policy

def drill(weight):
    def policy(topology: nx.Graph, src, dst):
        paths = list(nx.all_shortest_paths(topology, src, dst, weight=weight))

        choices = random.sample(paths, min(2, len(paths)))

        def path_cost(path):
            return sum(1.0 / get_capacity(topology, u, v)
                       for u, v in zip(path, path[1:]))

        return min(choices, key=path_cost)
    return policy