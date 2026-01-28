import random
from typing import Callable

import global_randoms

import networkx as nx

from Components.topology.utils import get_capacity
from Simulation.epoch_result import EpochResult

CongestionType = Callable[[nx.Graph, EpochResult], None]

def _roll_congestion(topology: nx.Graph) -> None:
    """
    Move edge['congestion'] → edge['stale_congestion'].
    Initialize missing fields safely.
    """
    for _, _, data in topology.edges(data=True):
        data["stale_congestion"] = data.get("congestion", 0.0)

def congestion_uniform(
    *,
    low: float = 0.0,
    high: float = 1.0,
) -> CongestionType:
    """
    Factory that returns a congestion function.

    Each epoch:
        congestion ~ U(low, high)
    """
    def apply(topology: nx.Graph, epoch_result: EpochResult=None) -> None:
        _roll_congestion(topology)

        for _, _, data in topology.edges(data=True):
            data["congestion"] = global_randoms.congestion.uniform(low, high)

    return apply

def congestion_ar1(
    *,
    alpha: float = 0.85,      # memory
    noise_scale: float = 1.0,
) -> CongestionType:
    """
    Factory returning AR(1) temporal congestion.

    congestion_t = alpha * stale + (1-alpha) * noise
    """
    def apply(topology: nx.Graph, epoch_result: EpochResult = None) -> None:
        _roll_congestion(topology)

        for _, _, data in topology.edges(data=True):
            stale = data["stale_congestion"]
            noise = global_randoms.workload.random() * noise_scale

            data["congestion"] = alpha * stale + (1.0 - alpha) * noise

    return apply

def carry_over(alpha: float = 0.9):

    def apply(topology: nx.Graph, epoch_result: EpochResult = None) -> None:
        for u, v, data in topology.edges(data=True):
            if epoch_result is None:
                data["congestion"] = 0
                data["stale_congestion"] = 0
            else:
                cap = get_capacity(topology, u, v)
                load = epoch_result.edge_load.get((u, v), 0.0)

                util = load / cap if cap > 0 else 0.0

                stale = data.get("congestion", 0.0)

                data["stale_congestion"] = stale
                data["congestion"] = alpha * stale + (1 - alpha) * util

    return apply
