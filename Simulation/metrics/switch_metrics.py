import math

def _switch_utils(epoch):
    for s, load in epoch.switch_load.items():
        cap = epoch.switch_capacity.get(s, 0.0)
        if cap > 0:
            yield load / cap

class MeanSwitchUtil:
    def __init__(self):
        self.sum = 0.0
        self.count = 0

    def reset(self):
        self.sum = 0.0
        self.count = 0

    def process(self, epoch):
        for u in _switch_utils(epoch):
            self.sum += u
            self.count += 1

    def result(self):
        return {"mean_switch_util": self.sum / self.count if self.count else 0.0}

class SwitchUtilStd:
    def __init__(self):
        self.sum = self.sum2 = 0.0
        self.count = 0

    def reset(self):
        self.sum = self.sum2 = 0.0
        self.count = 0

    def process(self, epoch):
        for u in _switch_utils(epoch):
            self.sum += u
            self.sum2 += u*u
            self.count += 1

    def result(self):
        if self.count == 0:
            return {"switch_util_std": 0.0}

        mean = self.sum / self.count
        var = self.sum2 / self.count - mean*mean
        return {"switch_util_std": math.sqrt(max(var, 0.0))}

class MaxSwitchUtil:
    def __init__(self):
        self.max_u = 0.0

    def reset(self):
        self.max_u = 0.0

    def process(self, epoch):
        for u in _switch_utils(epoch):
            self.max_u = max(self.max_u, u)

    def result(self):
        return {"max_switch_util": self.max_u}

class P95SwitchUtil:
    def __init__(self):
        self.values = []

    def reset(self):
        self.values.clear()

    def process(self, epoch):
        self.values.extend(_switch_utils(epoch))

    def result(self):
        if not self.values:
            return {"p95_switch_util": 0.0}

        v = sorted(self.values)
        idx = int(0.95 * (len(v) - 1))
        return {"p95_switch_util": v[idx]}

class HotSwitchFraction:
    def __init__(self, threshold=0.9):
        self.th = threshold
        self.hot = self.total = 0

    def reset(self):
        self.hot = self.total = 0

    def process(self, epoch):
        for u in _switch_utils(epoch):
            self.total += 1
            if u >= self.th:
                self.hot += 1

    def result(self):
        return {"frac_hot_switches": self.hot / self.total if self.total else 0.0}

class SwitchUtilGini:
    def __init__(self):
        self.values = []

    def reset(self):
        self.values.clear()

    def process(self, epoch):
        self.values.extend(_switch_utils(epoch))

    def result(self):
        if not self.values:
            return {"switch_util_gini": 0.0}

        v = sorted(self.values)
        n = len(v)
        cum = 0
        for i, x in enumerate(v, 1):
            cum += i * x

        gini = (2 * cum) / (n * sum(v)) - (n + 1) / n if sum(v) > 0 else 0
        return {"switch_util_gini": gini}