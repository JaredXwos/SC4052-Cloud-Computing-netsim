"""
host.py

Defines the Host abstraction used throughout the simulator.

A Host represents an endpoint (server / machine) in the datacenter.
It is intentionally lightweight and contains only metadata.
"""

from dataclasses import dataclass, field
from typing import Set


@dataclass(slots=True)
class Host:
    """
    Lightweight representation of a compute node.

    Parameters
    ----------
    id : int
        Unique identifier for this host.
    tags : set[str]
        Flexible capability or role labels.
        Examples:
            {"gpu"}
            {"storage"}
            {"server"}
            {"worker"}
        routing/topology/workload modules may interpret these.
    """

    id: int
    tags: Set[str] = field(default_factory=set)

    # Convenience helpers
    def has_tag(self, tag: str) -> bool:
        """Return True if this host has the given tag."""
        return tag in self.tags
    def add_tag(self, tag: str) -> None:
        """Attach a label to this host."""
        self.tags.add(tag)
    def remove_tag(self, tag: str) -> None:
        """Remove a label from this host."""
        self.tags.discard(tag)

    # Debugging / logging
    def __repr__(self) -> str:
        """Compact debug-friendly representation."""
        return (
            f"Host(id={self.id}, "
            f"tags={sorted(self.tags)})"
        )

def generate_hosts(n: int) -> list[Host]:
    """
    Create n hosts with unique deterministic IDs.

    IDs are 0..n-1.

    This function guarantees uniqueness.
    """
    return [Host(id=i) for i in range(n)]