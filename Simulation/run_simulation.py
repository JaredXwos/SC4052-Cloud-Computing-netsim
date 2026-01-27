from typing import Iterable, Dict, List

import networkx as nx

from Components.routing.policy import RoutingPolicy
from Components.workloads.congestion import CongestionType
from Components.workloads.workload import Workload
from Simulation.metric import Metric
from Simulation.run_epoch import run_epoch


def run_simulation(
    *,
    topology: nx.Graph,
    metrics: List[Metric],
    congestion: CongestionType,
    routing_policies: List[RoutingPolicy],
    workload: Workload,
    epochs: int,
) -> Dict[str, float]:
    """
    Run one simulation trajectory.

    Orchestrates:
        congestion -> workload -> routing/epoch -> metrics

    Returns:
        dict of metric_name -> value
    """

    # Reset stateful components
    for m in metrics:
        m.reset()

    for _ in range(epochs):

        # 1) update congestion
        congestion(topology)

        # 2) generate workload
        flows = workload.generate()

        # 3) execute epoch
        epoch_result = run_epoch(topology, flows, routing_policies)

        # 4) update metrics
        for m in metrics:
            m.process(epoch_result)

    # collect results
    results: Dict[str, float] = {}
    for m in metrics:
        results.update(m.result())

    return results