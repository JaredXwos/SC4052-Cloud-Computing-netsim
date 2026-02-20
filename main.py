import random

from Components.routing.configurations import policy_configuration
from Components.topology.configuration import topology_configuration
from Components.host import generate_hosts
from Components.workloads.configuration import workload_configuration
from Components.workloads.congestion import carry_over
from Simulation.metrics.metric import AllMetrics
from Simulation.run_simulation import run_simulation
import argparse

def parse_args():
    p = argparse.ArgumentParser()

    p.add_argument("--topology", choices=topology_configuration.keys(), required=True)
    p.add_argument("--workload", choices=workload_configuration.keys(), required=True)
    p.add_argument("--policy", choices=policy_configuration.keys(), required=True)

    p.add_argument("--hosts", type=int, default=128)
    p.add_argument("--flows", type=int, default=3000)
    p.add_argument("--rate", type=float, default=15)
    p.add_argument("--alpha", type=float, default=0.9)
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--seed", type=int, default=0)

    return p.parse_args()

def main():
    args = parse_args()
    random.seed(args.seed)

    # ----- setup -----
    hosts = generate_hosts(args.hosts)
    print(f"Generated {len(hosts)} hosts")

    metrics = [AllMetrics()]
    congestion = carry_over()

    # workload from registry
    workload_cls = workload_configuration[args.workload]
    workload = workload_cls(
        hosts,
        flows_per_epoch=args.flows,
        rate=args.rate,
        alpha=args.alpha,
    )

    # topology from registry
    topology = topology_configuration[args.topology](hosts)
    for _, _, data in topology.edges(data=True):
        data.setdefault("congestion", 0.0)
        data.setdefault("stale_congestion", 0.0)
    print(f"Graph: {topology.number_of_nodes()} nodes, {topology.number_of_edges()} edges")

    policy_names = policy_configuration[args.policy]

    # ----- run -----
    results = run_simulation(
        topology=topology,
        metrics=metrics,
        congestion=congestion,
        policy_names=policy_names,
        workload=workload,
        epochs=args.epochs
    )

    # ----- print -----
    print("\n=== Simulation Results ===")
    print(f"topology : {args.topology}")
    print(f"workload : {args.workload}")
    print(f"policy   : {args.policy}")
    print()

    for k, v in results.items():
        print(f"{k:20s} : {v:.4f}")


if __name__ == "__main__":
    main()
