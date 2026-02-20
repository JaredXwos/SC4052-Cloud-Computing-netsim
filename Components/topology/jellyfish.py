import math
from typing import List

import networkx as nx

import global_randoms
from Components.host import Host


import math

def build_jellyfish(
    hosts,
    *,
    link_capacity: float = 100.0,
    link_latency: float = 1.0,
    switch_degree: int = 32,     # match fat-tree k
    n_switches: int = 1280,      # match fat-tree total switches
) -> nx.Graph:
    """
    Jellyfish that matches fat-tree hardware budget:
      - same number of switches (n_switches)
      - same switch radix (switch_degree)
      - attach exactly len(hosts) hosts (possibly uneven per switch)
      - remaining ports become inter-switch links
    """

    topology = nx.Graph()

    host_count = len(hosts)
    if host_count == 0:
        raise ValueError("Cannot build topology with zero hosts")

    if n_switches <= 0:
        raise ValueError("n_switches must be > 0")

    if switch_degree <= 0:
        raise ValueError("switch_degree must be > 0")

    # ------------------------
    # create switches
    # ------------------------
    switches = [f"T{i}" for i in range(n_switches)]
    for s in switches:
        topology.add_node(s, type="switch")

    # ------------------------
    # distribute hosts across switches: 6 or 7 hosts per switch (for H=8192, S=1280)
    # ------------------------
    base = host_count // n_switches            # 8192//1280 = 6
    rem = host_count % n_switches              # 8192%1280  = 512

    # First `rem` switches get (base+1) hosts, rest get base
    hosts_per_sw = [base + 1] * rem + [base] * (n_switches - rem)

    # Safety: ensure host ports don't exceed radix
    if max(hosts_per_sw) > switch_degree:
        raise ValueError("Too many hosts per switch for given switch_degree")

    # Attach hosts
    h_idx = 0
    for s, hp in zip(switches, hosts_per_sw):
        for _ in range(hp):
            host = hosts[h_idx]
            h_idx += 1
            topology.add_node(host.id, type="host")
            topology.add_edge(
                host.id, s,
                capacity=link_capacity,
                latency=link_latency,
                congestion=0.0,
                stale_congestion=0.0,
            )

    assert h_idx == host_count

    # ------------------------
    # build inter-switch random graph with a degree sequence
    # degree per switch = remaining ports = switch_degree - hosts_attached
    # ------------------------
    degrees = [switch_degree - hp for hp in hosts_per_sw]

    # Must have even sum of degrees for pairing
    if sum(degrees) % 2 != 0:
        # Flip one switch by 1 (take one port away) to make sum even.
        # This keeps things stable and barely changes anything.
        for i in range(len(degrees)):
            if degrees[i] > 0:
                degrees[i] -= 1
                break

    # Create stubs
    stubs = []
    for s, d in zip(switches, degrees):
        stubs.extend([s] * d)

    global_randoms.topology.shuffle(stubs)

    # Pair stubs randomly (retry on conflicts)
    # NOTE: This can take longer at high degrees; still OK for your scale.
    max_retries = 200000
    retries = 0

    while len(stubs) >= 2:
        u = stubs.pop()
        v = stubs.pop()

        if u == v or topology.has_edge(u, v):
            # Put them back and reshuffle a bit
            stubs.extend([u, v])
            global_randoms.topology.shuffle(stubs)
            retries += 1
            if retries > max_retries:
                raise RuntimeError("Too many retries building switch graph; consider a stronger generator.")
            continue

        topology.add_edge(
            u, v,
            capacity=link_capacity,
            latency=link_latency,
            congestion=0.0,
            stale_congestion=0.0,
        )

    return topology