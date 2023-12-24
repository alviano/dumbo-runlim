import dataclasses
import os

import psutil
from dumbo_utils.primitives import bounded_string
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


@bounded_string(min_length=0, max_length=16, pattern=r'[A-Za-z0-9 _-]+')
class Tag:
    def __str__(self):
        return "{tag:{width}}".format(tag=self.value, width=self.max_length())
