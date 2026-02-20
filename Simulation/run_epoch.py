from collections import defaultdict
from typing import List, Tuple, Dict
import networkx as nx
from multiprocessing import Pool
import os

import numpy as np
from Components.workloads.flow import Flow
from Simulation.epoch_result import EpochResult

from dataclasses import dataclass

@dataclass(frozen=True)
class EpochContext:
    # (u, v) -> eid mapping (undirected symmetric)
    edge_id: Dict[Tuple[int, int], int]
    capacity: np.ndarray
    latency: np.ndarray
    congestion: np.ndarray
    stale_congestion: np.ndarray
    edge_list: List[Tuple[int, int]]
    adj: Dict[int, List[Tuple[int, int]]]


def build_epoch_context(topology: nx.Graph) -> EpochContext:

    edge_id = {}
    edge_list = []

    capacity = []
    latency = []
    congestion = []
    stale_congestion = []

    # Pre-initialize adjacency for all nodes
    adj = {node: [] for node in topology.nodes()}

    for i, (u, v, data) in enumerate(topology.edges(data=True)):

        edge_id[(u, v)] = i
        edge_id[(v, u)] = i

        capacity.append(data["capacity"])
        latency.append(data["latency"])
        congestion.append(data["congestion"])
        stale_congestion.append(data["stale_congestion"])

        edge_list.append((u, v))

        adj[u].append((v, i))
        adj[v].append((u, i))

    # Convert to NumPy arrays for fast indexing
    capacity = np.asarray(capacity, dtype=np.float64)
    latency = np.asarray(latency, dtype=np.float64)
    congestion = np.asarray(congestion, dtype=np.float64)
    stale_congestion = np.asarray(stale_congestion, dtype=np.float64)

    return EpochContext(
        edge_id=edge_id,
        capacity=capacity,
        latency=latency,
        congestion=congestion,
        stale_congestion=stale_congestion,
        edge_list=edge_list,
        adj=adj
    )
def run_epoch(
    flows: List["Flow"],
    routing_schedule: List,
    ctx: EpochContext,
) -> EpochResult:
    print("Unique sources this epoch:", len(set(flow.src for flow in flows)))
    capacity = ctx.capacity
    latency = ctx.latency
    edge_list = ctx.edge_list
    edge_id = ctx.edge_id

    num_edges = len(capacity)
    k = len(routing_schedule) if routing_schedule else 1

    cap = np.asarray(capacity, dtype=np.float64)
    lat_arr = np.asarray(latency, dtype=np.float64)

    edge_load = np.zeros(num_edges, dtype=np.float64)
    edge_dropped = np.zeros(num_edges, dtype=np.float64)

    flow_paths_eids = []
    flow_offered = []
    flow_latency = []

    # --------------------------------------------------
    # Phase 1: Routing + edge load accumulation
    # --------------------------------------------------

    for flow in flows:
        base_rate = flow.rate / k
        if base_rate <= 0.0:
            continue

        for policy in routing_schedule:

            path_nodes = policy(flow.src, flow.dst)

            path_eids = []
            total_lat = 0.0

            for i in range(len(path_nodes) - 1):
                eid = edge_id[(path_nodes[i], path_nodes[i + 1])]
                path_eids.append(eid)

                edge_load[eid] += base_rate
                total_lat += lat_arr[eid]

            flow_paths_eids.append(path_eids)
            flow_offered.append(base_rate)
            flow_latency.append(total_lat)

    total_sent = float(sum(flow_offered)) if flow_offered else 0.0

    # --------------------------------------------------
    # Phase 2: Edge utilization (vectorized)
    # --------------------------------------------------

    edge_util = np.ones(num_edges, dtype=np.float64)
    mask = cap > 0.0
    edge_util[mask] = edge_load[mask] / cap[mask]

    # --------------------------------------------------
    # Phase 3: Delivered / dropped
    # --------------------------------------------------

    flow_rates = []
    total_dropped = 0.0

    for path_eids, offered in zip(flow_paths_eids, flow_offered):

        if not path_eids:
            flow_rates.append(offered)
            continue

        # No numpy allocation here
        util = max(edge_util[eid] for eid in path_eids)

        if util <= 1.0:
            delivered = offered
            dropped = 0.0
        else:
            delivered = offered / util
            dropped = offered - delivered

        flow_rates.append(delivered * k)
        total_dropped += dropped

        if dropped > 0.0:
            share = dropped / len(path_eids)
            for eid in path_eids:
                edge_dropped[eid] += share

    # --------------------------------------------------
    # Phase 4: Build result dictionaries
    # --------------------------------------------------

    edge_load_dict = {}
    edge_capacity_dict = {}
    edge_dropped_dict = {}

    switch_load = defaultdict(float)
    switch_capacity = defaultdict(float)

    for eid, (u, v) in enumerate(edge_list):

        load_e = float(edge_load[eid])
        cap_e = float(cap[eid])
        drop_e = float(edge_dropped[eid])

        edge_load_dict[(u, v)] = load_e
        edge_capacity_dict[(u, v)] = cap_e
        edge_dropped_dict[(u, v)] = drop_e

        switch_load[u] += load_e
        switch_load[v] += load_e
        switch_capacity[u] += cap_e
        switch_capacity[v] += cap_e

    return EpochResult(
        edge_load=edge_load_dict,
        edge_capacity=edge_capacity_dict,
        edge_dropped=edge_dropped_dict,
        flow_paths=flow_paths_eids,
        flow_rates=flow_rates,
        flow_latency=flow_latency,
        switch_load=switch_load,
        switch_capacity=switch_capacity,
        total_sent=total_sent,
        total_dropped=float(total_dropped),
    )
