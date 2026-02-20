import global_randoms
import heapq
import itertools


class ShortestPathEngine:

    def __init__(self, ctx, weight_builder, rel_threshold=0.05):
        self.ctx = ctx
        self.weight_fn = weight_builder(ctx)
        self.rel_threshold = rel_threshold

        self.last_w = {}
        self.changed = False
        self.epoch_initialized = False

    def epoch_tick(self):
        changed = False

        for eid in range(len(self.ctx.edge_list)):
            w = self.weight_fn(eid)
            old = self.last_w.get(eid)
            self.last_w[eid] = w

            if old is None:
                continue

            rel = abs(w - old) / old if old != 0 else abs(w - old)
            if rel > self.rel_threshold:
                changed = True
                break

        self.changed = changed
        self.epoch_initialized = True

    # -------------------------------------------------
    # Optimised Dijkstra
    # Returns order in nondecreasing distance
    # -------------------------------------------------
    def compute_dag(self, src, eps=1e-12):

        counter = itertools.count()

        dist = {src: 0.0}
        preds = {src: []}
        order = []

        heap = [(0.0, next(counter), src)]

        while heap:
            d, _, u = heapq.heappop(heap)

            if d > dist[u] + eps:
                continue

            order.append(u)

            for v, eid in self.ctx.adj[u]:
                nd = d + self.weight_fn(eid)
                old = dist.get(v)

                if old is None or nd < old - eps:
                    dist[v] = nd
                    preds[v] = [u]
                    heapq.heappush(heap, (nd, next(counter), v))

                elif abs(nd - old) <= eps:
                    preds[v].append(u)

        return preds, dist, order


# =====================================================
# NO MULTIPATH
# =====================================================

def no_multipath(weight_builder, rel_threshold=0.05):

    def build(ctx):
        engine = ShortestPathEngine(ctx, weight_builder, rel_threshold)

        # Cache per source
        route_cache = {}

        def policy(src, dst):

            if src == dst:
                return [src]

            if engine.changed:
                route_cache.clear()
                engine.changed = False

            # Compute once per source
            if src not in route_cache:
                preds, dist, _ = engine.compute_dag(src)
                route_cache[src] = preds

            preds = route_cache[src]

            if dst not in preds:
                return []

            node = dst
            path = [dst]

            while node != src:
                ps = preds.get(node)
                if not ps:
                    return []
                node = ps[0]   # deterministic
                path.append(node)

            path.reverse()
            return path

        policy.epoch_tick = engine.epoch_tick
        policy.engine = engine
        return policy

    return build


# =====================================================
# ECMP (Optimised: Per-Source Cache, No Sorting)
# =====================================================

def ecmp(weight_builder, rel_threshold=0.05):

    def build(ctx):
        engine = ShortestPathEngine(ctx, weight_builder, rel_threshold)

        # Cache per source only
        route_cache = {}

        def policy(src, dst):

            if src == dst:
                return [src]

            if engine.changed:
                route_cache.clear()
                engine.changed = False

            # Compute once per source
            if src not in route_cache:

                preds, dist, order = engine.compute_dag(src)

                # Compute ECMP counts once
                count = {src: 1}

                for n in order:
                    if n == src:
                        continue

                    total = 0
                    for p in preds.get(n, []):
                        total += count.get(p, 0)

                    if total > 0:
                        count[n] = total

                route_cache[src] = (preds, count)

            preds, count = route_cache[src]

            if dst not in preds or count.get(dst, 0) == 0:
                return []

            node = dst
            path = [dst]

            while node != src:

                ps = preds.get(node, [])
                valid = []
                weights = []

                for p in ps:
                    w = count.get(p, 0)
                    if w > 0:
                        valid.append(p)
                        weights.append(w)

                if not valid:
                    return []

                node = global_randoms.multipath.choices(valid, weights=weights)[0]
                path.append(node)

            path.reverse()
            return path

        policy.epoch_tick = engine.epoch_tick
        policy.engine = engine
        return policy

    return build


# =====================================================
# DRILL (Optimised: Per-Source DAG Reuse)
# =====================================================

def drill(weight_builder, rel_threshold=0.05):

    def build(ctx):
        engine = ShortestPathEngine(ctx, weight_builder, rel_threshold)

        route_cache = {}

        cap = ctx.capacity
        cong = ctx.congestion
        edge_id = ctx.edge_id
        rng = global_randoms.multipath

        def path_cost(path):
            worst = 0.0
            for u, v in zip(path, path[1:]):
                eid = edge_id[(u, v)]
                denom = cap[eid]
                util = cong[eid] / denom if denom > 0 else 1.0
                if util > worst:
                    worst = util
            return worst

        def policy(src, dst):

            if src == dst:
                return [src]

            if engine.changed:
                route_cache.clear()
                engine.changed = False

            key = (src, dst)
            if key in route_cache:
                return route_cache[key]

            # Compute full DAG once per src per epoch
            if src not in route_cache:

                preds, dist, order = engine.compute_dag(src)

                count = {src: 1}
                for n in order:
                    if n == src:
                        continue
                    total = 0
                    for p in preds.get(n, []):
                        total += count.get(p, 0)
                    if total > 0:
                        count[n] = total

                route_cache[src] = (preds, count)

            preds, count = route_cache[src]

            if dst not in preds:
                return []

            def sample():
                node = dst
                path = [dst]
                while node != src:
                    ps = preds[node]
                    weights = [count.get(p, 0) for p in ps]
                    node = rng.choices(ps, weights=weights)[0]
                    path.append(node)
                path.reverse()
                return path

            p1 = sample()
            p2 = sample()

            best = p1 if path_cost(p1) < path_cost(p2) else p2
            route_cache[(src, dst)] = best
            return best

        policy.epoch_tick = engine.epoch_tick
        policy.engine = engine
        return policy

    return build
