from Components.topology.fat_tree import build_fat_tree, build_fat_tree_informed
from Components.topology.jellyfish import build_jellyfish
from Components.topology.leaf_spine import build_leaf_spine, build_leaf_spine_informed

topology_configuration = {
    "fat_tree": build_fat_tree,
    "informed_fat_tree": build_fat_tree_informed,
    "jellyfish": build_jellyfish,
    "leaf_spine": build_leaf_spine,
    "informed_leaf_spine": build_leaf_spine_informed
}