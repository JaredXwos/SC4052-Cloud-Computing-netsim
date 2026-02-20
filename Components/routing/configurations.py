from Components.routing.policy import *

policy_configuration = {
    "conga_configuration": ["conga"],
    "rip_configuration": ["rip"],
    "ospf_configuration": ["stale_ospf"],
    "eigrp_configuration": ["stale_eigrp", "eigrp"],
    "rip_ecmp_configuration": ["rip_ecmp"],
    "ospf_ecmp_configuration": ["stale_ospf_ecmp"],
    "eigrp_ecmp_configuration": ["stale_eigrp_ecmp", "eigrp_ecmp"],
    "rip_drill_configuration": ["rip_drill"],
    "ospf_drill_configuration": ["stale_ospf_drill"],
    "eigrp_drill_configuration": ["stale_eigrp_drill", "eigrp_drill"],
}
POLICY_BUILDERS = {
    "conga": conga,
    "rip": rip,
    "ospf": ospf,
    "eigrp": eigrp,
    "stale_ospf": stale_ospf,
    "stale_eigrp": stale_eigrp,
    "rip_ecmp": rip_ecmp,
    "ospf_ecmp": ospf_ecmp,
    "eigrp_ecmp": eigrp_ecmp,
    "stale_ospf_ecmp": stale_ospf_ecmp,
    "stale_eigrp_ecmp": stale_eigrp_ecmp,
    "rip_drill": rip_drill,
    "ospf_drill": ospf_drill,
    "eigrp_drill": eigrp_drill,
    "stale_ospf_drill": stale_ospf_drill,
    "stale_eigrp_drill": stale_eigrp_drill,
}