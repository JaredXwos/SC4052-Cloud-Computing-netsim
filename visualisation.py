import matplotlib.pyplot as plt
import networkx as nx

from Components.host import generate_hosts
from Components.topology.configuration import topology_configuration


def draw_topology(topology):
    """
    Draw graph using node 'layer' metadata.

    Requirements:
        each node has:
            layer : int
            type  : "host" | "switch"
    """

    # --------------------------------------------------------
    # build layered positions
    # --------------------------------------------------------

    pos = {}

    layers = {}

    for node, data in topology.nodes(data=True):
        layer = data.get("layer", 0)
        layers.setdefault(layer, []).append(node)

    # place nodes row by row
    for layer, nodes in layers.items():
        count = len(nodes)

        for i, node in enumerate(nodes):
            # spread horizontally and center
            x = i - count / 2
            y = layer
            pos[node] = (x, y)

    # --------------------------------------------------------
    # draw
    # --------------------------------------------------------

    hosts = [n for n, d in topology.nodes(data=True) if d["type"] == "host"]
    switches = [n for n, d in topology.nodes(data=True) if d["type"] == "switch"]

    nx.draw_networkx_edges(topology, pos, alpha=0.25)

    nx.draw_networkx_nodes(
        topology, pos,
        nodelist=switches,
        node_color="tab:orange",
        node_size=80,
    )

    nx.draw_networkx_nodes(
        topology, pos,
        nodelist=hosts,
        node_color="tab:blue",
        node_size=30,
    )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig("topology.svg", bbox_inches="tight")
    plt.show()


def draw_jellyfish(topology):

    import networkx as nx
    import matplotlib.pyplot as plt
    import numpy as np

    switches = [n for n,d in topology.nodes(data=True) if d["type"]=="switch"]
    hosts = [n for n,d in topology.nodes(data=True) if d["type"]=="host"]

    # ----------------------------------------
    # Layout ONLY the switch fabric
    # ----------------------------------------

    switch_graph = topology.subgraph(switches)

    pos = nx.spring_layout(
        switch_graph,
        k=0.15,
        iterations=40,
        seed=42
    )

    # ----------------------------------------
    # Radially place hosts around switch
    # ----------------------------------------

    for sw in switches:

        nbrs = [n for n in topology.neighbors(sw)
                if topology.nodes[n]["type"]=="host"]

        if not nbrs:
            continue

        cx, cy = pos[sw]

        r = 0.15
        for i, h in enumerate(nbrs):

            theta = 2*np.pi*i/len(nbrs)

            pos[h] = (
                cx + r*np.cos(theta),
                cy + r*np.sin(theta)
            )

    # ----------------------------------------
    # Draw
    # ----------------------------------------

    nx.draw_networkx_edges(topology, pos, alpha=0.1)

    nx.draw_networkx_nodes(
        topology, pos,
        nodelist=switches,
        node_color="tab:orange",
        node_size=60
    )

    nx.draw_networkx_nodes(
        topology, pos,
        nodelist=hosts,
        node_color="tab:blue",
        node_size=20
    )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig("jellyfish.svg")
    plt.show()

hosts = generate_hosts(16)
draw_jellyfish(topology_configuration["jellyfish"](hosts,switch_degree=4, n_switches=20))