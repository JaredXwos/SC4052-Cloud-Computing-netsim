def hop_weight(u, v, d):
    return 1.0

def latency_weight(u, v, d):
    return d["latency"]

def ospf_weight(u, v, d):
    return 1.0 / (d["capacity"] - d["congestion"])

def eigrp_weight(u, v, d, alpha=1.0, beta=1.0):
    return alpha * d["latency"] + beta * (1.0 / (d["capacity"] - d["congestion"]))

def stale_ospf_weight(u, v, d):
    return 1.0 / (d["capacity"] - d["stale_congestion"])

def stale_eigrp_weight(u, v, d, alpha=1.0, beta=1.0):
    return alpha * d["latency"] + beta * (1.0 / (d["capacity"] - d["stale_congestion"]))