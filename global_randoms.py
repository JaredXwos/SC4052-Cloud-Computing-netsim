import random

seed = 42
master = random.Random(seed)
workload = random.Random(master.randrange(2**32))
topology = random.Random(master.randrange(2**32))
weights = random.Random(master.randrange(2**32))
policy = random.Random(master.randrange(2**32))
multipath = random.Random(master.randrange(2**32))
congestion = random.Random(master.randrange(2**32))

def reset_randoms():
    global master, workload, topology, weights, policy, multipath, congestion
    master = random.Random(seed)
    workload = random.Random(master.randrange(2 ** 32))
    topology = random.Random(master.randrange(2 ** 32))
    weights = random.Random(master.randrange(2 ** 32))
    policy = random.Random(master.randrange(2 ** 32))
    multipath = random.Random(master.randrange(2 ** 32))
    congestion = random.Random(master.randrange(2 ** 32))