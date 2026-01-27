from typing import List, Tuple, Protocol
import random
from Components.host import Host
from Components.workloads.flow import Flow


class Workload(Protocol):
    """
    Generate traffic for a single epoch.

    Returns:
    List of flows:
        (src_id, dst_id, rate)
    """
    def generate(self) -> List[Flow]: ...

class RandomWorkload:
    """
    Simple synthetic workload for testing the simulator.

    Behaviour:
    No host tagging
    Random src to dst flows with constant rate
    """

    hosts: List[Host]
    flows_per_epoch: int
    data_per_epoch: float #constant

    def __init__(
        self,
        hosts: List[Host],
        flows_per_epoch: int = 50,
        rate: float = 1.0,
    ) -> None:
        self.hosts = hosts
        self.flows_per_epoch = flows_per_epoch
        self.data_per_epoch = rate

    def generate(self) -> List[Flow]:

        flows: List[Flow] = []

        for _ in range(self.flows_per_epoch):
            src, dst = random.sample(self.hosts, 2)
            flows.append(Flow(src.id, dst.id, self.data_per_epoch))

        return flows