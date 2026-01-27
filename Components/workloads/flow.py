from dataclasses import dataclass

@dataclass(slots=True)
class Flow:
    src: int
    dst: int
    rate: float