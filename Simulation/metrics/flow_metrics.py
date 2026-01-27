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