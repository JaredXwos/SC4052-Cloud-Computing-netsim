import os
from multiprocessing import Pool
from typing import Dict, List

import networkx as nx

from Components.routing.configurations import POLICY_BUILDERS
from Components.topology.utils import clear_congestions
from Components.workloads.congestion import CongestionType
from Components.workloads.workload import Workload
from Simulation.metrics.metric import Metric
from Simulation.run_epoch import run_epoch, build_epoch_context
from global_randoms import reset_randoms
from tqdm import tqdm

def run_simulation(
    *,
    topology: nx.Graph,
    metrics: List[Metric],
    congestion: CongestionType,
    policy_names: List[str],
    workload: Workload,
    epochs: int,
) -> Dict[str, float]:

    for m in metrics:
        m.reset()

    epoch_result = None

    ctx = build_epoch_context(topology)

    routing_schedule = [
        POLICY_BUILDERS[name](ctx)
        for name in policy_names
    ]

    for _ in tqdm(range(epochs)):

        # ------------------------------
        # Phase 0: update congestion
        # ------------------------------
        congestion(topology, epoch_result)

        # 🔥 Sync ctx arrays
        for eid, (u, v) in enumerate(ctx.edge_list):
            data = topology[u][v]
            ctx.congestion[eid] = data["congestion"]
            ctx.stale_congestion[eid] = data["stale_congestion"]

        # Notify engines
        for policy in routing_schedule:
            engine = getattr(policy, "engine", None)
            if engine:
                engine.epoch_tick()

        # ------------------------------
        # Generate flows
        # ------------------------------
        flows = workload.generate()

        # ------------------------------
        # Run epoch
        # ------------------------------
        epoch_result = run_epoch(
            flows=flows,
            routing_schedule=routing_schedule,
            ctx=ctx,
        )

        for m in metrics:
            m.process(epoch_result)

    results: Dict[str, float] = {}
    for m in metrics:
        results.update(m.result())

    clear_congestions(topology)
    reset_randoms()

    return results