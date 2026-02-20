import math
from typing import List

import networkx as nx

from Components.host import Host
from Components.topology.utils import order_hosts_by_rack, order_hosts_by_tag


def build_leaf_spine(
    hosts: List[Host],
    link_capacity: float = 100.0,
    link_latency: float = 1.0,
    hosts_per_leaf: int = 8,
) -> nx.Graph:

    topology = nx.Graph()

    n_hosts = len(hosts)
    n_leaves = math.ceil(n_hosts / hosts_per_leaf)

    # Clos-style heuristic
    n_spines = max(2, int(math.sqrt(n_leaves)))

    leaves = [f"L{i}" for i in range(n_leaves)]
    spines = [f"S{i}" for i in range(n_spines)]

    # --------------------------------------------------
    # add spine switches
    # --------------------------------------------------

    for s in spines:
        topology.add_node(
            s,
            type="switch",
            role="spine",
            layer=2,
        )

    # --------------------------------------------------
    # add leaf switches
    # --------------------------------------------------

    for l in leaves:
        topology.add_node(
            l,
            type="switch",
            role="leaf",
            layer=1,
        )

    # --------------------------------------------------
    # leaf ↔ spine full bipartite
    # --------------------------------------------------

    for l in leaves:
        for s in spines:
            topology.add_edge(
                l, s,
                capacity=link_capacity,
                latency=link_latency,
                congestion=0.0,
                stale_congestion=0.0,
            )

    # --------------------------------------------------
    # hosts ↔ leaf
    # --------------------------------------------------

    for i, host in enumerate(hosts):

        leaf = leaves[i // hosts_per_leaf]

        topology.add_node(
            host.id,
            type="host",
            layer=0,
        )

        topology.add_edge(
            host.id, leaf,
            capacity=link_capacity,
            latency=link_latency,
            congestion=0.0,
            stale_congestion=0.0,
        )

    return topology

def build_leaf_spine_informed(
    hosts: List[Host],
    link_capacity: float = 100.0,
    link_latency: float = 1.0,
    hosts_per_leaf: int = 8,
    affinity_prefix: str = "job:",
) -> nx.Graph:
    """
    Leaf–spine topology with affinity-aware placement.

    Hosts sharing the same affinity tag prefix are packed onto the same leaf
    before moving to the next leaf.

    Simulates rack-aware scheduler placement.
    """

    topology = nx.Graph()

    n_hosts = len(hosts)
    n_leaves = math.ceil(n_hosts / hosts_per_leaf)

    # same heuristic as before
    n_spines = max(2, int(math.sqrt(n_leaves)))

    leaves = [f"L{i}" for i in range(n_leaves)]
    spines = [f"S{i}" for i in range(n_spines)]

    # ------------------------
    # switches
    # ------------------------

    for l in leaves:
        topology.add_node(l, type="leaf")

    for s in spines:
        topology.add_node(s, type="spine")

    # full bipartite leaf-spine
    for l in leaves:
        for s in spines:
            topology.add_edge(
                l, s,
                capacity=link_capacity,
                latency=link_latency,
                congestion=0.0,
                stale_congestion=0.0,
            )

    ordered_hosts = order_hosts_by_tag(hosts, affinity_prefix)

    for i, host in enumerate(ordered_hosts):

        leaf = leaves[i // hosts_per_leaf]

        topology.add_node(host.id, type="host", host=host)

        topology.add_edge(
            host.id, leaf,
            capacity=link_capacity,
            latency=link_latency,
            congestion=0.0,
            stale_congestion=0.0,
        )

    return topology
