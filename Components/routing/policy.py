import random
import networkx as nx
import weights
import multipath

rip = multipath.no_multipath(weights.hop_weight)
ospf = multipath.no_multipath(weights.ospf_weight)
eigrp = multipath.no_multipath(weights.eigrp_weight)
rip_ecmp = multipath.ecmp(weights.hop_weight)
ospf_ecmp = multipath.ecmp(weights.ospf_weight)
eigrp_ecmp = multipath.ecmp(weights.eigrp_weight)
rip_drill = multipath.drill(weights.hop_weight)
ospf_drill = multipath.drill(weights.ospf_weight)
eigrp_drill = multipath.drill(weights.eigrp_weight)

def conga(topology: nx.Graph, src, dst):
    current = src
    path = [src]

    while current != dst:
        neighbors = topology[current].items()  # (neighbor, edge_data)

        costs = [
            (n, 1.0 / float(data["available_capacity"]))
            for n, data in neighbors
        ]

        min_cost = min(c for _, c in costs)
        candidates = [n for n, c in costs if c == min_cost]

        nxt = random.choice(candidates)

        path.append(nxt)
        current = nxt

    return path