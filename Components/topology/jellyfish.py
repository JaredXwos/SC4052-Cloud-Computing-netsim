import math
from typing import List

import networkx as nx

import global_randoms
from Components.host import Host


def build_jellyfish(
    hosts: List[Host],
    link_capacity: float = 100.0,
    link_latency: float = 1.0,
    switch_degree: int = 8,      # total ports per switch
    hosts_per_switch: int = 4,   # host ports
) -> nx.Graph:
    """
    Build Jellyfish random regular topology.

    Each switch:
        switch_degree total ports
        hosts_per_switch to hosts
        rest random switch-switch links
    """

    G = nx.Graph()

    n_hosts = len(hosts)
    n_switches = math.ceil(n_hosts / hosts_per_switch)

    switch_ports = switch_degree - hosts_per_switch
    if switch_ports <= 0:
        raise ValueError("switch_degree must exceed hosts_per_switch")

    # ------------------------
    # create switches
    # ------------------------

    switches = [f"T{i}" for i in range(n_switches)]

    for s in switches:
        G.add_node(s, type="switch")

    # ------------------------
    # attach hosts
    # ------------------------

    for i, host in enumerate(hosts):
        sw = switches[i // hosts_per_switch]

        G.add_node(host.id, type="host")

        G.add_edge(
            host.id, sw,
            capacity=link_capacity,
            latency=link_latency,
            congestion=0.0,
            stale_congestion=0.0,
        )

    # ------------------------
    # random regular switch graph
    # ------------------------

    # create stubs for each switch
    stubs = []
    for s in switches:
        stubs.extend([s] * switch_ports)

    global_randoms.topology.shuffle(stubs)

    # pair stubs randomly
    while len(stubs) >= 2:
        u = stubs.pop()
        v = stubs.pop()

        # avoid self-loop or duplicate edges
        if u == v or G.has_edge(u, v):
            stubs.extend([u, v])
            global_randoms.topology.shuffle(stubs)
            continue

        G.add_edge(
            u, v,
            capacity=link_capacity,
            latency=link_latency,
            congestion=0.0,
            stale_congestion=0.0,
        )

    return G