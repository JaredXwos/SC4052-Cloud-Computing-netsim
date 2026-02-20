from typing import List, Protocol
from Components.host import Host
from Components.workloads.flow import Flow
import global_randoms

class Workload(Protocol):
    """
    Generate traffic for a single epoch.

    Returns:
    List of flows:
        (src_id, dst_id, rate)
    """
    def generate(self) -> List[Flow]: ...

def clear_prefixed_tags(hosts: List[Host], prefix: str):
    for h in hosts:
        to_remove = {t for t in h.tags if t.startswith(prefix)}
        h.tags.difference_update(to_remove)


def add_group_tag(host: Host, prefix: str, gid: int):
    host.add_tag(f"{prefix}:{gid}")

class _AR1BaseWorkload:
    """
    Shared AR(1) temporal engine.

    Subclasses only implement:
        _choose_endpoints()
    """

    hosts: List[Host]
    flows_per_epoch: int
    data_per_epoch: float
    alpha: float

    def __init__(
        self,
        hosts: List[Host],
        flows_per_epoch: int,
        rate: float,
        alpha: float,
    ) -> None:
        self.hosts = hosts
        self.flows_per_epoch = flows_per_epoch
        self.data_per_epoch = rate
        self.alpha = alpha

        self._prev_rates = [0.0] * flows_per_epoch

    # ------------------------
    # AR(1) core
    # ------------------------

    def _next_rate(self, i: int) -> float:
        prev = self._prev_rates[i]
        noise = self.data_per_epoch * global_randoms.workload.random()

        rate = self.alpha * prev + (1.0 - self.alpha) * noise
        self._prev_rates[i] = rate
        return rate

    # ------------------------
    # to be overridden
    # ------------------------

    def _choose_endpoints(self) -> tuple[Host, Host]:
        raise NotImplementedError

    # ------------------------
    # public API
    # ------------------------

    def generate(self) -> List[Flow]:
        flows: List[Flow] = []

        for i in range(self.flows_per_epoch):
            src, dst = self._choose_endpoints()
            rate = self._next_rate(i)

            flows.append(Flow(src.id, dst.id, rate))

        return flows

    def reset(self):
        self._prev_rates = [0.0] * self.flows_per_epoch

class AR1Workload(_AR1BaseWorkload):
    """Pure random AR(1) workload."""

    def __init__(
        self,
        hosts: List[Host],
        flows_per_epoch: int = 50,
        rate: float = 1.0,
        alpha: float = 0.9,
    ):
        super().__init__(hosts, flows_per_epoch, rate, alpha)

        self._endpoints = []
        self._initialise_endpoints()

    # -----------------------------------------

    def _initialise_endpoints(self):
        self._endpoints = []

        for _ in range(self.flows_per_epoch):
            src, dst = global_randoms.workload.sample(self.hosts, 2)
            self._endpoints.append((src.id, dst.id))

    # -----------------------------------------

    def generate(self) -> List[Flow]:

        flows: List[Flow] = []

        for i in range(self.flows_per_epoch):

            # Drift with probability alpha
            if i < len(self._endpoints) and global_randoms.workload.random() < self.alpha:
                src_id, dst_id = self._endpoints[i]
            else:
                src, dst = global_randoms.workload.sample(self.hosts, 2)
                src_id, dst_id = src.id, dst.id

                if i < len(self._endpoints):
                    self._endpoints[i] = (src_id, dst_id)
                else:
                    self._endpoints.append((src_id, dst_id))

            rate = self._next_rate(i)
            flows.append(Flow(src_id, dst_id, rate))

        return flows

class AR1HotspotWorkload(_AR1BaseWorkload):
    """AR(1) + spatial hotspot workload."""

    def __init__(
        self,
        hosts: List[Host],
        flows_per_epoch: int = 50,
        rate: float = 1.0,
        alpha: float = 0.9,
        hotspot_ratio: float = 0.3,
        hotspot_count: int = 2,
    ):
        super().__init__(hosts, flows_per_epoch, rate, alpha)

        self.hotspot_ratio = hotspot_ratio
        self.hotspot_count = hotspot_count
        self._choose_hotspots()

    def _choose_hotspots(self):
        self.hotspots = global_randoms.workload.sample(
            self.hosts, self.hotspot_count
        )

    def reset(self):
        super().reset()
        self._choose_hotspots()

    def _choose_endpoints(self):

        if global_randoms.workload.random() < self.hotspot_ratio:
            src = global_randoms.workload.choice(self.hosts)

            dst_candidates = [h for h in self.hotspots if h != src]
            if dst_candidates:
                dst = global_randoms.workload.choice(dst_candidates)
                return src, dst

        return global_randoms.workload.sample(self.hosts, 2)

class AR1UnscheduledIncast(_AR1BaseWorkload):
    def __init__(
            self,
            hosts: List[Host],
            flows_per_epoch: int = 50,  # fan-in size
            rate: float = 1.0,
            alpha: float = 0.9,
    ):
        super().__init__(hosts, flows_per_epoch, rate, alpha)
        self._receiver = global_randoms.workload.choice(self.hosts)
        self._choose_endpoints()

    def generate(self) -> List[Flow]:

        # endpoint drift
        if global_randoms.workload.random() > self.alpha:
            self._receiver = global_randoms.workload.choice(self.hosts)

        return super().generate()

class AR1ScheduledGroupIncast(_AR1BaseWorkload):

    JOB_PREFIX = "job"

    def __init__(self, hosts, flows_per_epoch=50,
                 rate=1.0, alpha=0.9,
                 group_size=32, cross_ratio=0.1):

        super().__init__(hosts, flows_per_epoch, rate, alpha)

        self.group_size = group_size
        self.cross_ratio = cross_ratio

        self.groups = max(1, len(hosts) // group_size)
        self._assign_groups()

        self._active_group = global_randoms.workload.randrange(self.groups)
        self._incast_dst = None

        self._endpoints = []
        self._initialise_endpoints()

    def _initialise_endpoints(self):
        self._endpoints = []

        for _ in range(self.flows_per_epoch):
            src, dst = self._draw_new_pair()
            self._endpoints.append((src.id, dst.id))

    def _draw_new_pair(self):
        group = self._groups[self._active_group]

        if not group:
            return None, None

        # choose incast destination once
        if self._incast_dst is None or \
                global_randoms.workload.random() > self.alpha:
            self._incast_dst = global_randoms.workload.choice(group)

        # choose source
        if global_randoms.workload.random() < self.cross_ratio:
            src = global_randoms.workload.choice(self.hosts)
        else:
            src = global_randoms.workload.choice(group)

        return src, self._incast_dst
    def _assign_groups(self):
        clear_prefixed_tags(self.hosts, f"{self.JOB_PREFIX}:")

        shuffled = self.hosts[:]
        global_randoms.workload.shuffle(shuffled)

        chunk = len(shuffled) // self.groups
        self._groups = []

        for g in range(self.groups):
            group_hosts = shuffled[g * chunk:(g + 1) * chunk]
            self._groups.append(group_hosts)

            for h in group_hosts:
                add_group_tag(h, self.JOB_PREFIX, g)

    def generate(self):

        # group drift
        if global_randoms.workload.random() > self.alpha:
            self._active_group = global_randoms.workload.randrange(self.groups)
            self._incast_dst = None  # reset incast target

        flows = []

        for i in range(self.flows_per_epoch):

            if i < len(self._endpoints) and \
                    global_randoms.workload.random() < self.alpha:

                src_id, dst_id = self._endpoints[i]

            else:
                src, dst = self._draw_new_pair()
                if src is None or dst is None:
                    continue

                src_id, dst_id = src.id, dst.id
                self._endpoints[i] = (src_id, dst_id)

            rate = self._next_rate(i)
            flows.append(Flow(src_id, dst_id, rate))

        return flows

class AR1StrictLocalGroupWorkload(_AR1BaseWorkload):
    """
    Strict locality within logical job groups.

    All flows stay inside same job group.
    No cross-group traffic.
    """

    JOB_PREFIX = "job"

    def __init__(
            self,
            hosts: List[Host],
            flows_per_epoch: int = 50,
            rate: float = 1.0,
            alpha: float = 0.9,
            group_size: int = 32,
            cross_ratio: float = 0.1,
    ):
        super().__init__(hosts, flows_per_epoch, rate, alpha)

        self.group_size = group_size
        self.cross_ratio = cross_ratio

        # Compute number of groups dynamically
        self.groups = max(1, len(self.hosts) // self.group_size)

        self._assign_groups()

        self._endpoints = []
        self._initialise_endpoints()

    def _initialise_endpoints(self):
        self._endpoints = []

        for _ in range(self.flows_per_epoch):
            g = global_randoms.workload.randrange(self.groups)
            group = self._group_hosts(g)

            if len(group) < 2:
                continue

            while True:
                src = global_randoms.workload.choice(group)
                dst = global_randoms.workload.choice(group)
                if src != dst:
                    break

            self._endpoints.append((src.id, dst.id))

    def _assign_groups(self):
        clear_prefixed_tags(self.hosts, f"{self.JOB_PREFIX}:")

        shuffled = self.hosts[:]
        global_randoms.workload.shuffle(shuffled)

        self._groups = []

        for g in range(self.groups):
            start = g * self.group_size
            end = start + self.group_size
            group_hosts = shuffled[start:end]

            if not group_hosts:
                continue

            self._groups.append(group_hosts)

            for h in group_hosts:
                add_group_tag(h, self.JOB_PREFIX, g)

    # ------------------------

    def _group_hosts(self, g: int):
        return self._groups[g]

    # ------------------------

    def generate(self) -> List[Flow]:

        flows: List[Flow] = []

        for i in range(self.flows_per_epoch):

            # Drift: with probability alpha keep previous endpoints
            if i < len(self._endpoints) and global_randoms.workload.random() < self.alpha:
                src_id, dst_id = self._endpoints[i]
            else:
                g = global_randoms.workload.randrange(self.groups)
                group = self._group_hosts(g)

                if len(group) < 2:
                    continue

                while True:
                    src = global_randoms.workload.choice(group)
                    dst = global_randoms.workload.choice(group)
                    if src != dst:
                        break

                src_id, dst_id = src.id, dst.id

                # store new endpoints
                if i < len(self._endpoints):
                    self._endpoints[i] = (src_id, dst_id)
                else:
                    self._endpoints.append((src_id, dst_id))

            rate = self._next_rate(i)
            flows.append(Flow(src_id, dst_id, rate))

        return flows