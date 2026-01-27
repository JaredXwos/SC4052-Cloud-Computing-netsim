from dataclasses import dataclass
from typing import Dict, Tuple, List, Hashable


Node = Hashable
Edge = Tuple[Node, Node]


@dataclass(slots=True)
class EpochResult:
    """
    Snapshot of network behaviour for ONE epoch.

    This is the ONLY object metrics read from.
    It must contain all observable outcomes,
    but no routing/topology internals.
    """

    # Link statistics (core)

    # total traffic sent through each edge (bytes or rate)
    edge_load: Dict[Edge, float]

    # static capacity (copied once for convenience)
    edge_capacity: Dict[Edge, float]

    # overflow traffic
    edge_dropped: Dict[Edge, float]

    # Flow statistics

    # actual path used for each flow
    flow_paths: List[List[Node]]

    # traffic volume per flow
    flow_rates: List[float]

    # total latency experienced
    flow_latency: List[float]
