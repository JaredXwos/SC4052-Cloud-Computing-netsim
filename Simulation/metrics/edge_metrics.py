import math


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

class EdgeUtilizationStd:
    def __init__(self):
        self.sum_u = 0.0
        self.sum_u2 = 0.0
        self.count = 0

    def reset(self):
        self.sum_u = 0.0
        self.sum_u2 = 0.0
        self.count = 0

    def process(self, epoch):
        for e, cap in epoch.edge_capacity.items():
            if cap <= 0:
                continue

            load = epoch.edge_load.get(e, 0.0)
            u = load / cap

            self.sum_u += u
            self.sum_u2 += u * u
            self.count += 1

    def result(self):
        if self.count == 0:
            return {"edge_util_std": 0.0}

        mean = self.sum_u / self.count
        var = self.sum_u2 / self.count - mean * mean
        std = math.sqrt(max(var, 0.0))

        return {"edge_util_std": std}

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