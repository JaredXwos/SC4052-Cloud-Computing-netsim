from collections import defaultdict


class Throughput:
    def __init__(self): self.delivered = 0.0
    def reset(self): self.delivered = 0.0
    def process(self, epoch): self.delivered += epoch.total_sent - epoch.total_dropped
    def result(self): return {"throughput": self.delivered}

class OfferedLoad:
    def __init__(self): self.offered = 0.0
    def reset(self): self.offered = 0.0
    def process(self, epoch): self.offered += epoch.total_sent
    def result(self): return {"offered_load": self.offered}

class TrafficWeightedUtilization:
    def __init__(self):
        self.sum_load = 0.0
        self.sum_cap = 0.0

    def reset(self):
        self.sum_load = 0.0
        self.sum_cap = 0.0

    def process(self, epoch):
        for e, cap in epoch.edge_capacity.items():
            load = epoch.edge_load.get(e, 0.0)

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