import random
from typing import Callable

import networkx as nx

CongestionType = Callable[[nx.Graph], None]

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

    def apply(topology: nx.Graph) -> None:
        _roll_congestion(topology)

        for _, _, data in topology.edges(data=True):
            data["congestion"] = random.uniform(low, high)

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

    def apply(topology: nx.Graph) -> None:
        _roll_congestion(topology)

        for _, _, data in topology.edges(data=True):
            stale = data["stale_congestion"]
            noise = random.random() * noise_scale

            data["congestion"] = alpha * stale + (1.0 - alpha) * noise

    return apply