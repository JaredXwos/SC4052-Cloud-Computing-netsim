from typing import List, Tuple
import random
from Components.host import Host

class RandomWorkload:
    """
    Simple synthetic workload for testing the simulator.

    Behaviour:
    No host tagging
    Random src to dst flows with constant rate
    """

    hosts: List[Host]

    flows_per_epoch: int
    """
    Number of flows to generate every epoch.
    Controls overall offered load.
    """

    data_per_epoch: float
    """
    Traffic rate per flow, given in units per epoch.
    """

    def __init__(
        self,
        hosts: List[Host],
        flows_per_epoch: int = 50,
        rate: float = 1.0,
    ) -> None:
        self.hosts = hosts
        self.flows_per_epoch = flows_per_epoch
        self.data_per_epoch = rate

    def generate(self) -> List[Tuple[int, int, float]]:
        """
        Generate traffic for a single epoch.

        Returns:
        List of flows:
            (src_id, dst_id, rate)
        """

        flows: List[Tuple[int, int, float]] = []

        for _ in range(self.flows_per_epoch):
            src, dst = random.sample(self.hosts, 2)
            flows.append((src.id, dst.id, self.data_per_epoch))

        return flows