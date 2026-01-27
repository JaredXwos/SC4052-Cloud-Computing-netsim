import networkx as nx
def add_link_alias(topology: nx.Graph, capacity: float, latency: float):
    """
    Return a small helper function:

        add_link(u, v)

    that adds an edge with standard attributes.

    Uses closure to capture:
        - graph
        - capacity
        - latency
    """

    def add_link(u, v):
        topology.add_edge(
            u,
            v,
            capacity=capacity,
            latency=latency,
            load=0.0,
        )

    return add_link

def get_capacity(topology, u, v) -> float:
    return float(topology[u][v]["capacity"])