import dataclasses
import time
from collections import defaultdict

import psutil
import typeguard
from dumbo_utils.validation import validate

MAX_LIMIT = 10**100


@typeguard.typechecked
@dataclasses.dataclass(frozen=True)
class Limit:
    realtime: int = dataclasses.field(default=MAX_LIMIT)
    time: int = dataclasses.field(default=MAX_LIMIT)
    memory: int = dataclasses.field(default=MAX_LIMIT)
    swap: int = dataclasses.field(default=0)

    def __post_init__(self):
        validate("realtime", self.realtime, min_value=0, max_value=MAX_LIMIT)
        validate("time", self.time, min_value=0, max_value=MAX_LIMIT)
        validate("memory", self.memory, min_value=0, max_value=MAX_LIMIT)
        validate("swap", self.swap, min_value=0, max_value=MAX_LIMIT)


@typeguard.typechecked
@dataclasses.dataclass()
class Usage:
    __user: float = dataclasses.field(default=0, init=False)
    __system: float = dataclasses.field(default=0, init=False)
    __rss: float = dataclasses.field(default=0, init=False)
    __swap: float = dataclasses.field(default=0, init=False)

    @property
    def time(self) -> float:
        return self.__user + self.__system

    @property
    def memory(self) -> float:
        return self.__rss + self.__swap

    @property
    def swap(self) -> float:
        return self.__swap

    def update(self, process: psutil.Process) -> None:
        cpu_times, memory_info, memory_maps = process.cpu_times(), process.memory_info(), process.memory_maps()
        self.__user = max(self.__user, cpu_times.user)
        self.__system = max(self.__system, cpu_times.system)
        self.__rss = memory_info.rss / 1024 / 1024
        self.__swap = sum([mem.swap for mem in memory_maps]) / 1024 / 1024


@typeguard.typechecked
@dataclasses.dataclass()
class UsageSummary:
    __start: float = dataclasses.field(default=time.time(), init=False)
    __real: float = dataclasses.field(default=0, init=False)
    __max_memory: float = dataclasses.field(default=0, init=False)
    __processes: dict[int, Usage] = dataclasses.field(default_factory=lambda: defaultdict(Usage), init=False)
    __last_report: float = dataclasses.field(default=0, init=False)

    @property
    def real(self) -> float:
        return self.__real

    @property
    def time(self) -> float:
        return sum(process.time for process in self.__processes.values())

    @property
    def max_memory(self) -> float:
        return self.__max_memory

    @property
    def memory(self) -> float:
        return sum(process.memory for process in self.__processes.values())

    @property
    def swap(self) -> float:
        return sum(process.swap for process in self.__processes.values())

    def exceed_limit(self, limit: Limit) -> bool:
        return (self.real > limit.realtime or
                self.time > limit.time or
                self.max_memory > limit.memory or
                self.swap > limit.swap)

    def update(self, process: psutil.Process, report_frequency: int) -> bool:
        all_processes = [process]
        try:
            all_processes.extend(process.children(recursive=True))
        except psutil.NoSuchProcess:
            pass

        for proc in all_processes:
            try:
                self.__processes[proc.pid].update(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        self.__real = time.time() - self.__start
        self.__max_memory = max(self.__max_memory, self.memory)

        if self.real > self.__last_report + report_frequency:
            self.__last_report = self.real
            return True
        return False
