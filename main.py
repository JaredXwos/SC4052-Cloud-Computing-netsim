from Components.topology.fat_tree import build_fat_tree
from Components.host import generate_hosts
from visualisation import draw_topology

def main():

    num_hosts = 128
    hosts = generate_hosts(num_hosts)

    print(f"Generated {len(hosts)} hosts")


    G = build_fat_tree(hosts)

    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")


    draw_topology(G)

if __name__ == "__main__":
    main()
