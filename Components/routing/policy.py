import time
from typing import Callable

import networkx as nx

import global_randoms
from Components.routing import weights, multipath
from Components.routing.multipath import ShortestPathEngine
from Components.routing.weights import hop_weight_builder
from Components.topology.topology_types import Node, Path

RoutingPolicy = Callable[[nx.Graph, Node, Node], Path]

rip = multipath.no_multipath(weights.hop_weight_builder)
ospf = multipath.no_multipath(weights.ospf_weight_builder)
eigrp = multipath.no_multipath(weights.eigrp_weight_builder)
stale_ospf = multipath.no_multipath(weights.stale_ospf_weight_builder)
stale_eigrp = multipath.no_multipath(weights.stale_eigrp_weight_builder)

rip_ecmp = multipath.ecmp(weights.hop_weight_builder)
ospf_ecmp = multipath.ecmp(weights.ospf_weight_builder)
eigrp_ecmp = multipath.ecmp(weights.eigrp_weight_builder)
stale_ospf_ecmp = multipath.ecmp(weights.stale_ospf_weight_builder)
stale_eigrp_ecmp = multipath.ecmp(weights.stale_eigrp_weight_builder)

rip_drill = multipath.drill(weights.hop_weight_builder)
ospf_drill = multipath.drill(weights.ospf_weight_builder)
eigrp_drill = multipath.drill(weights.eigrp_weight_builder)
stale_ospf_drill = multipath.drill(weights.stale_ospf_weight_builder)
stale_eigrp_drill = multipath.drill(weights.stale_eigrp_weight_builder)
def conga_policy(weight_builder, rel_threshold=0.05, k_samples=30):

    def build(ctx):

        engine = ShortestPathEngine(ctx, weight_builder, rel_threshold)

        # Per-source cache
        route_cache = {}

        uv2eid = ctx.edge_id
        cap = ctx.capacity
        cong = ctx.congestion
        rng = global_randoms.multipath

        # --------------------------------------------
        # Path congestion cost (sum utilization)
        # --------------------------------------------
        def path_cost(path):
            total = 0.0
            for u, v in zip(path[:-1], path[1:]):
                eid = uv2eid[(u, v)]
                denom = cap[eid]
                util = cong[eid] / denom if denom > 0 else 1.0
                total += util
            return total

        # --------------------------------------------
        # Policy
        # --------------------------------------------
        def policy(src, dst):

            if src == dst:
                return [src]

            if engine.changed:
                route_cache.clear()
                engine.changed = False

            # Compute DAG once per source per epoch
            if src not in route_cache:

                preds, dist, order = engine.compute_dag(src)

                # Precompute ECMP counts once
                count = {src: 1}
                for n in order:
                    if n == src:
                        continue
                    total = 0
                    for p in preds.get(n, []):
                        total += count.get(p, 0)
                    if total > 0:
                        count[n] = total

                route_cache[src] = {
                    "preds": preds,
                    "count": count,
                    "paths": {}
                }

            data = route_cache[src]
            preds = data["preds"]
            count = data["count"]
            path_cache = data["paths"]

            if dst in path_cache:
                return path_cache[dst]

            if dst not in preds or count.get(dst, 0) == 0:
                path_cache[dst] = []
                return []

            # --------------------------------------------
            # Sample K ECMP paths
            # --------------------------------------------
            best_path = None
            best_cost = float("inf")

            for _ in range(k_samples):

                node = dst
                path = [dst]

                while node != src:

                    ps = preds[node]
                    valid = []
                    weights = []

                    for p in ps:
                        w = count.get(p, 0)
                        if w > 0:
                            valid.append(p)
                            weights.append(w)

                    if not valid:
                        path = []
                        break

                    node = rng.choices(valid, weights=weights)[0]
                    path.append(node)

                if not path:
                    continue

                path.reverse()
                cost = path_cost(path)

                if cost < best_cost:
                    best_cost = cost
                    best_path = path

            path_cache[dst] = best_path
            return best_path

        policy.epoch_tick = engine.epoch_tick
        policy.engine = engine

        return policy

    return build

conga = conga_policy(hop_weight_builder)