from collections import defaultdict
from typing import List
import networkx as nx

from Components.routing.policy import RoutingPolicy
from Components.workloads.flow import Flow
from Components.topology.utils import get_capacity
from Simulation.epoch_result import EpochResult


def run_epoch(
    topology: nx.Graph,
    flows: List[Flow],
    routing_schedule: List[RoutingPolicy],
) -> EpochResult:
    """
    Simulate ONE epoch with flow-level congestion handling.

    Traffic is split across routing policies (subepochs).
    Delivery is computed per-flow using bottleneck scaling.
    """

    if not routing_schedule:
        raise ValueError("routing_schedule cannot be empty")

    k = len(routing_schedule)

    edge_load = defaultdict(float)
    edge_capacity = {}
    flow_paths = []
    flow_offered = []
    flow_latency = []

    total_sent = 0.0
    total_latency_weighted = 0.0

    for policy in routing_schedule:
        for flow in flows:

            subrate = flow.rate / k
            total_sent += subrate

            path = policy(topology, flow.src, flow.dst)

            flow_paths.append(path)
            flow_offered.append(subrate)

            latency = 0.0

            for u, v in zip(path, path[1:]):
                edge_load[(u, v)] += subrate
                latency += topology[u][v]["latency"]

            flow_latency.append(latency)
            total_latency_weighted += subrate * latency

    # Phase 2: compute utilization per edge

    edge_util = {}
    edge_dropped = defaultdict(float)

    for e, load in edge_load.items():
        cap = get_capacity(topology, *e)
        edge_capacity[e] = cap

        util = load / cap if cap > 0 else 1.0
        edge_util[e] = util

    # Phase 3: compute delivered per-flow

    flow_rates = []
    total_dropped = 0.0

    for path, offered in zip(flow_paths, flow_offered):

        # bottleneck utilization
        util = max(edge_util[(u, v)] for u, v in zip(path, path[1:]))

        if util <= 1.0:
            delivered = offered
        else:
            delivered = offered / util

        dropped = offered - delivered

        flow_rates.append(delivered)
        total_dropped += dropped

        # distribute dropped back to edges (for diagnostics only)
        if dropped > 0:
            share = dropped / (len(path) - 1)
            for u, v in zip(path, path[1:]):
                edge_dropped[(u, v)] += share

    return EpochResult(
        edge_load=dict(edge_load),
        edge_capacity=edge_capacity,
        edge_dropped=dict(edge_dropped),
        flow_paths=flow_paths,
        flow_rates=flow_rates,      # delivered rates now!
        flow_latency=flow_latency,
        total_sent=total_sent,      # offered
        total_dropped=total_dropped
    )