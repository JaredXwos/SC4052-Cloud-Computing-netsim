from collections import defaultdict
from typing import Protocol, runtime_checkable
from typing import Dict
from Simulation.epoch_result import EpochResult


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

class DropRatio:
    def __init__(self):
        self.sent = 0.0
        self.dropped = 0.0

    def process(self, epoch):
        self.sent += epoch.total_sent
        self.dropped += epoch.total_dropped

    def result(self):
        ratio = self.dropped / self.sent if self.sent else 0.0
        return {"drop_ratio": ratio}

    def reset(self):
        self.sent = 0.0
        self.dropped = 0.0

class MeanLatency:
    def __init__(self):
        self.sum = 0.0
        self.count = 0

    def process(self, epoch):
        self.sum += sum(epoch.flow_latency)
        self.count += len(epoch.flow_latency)

    def result(self):
        mean = self.sum / self.count if self.count else 0.0
        return {"mean_latency": mean}

    def reset(self):
        self.sum = 0.0
        self.count = 0

class JainFairness:
    def __init__(self):
        self.sum = 0.0
        self.sum_sq = 0.0
        self.n = 0

    def process(self, epoch):
        for r in epoch.flow_rates:
            self.sum += r
            self.sum_sq += r * r
            self.n += 1

    def result(self):
        if self.n == 0 or self.sum_sq == 0:
            fairness = 0.0
        else:
            fairness = (self.sum * self.sum) / (self.n * self.sum_sq)

        return {"jain_fairness": fairness}

    def reset(self):
        self.sum = self.sum_sq = 0.0
        self.n = 0

class EdgeUtilization:
    def __init__(self):
        self.total_load = 0.0
        self.total_capacity = 0.0

    def process(self, epoch):
        self.total_load += sum(epoch.edge_load.values())
        self.total_capacity += sum(epoch.edge_capacity.values())

    def result(self):
        util = (
            self.total_load / self.total_capacity
            if self.total_capacity else 0.0
        )
        return {"mean_edge_utilization": util}

    def reset(self):
        self.total_load = 0.0
        self.total_capacity = 0.0

class Throughput:
    def __init__(self):
        self.delivered = 0.0

    def reset(self):
        self.delivered = 0.0

    def process(self, epoch):
        self.delivered += epoch.total_sent - epoch.total_dropped

    def result(self):
        return {"throughput": self.delivered}

class OfferedLoad:
    def __init__(self): self.offered = 0.0
    def reset(self): self.offered = 0.0
    def process(self, epoch): self.offered += epoch.total_sent
    def result(self): return {"offered_load": self.offered}

class EdgeUtilization:
    def __init__(self):
        self.sum_util = 0.0
        self.count = 0
        self.max_util = 0.0

    def reset(self):
        self.sum_util = 0.0
        self.count = 0
        self.max_util = 0.0

    def process(self, epoch):
        for e, load in epoch.edge_load.items():
            cap = epoch.edge_capacity.get(e, 0.0)
            if cap > 0:
                util = load / cap
                self.sum_util += util
                self.count += 1
                if util > self.max_util:
                    self.max_util = util

    def result(self):
        mean_util = self.sum_util / self.count if self.count else 0.0
        return {
            "mean_edge_util": mean_util,
            "max_edge_util": self.max_util,
        }

class SaturatedEdges:
    def __init__(self):
        self.saturated = 0
        self.total = 0

    def reset(self):
        self.saturated = 0
        self.total = 0

    def process(self, epoch):
        for e, load in epoch.edge_load.items():
            cap = epoch.edge_capacity.get(e, 0.0)
            if cap > 0:
                self.total += 1
                if load / cap > 1.0:
                    self.saturated += 1

    def result(self):
        frac = self.saturated / self.total if self.total else 0.0
        return {"frac_saturated_edges": frac}

class MeanHopCount:
    def __init__(self):
        self.sum_hops = 0
        self.count = 0

    def reset(self):
        self.sum_hops = 0
        self.count = 0

    def process(self, epoch):
        for path in epoch.flow_paths:
            self.sum_hops += max(0, len(path) - 1)
            self.count += 1

    def result(self):
        mean_hops = self.sum_hops / self.count if self.count else 0.0
        return {"mean_hops": mean_hops}

class FlowRatePercentiles:
    def __init__(self):
        self.rates = []

    def reset(self):
        self.rates = []

    def process(self, epoch):
        self.rates.extend(epoch.flow_rates)

    def result(self):
        if not self.rates:
            return {"p50_flow_rate": 0.0, "p95_flow_rate": 0.0}
        xs = sorted(self.rates)
        def pct(p):
            i = int(p * (len(xs)-1))
            return xs[i]
        return {
            "p50_flow_rate": pct(0.50),
            "p95_flow_rate": pct(0.95),
        }

class TrafficWeightedUtilization:
    def __init__(self):
        self.sum_load = 0.0
        self.sum_cap = 0.0

    def reset(self):
        self.sum_load = 0.0
        self.sum_cap = 0.0

    def process(self, epoch):
        for e, load in epoch.edge_load.items():
            cap = epoch.edge_capacity.get(e, 0.0)
            if cap > 0:
                self.sum_load += load
                self.sum_cap += cap

    def result(self):
        util = self.sum_load / self.sum_cap if self.sum_cap else 0.0
        return {"traffic_weighted_util": util}

class HotspotShare:
    def __init__(self, k: int = 5):
        self.k = k
        self.edge_totals = defaultdict(float)

    def reset(self):
        self.edge_totals.clear()

    def process(self, epoch):
        for e, load in epoch.edge_load.items():
            self.edge_totals[e] += load

    def result(self):
        if not self.edge_totals:
            return {"topk_edge_load_share": 0.0}

        loads = list(self.edge_totals.values())
        total = sum(loads)
        topk = sum(sorted(loads, reverse=True)[: self.k])
        return {"topk_edge_load_share": topk / total if total else 0.0}

class LoadCapTotals:
    def __init__(self):
        self.sum_load = 0.0
        self.sum_cap = 0.0

    def reset(self):
        self.sum_load = 0.0
        self.sum_cap = 0.0

    def process(self, epoch):
        for e, load in epoch.edge_load.items():
            cap = epoch.edge_capacity.get(e, 0.0)
            if cap > 0:
                self.sum_load += load
                self.sum_cap += cap

    def result(self):
        return {
            "sum_edge_load": self.sum_load,
            "sum_edge_cap": self.sum_cap,
        }