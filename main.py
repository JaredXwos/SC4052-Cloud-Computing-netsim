from Components.routing.policy import ospf_ecmp, ospf_drill, conga
from Components.topology.fat_tree import build_fat_tree, build_fat_tree_informed
from Components.host import generate_hosts
from Components.topology.jellyfish import build_jellyfish
from Components.topology.leaf_spine import build_leaf_spine, build_leaf_spine_informed
from Components.workloads.congestion import congestion_ar1, carry_over
from Components.workloads.workload import *
from Simulation.metrics.metric import AllMetrics
from Simulation.run_simulation import run_simulation


def main():


    num_hosts = 128
    hosts = generate_hosts(num_hosts)
    print(f"Generated {len(hosts)} hosts")
    metrics = [AllMetrics()]
    congestion = carry_over()

    workload = AR1StrictLocalGroupWorkload(hosts, flows_per_epoch=10, rate=15, alpha=0.9)
    topology = build_fat_tree_informed(hosts)
    print(f"Graph: {topology.number_of_nodes()} nodes, {topology.number_of_edges()} edges")
    results = run_simulation(
        topology=topology,
        metrics=metrics,
        congestion=congestion,
        routing_policies=[conga],
        workload=workload,
        epochs=10,
    )

    print("Simulation results:")
    for k, v in results.items():
        print(f"{k:20s} : {v:.4f}")



if __name__ == "__main__":
    main()
