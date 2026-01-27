from Components.routing.policy import eigrp, eigrp_drill, ospf_ecmp, ospf_drill
from Components.topology.fat_tree import build_fat_tree
from Components.host import generate_hosts
from Components.workloads.congestion import congestion_ar1
from Components.workloads.workload import RandomWorkload
from Simulation import metric
from Simulation.run_simulation import run_simulation
from visualisation import draw_topology

def main():


    num_hosts = 128
    hosts = generate_hosts(num_hosts)
    print(f"Generated {len(hosts)} hosts")

    topology = build_fat_tree(hosts)
    print(f"Graph: {topology.number_of_nodes()} nodes, {topology.number_of_edges()} edges")

    workload = RandomWorkload(
        hosts=hosts,
        flows_per_epoch=800,
        rate=10,
    )

    metrics = [
        metric.DropRatio(),
        metric.MeanLatency(),
        metric.OfferedLoad(),
        metric.JainFairness(),
        metric.FlowRatePercentiles(),
        metric.EdgeUtilization(),
        metric.MeanHopCount(),
        metric.SaturatedEdges(),
        metric.Throughput(),
        metric.TrafficWeightedUtilization(),
        metric.HotspotShare(),
        metric.LoadCapTotals()
    ]

    congestion = congestion_ar1(alpha=0.9, noise_scale=0.5)

    results = run_simulation(
        topology=topology,
        metrics=metrics,
        congestion=congestion,
        routing_policies=[ospf_drill],
        workload=workload,
        epochs=100,
    )

    print("Simulation results:")
    for k, v in results.items():
        print(f"{k:20s} : {v:.4f}")

    results = run_simulation(
        topology=topology,
        metrics=metrics,
        congestion=congestion,
        routing_policies=[ospf_ecmp],
        workload=workload,
        epochs=100,
    )

    print("Simulation results:")
    for k, v in results.items():
        print(f"{k:20s} : {v:.4f}")

if __name__ == "__main__":
    main()
