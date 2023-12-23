import dataclasses
import os

import psutil
from dumbo_utils import primitives
from dumbo_utils.validation import validate


@dataclasses.dataclass(frozen=True)
class CPUAffinity:
    value: tuple[int, ...] = dataclasses.field(default_factory=lambda: CPUAffinity.cpus())

    def __post_init__(self):
        cpus = self.cpus()
        for value in self.value:
            validate("cpu", value, is_in=cpus, help_msg=f"CPU {value} is invalid")

    @staticmethod
    def of(*args: int) -> "CPUAffinity":
        return CPUAffinity(args)

    @staticmethod
    def cpus() -> tuple[int, ...]:
        return tuple(psutil.Process(os.getpid()).cpu_affinity())


@primitives.bounded_integer(min_value=-20, max_value=20)
class CPUNice:
    pass


@dataclasses.dataclass(frozen=True)
class Process:
    cpu_affinity: CPUAffinity = dataclasses.field(default=CPUAffinity())
    cpu_nice: CPUNice = dataclasses.field(default=CPUNice(20))
