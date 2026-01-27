import random
import networkx as nx
from Components.topology.utils import get_capacity, get_congestion


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

        # sample 2 like classic DRILL
        choices = random.sample(paths, min(2, len(paths)))

        def path_cost(path):
            # bottleneck utilization (smaller is better)
            worst = 0.0

            for u, v in zip(path, path[1:]):
                cap = get_capacity(topology, u, v)
                cong = get_congestion(topology, u, v)

                util = cong / cap if cap > 0 else 1.0
                if util > worst:
                    worst = util

            return worst

        return min(choices, key=path_cost)

    return policy