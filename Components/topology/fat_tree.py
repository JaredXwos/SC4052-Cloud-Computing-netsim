import networkx as nx
from typing import List
from Components.topology.utils import add_link_alias, order_hosts_by_tag, order_hosts_by_rack
from Components.host import Host

def infer_k(num_hosts: int) -> int:
    """
    Find smallest even k such that k^3/4 >= H.

    This ensures the fat-tree has enough host ports.
    """
    k = 2
    while (k**3) // 4 < num_hosts:
        k += 2
    return k

def build_fat_tree(
    hosts: List[Host],
    link_capacity: float = 100.0,
    link_latency: float = 1.0,
) -> nx.Graph:
    """
    Build full symmetric fat-tree sized automatically to fit hosts.

    Round-up strategy:
        capacity >= len(hosts)
        unused ports remain empty
    """

    num_hosts = len(hosts)
    if num_hosts == 0:
        raise ValueError("Cannot build topology with zero hosts")

    k = infer_k(num_hosts)
    half = k // 2

    print(f"[fat-tree] k={k}, capacity={k**3//4}, hosts={num_hosts}")

    fat_tree = nx.Graph()

    # 🔑 get closure helper (this replaces local add_link)
    add_link = add_link_alias(fat_tree, link_capacity, link_latency)

    # Add host nodes
    for host in hosts:
        fat_tree.add_node(host.id, type="host", host=host, layer=0)

    # Create switches
    edge_switches = []
    agg_switches = []
    for p in range(k):
        for e in range(half):
            name = f"e_{p}_{e}"
            fat_tree.add_node(name, type="switch", layer=1)
            edge_switches.append(name)

        for a in range(half):
            name = f"a_{p}_{a}"
            fat_tree.add_node(name, type="switch", layer=2)
            agg_switches.append(name)

    core_switches = []
    for c in range(half * half):
        name = f"c_{c}"
        fat_tree.add_node(name, type="switch", layer=3)
        core_switches.append(name)

    # link edge to aggregation
    for p in range(k):
        edges = [f"e_{p}_{i}" for i in range(half)]
        aggs = [f"a_{p}_{i}" for i in range(half)]

        for e in edges:
            for a in aggs:
                add_link(e, a)

    # link aggregation to core
    for p in range(k):
        for a_idx in range(half):
            agg = f"a_{p}_{a_idx}"
            for c_idx in range(half):
                core = f"c_{a_idx * half + c_idx}"
                add_link(agg, core)

    # link hosts to edges
    host_iter = iter(hosts)

    for edge in edge_switches:
        for _ in range(half):
            try:
                host = next(host_iter)
            except StopIteration:
                break
            add_link(host.id, edge)

    return fat_tree

def build_fat_tree_informed(
    hosts: List[Host],
    link_capacity: float = 100.0,
    link_latency: float = 1.0,
    affinity_prefix: str = "job:",
) -> nx.Graph:
    """
    Fat-tree with affinity-aware placement.

    Hosts sharing the same tag prefix (e.g. "job:0")
    are packed into the same racks first.

    Simulates scheduler-aware placement.
    """

    num_hosts = len(hosts)
    if num_hosts == 0:
        raise ValueError("Cannot build topology with zero hosts")

    k = infer_k(num_hosts)
    half = k // 2

    print(f"[fat-tree-informed] k={k}, capacity={k**3//4}, hosts={num_hosts}")

    fat_tree = nx.Graph()
    add_link = add_link_alias(fat_tree, link_capacity, link_latency)

    # ------------------------
    # add host nodes
    # ------------------------

    for host in hosts:
        fat_tree.add_node(host.id, type="host", host=host, layer=0)

    # ------------------------
    # switches (UNCHANGED)
    # ------------------------

    edge_switches = []
    agg_switches = []

    for p in range(k):
        for e in range(half):
            name = f"e_{p}_{e}"
            fat_tree.add_node(name, type="switch", layer=1)
            edge_switches.append(name)

        for a in range(half):
            name = f"a_{p}_{a}"
            fat_tree.add_node(name, type="switch", layer=2)
            agg_switches.append(name)

    core_switches = []

    for c in range(half * half):
        name = f"c_{c}"
        fat_tree.add_node(name, type="switch", layer=3)
        core_switches.append(name)

    # ------------------------
    # wiring (UNCHANGED)
    # ------------------------

    for p in range(k):
        edges = [f"e_{p}_{i}" for i in range(half)]
        aggs = [f"a_{p}_{i}" for i in range(half)]
        for e in edges:
            for a in aggs:
                add_link(e, a)

    for p in range(k):
        for a_idx in range(half):
            agg = f"a_{p}_{a_idx}"
            for c_idx in range(half):
                core = f"c_{a_idx * half + c_idx}"
                add_link(agg, core)

    # ------------------------
    # ⭐ NEW: affinity-aware host ordering
    # ------------------------

    hosts_per_rack = half
    ordered_hosts = order_hosts_by_rack(hosts, affinity_prefix, hosts_per_rack)

    host_iter = iter(ordered_hosts)

    for edge in edge_switches:
        for _ in range(half):
            try:
                host = next(host_iter)
            except StopIteration:
                break
            add_link(host.id, edge)

    return fat_tree