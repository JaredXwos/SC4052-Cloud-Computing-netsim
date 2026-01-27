import matplotlib.pyplot as plt
import networkx as nx

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