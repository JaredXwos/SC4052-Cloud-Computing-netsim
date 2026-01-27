def hop_weight(u, v, d):
    return 1.0

def latency_weight(u, v, d):
    return d["latency"]

def ospf_weight(u, v, d):
    return 1.0 / d["base_capacity"]

def eigrp_weight(u, v, d, alpha=1.0, beta=1.0):
    return alpha * d["base_latency"] + beta * (1.0 / d["base_capacity"])