import random
from typing import Callable

import networkx as nx
from Components.routing import weights, multipath
from Components.topology.topology_types import Node, Path

RoutingPolicy = Callable[[nx.Graph, Node, Node], Path]

rip = multipath.no_multipath(weights.hop_weight)
ospf = multipath.no_multipath(weights.ospf_weight)
eigrp = multipath.no_multipath(weights.eigrp_weight)
stale_ospf = multipath.no_multipath(weights.stale_ospf_weight)
stale_eigrp = multipath.no_multipath(weights.stale_eigrp_weight)

rip_ecmp = multipath.ecmp(weights.hop_weight)
ospf_ecmp = multipath.ecmp(weights.ospf_weight)
eigrp_ecmp = multipath.ecmp(weights.eigrp_weight)
stale_ospf_ecmp = multipath.ecmp(weights.stale_ospf_weight)
stale_eigrp_ecmp = multipath.ecmp(weights.stale_eigrp_weight)

rip_drill = multipath.drill(weights.hop_weight)
ospf_drill = multipath.drill(weights.ospf_weight)
eigrp_drill = multipath.drill(weights.eigrp_weight)
stale_ospf_drill = multipath.drill(weights.stale_ospf_weight)
stale_eigrp_drill = multipath.drill(weights.stale_eigrp_weight)

def conga(topology: nx.Graph, src, dst):
    current = src
    path = [src]

    while current != dst:
        neighbors = topology[current].items()  # (neighbor, edge_data)

        costs = [
            (n, 1.0 / float(data["capacity"]-data["congestion"]))
            for n, data in neighbors
        ]

        min_cost = min(c for _, c in costs)
        candidates = [n for n, c in costs if c == min_cost]

        nxt = random.choice(candidates)

        path.append(nxt)
        current = nxt

    return path