from typing import Protocol, runtime_checkable, Iterable
from typing import Dict
from Simulation.epoch_result import EpochResult
from Simulation.metrics.edge_metrics import *
from Simulation.metrics.flow_metrics import *
from Simulation.metrics.general_metrics import *
from Simulation.metrics.switch_metrics import *


@runtime_checkable
class Metric(Protocol):
    """
    Structural interface for streaming metrics.

    process()  -> consume one epoch
    result()   -> return final scalar(s)
    reset()    -> optional reuse
    """

    def process(self, epoch: "EpochResult") -> None: ...
    def result(self) -> Dict[str, float]: ...
    def reset(self) -> None: ...

class AllMetrics:
    metrics: Iterable[Metric]
    def __init__(self):
        self.metrics = [
        DropRatio(),
        MeanLatency(),
        OfferedLoad(),
        JainFairness(),
        FlowRatePercentiles(),
        EdgeUtilization(),
        MeanHopCount(),
        SaturatedEdges(),
        Throughput(),
        TrafficWeightedUtilization(),
        HotspotShare(),
        LoadCapTotals(),
        EdgeUtilizationStd(),
        SwitchUtilStd(),
        SwitchUtilGini(),
        HotSwitchFraction(),
        MeanSwitchUtil(),
        P95SwitchUtil(),
    ]

    def process(self, epoch: "EpochResult") -> None:
        for metric in self.metrics:
            metric.process(epoch)

    def result(self) -> Dict[str, float]:
        result = {}
        for metric in self.metrics:
            result |= metric.result()
        return result

    def reset(self) -> None:
        for metric in self.metrics:
            metric.reset()