class Metric:
    name: str

    def compute(self, result) -> float:
        raise NotImplementedError

class Throughput(Metric):
    name = "throughput"

    def compute(self, result):
        return sum(
            sum(epoch.flow_rates) - epoch.dropped
            for epoch in result
        )

class MaxLinkUtilization(Metric):
    name = "max_util"

    def compute(self, result):
        return max(
            max(load for load in epoch.edge_loads.values())
            for epoch in result
        )

class AvgLatency(Metric):
    name = "latency"

    def compute(self, result):
        total_lat = sum(epoch.latency_sum for epoch in result)
        total_flows = sum(len(epoch.flow_paths) for epoch in result)
        return total_lat / total_flows