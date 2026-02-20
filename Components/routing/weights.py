def hop_weight_builder(ctx):
    return lambda eid: 1.0

def latency_weight_builder(ctx):
    latency = ctx.latency
    return lambda eid: latency[eid]

def ospf_weight_builder(ctx):
    cap = ctx.capacity
    cong = ctx.congestion

    def weight(eid):
        denom = cap[eid] - cong[eid]
        return 1.0 / denom if denom > 0 else 1e9

    return weight

def eigrp_weight_builder(ctx, alpha=1.0, beta=1.0):
    cap = ctx.capacity
    cong = ctx.congestion
    lat = ctx.latency

    def weight(eid):
        denom = cap[eid] - cong[eid]
        inv = 1.0 / denom if denom > 0 else 1e9
        return alpha * lat[eid] + beta * inv

    return weight

def stale_ospf_weight_builder(ctx):
    cap = ctx.capacity
    stale = ctx.stale_congestion

    def weight(eid):
        denom = cap[eid] - stale[eid]
        return 1.0 / denom if denom > 0 else 1e9

    return weight

def stale_eigrp_weight_builder(ctx, alpha=1.0, beta=1.0):
    cap = ctx.capacity
    stale = ctx.stale_congestion
    lat = ctx.latency

    def weight(eid):
        denom = cap[eid] - stale[eid]
        inv = 1.0 / denom if denom > 0 else 1e9
        return alpha * lat[eid] + beta * inv

    return weight