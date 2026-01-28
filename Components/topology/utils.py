from collections import defaultdict
from typing import List

import networkx as nx

from Components.host import Host


def add_link_alias(topology: nx.Graph, capacity: float, latency: float):
    """
    Return a small helper function:

        add_link(u, v)

    that adds an edge with standard attributes.

    Uses closure to capture:
        - graph
        - capacity
        - latency
    """

    def add_link(u, v):
        topology.add_edge(
            u,
            v,
            capacity=capacity,
            latency=latency,
            load=0.0,
        )

    return add_link

def get_capacity(topology, u, v) -> float:
    return float(topology[u][v]["capacity"])

def get_congestion(topology, u, v) -> float:
    return float(topology[u][v]["congestion"])

def get_stale_congestion(topology, u, v) -> float:
    return float(topology[u][v]["stale_congestion"])

def clear_congestions(topology) -> None:
    for u in topology:
        for v in topology[u]:
            topology[u][v]["congestion"] = 0
            topology[u][v]["stale_congestion"] = 0

def order_hosts_by_tag(hosts: List[Host], prefix: str) -> List[Host]:
    """
    Pack hosts with same prefix tag together.

    Example:
        prefix="job:"
    """

    groups = defaultdict(list)
    others = []

    for h in hosts:
        tag = next((t for t in h.tags if t.startswith(prefix)), None)
        if tag:
            groups[tag].append(h)
        else:
            others.append(h)

    ordered = []

    # keep deterministic order
    for key in sorted(groups):
        ordered.extend(groups[key])

    ordered.extend(others)

    return ordered

def order_hosts_by_rack(
    hosts: List[Host],
    prefix: str,
    hosts_per_rack: int,
) -> List[Host]:
    """
    Order hosts so that:
    1) same-tag hosts stay together
    2) no rack contains mixed tags unless unavoidable

    This respects rack capacity while preserving affinity.
    """

    groups = defaultdict(list)
    others = []

    for h in hosts:
        tag = next((t for t in h.tags if t.startswith(prefix)), None)
        if tag:
            groups[tag].append(h)
        else:
            others.append(h)

    ordered = []

    # deterministic order
    for key in sorted(groups):
        g = groups[key]

        # ⭐ chunk by rack capacity
        for i in range(0, len(g), hosts_per_rack):
            ordered.extend(g[i:i + hosts_per_rack])

    # pack leftovers
    ordered.extend(others)

    return ordered