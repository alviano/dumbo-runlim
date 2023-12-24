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
    real: int = dataclasses.field(default=MAX_LIMIT)
    time: int = dataclasses.field(default=MAX_LIMIT)
    memory: int = dataclasses.field(default=MAX_LIMIT)
    swap: int = dataclasses.field(default=0)

    def __post_init__(self):
        validate("realtime", self.real, min_value=0, max_value=MAX_LIMIT)
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
    __key: object = dataclasses.field()
    __start: float = dataclasses.field(default=time.time(), init=False)
    __real: float = dataclasses.field(default=0, init=False)
    __max_memory: float = dataclasses.field(default=0, init=False)
    __processes: dict[int, Usage] = dataclasses.field(default_factory=lambda: defaultdict(Usage), init=False)
    __last_report: float = dataclasses.field(default=0, init=False)
    __status: str = dataclasses.field(default="running", init=False)

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

    @property
    def status(self) -> str:
        return self.__status

    @property
    def terminated(self) -> bool:
        return self.__status != "running"

    def __exceed_limit(self, limit: Limit) -> bool:
        if self.real > limit.real:
            self.terminate("out of time (real)", key=self.__key)
        elif self.time > limit.time:
            self.terminate("out of time", key=self.__key)
        elif self.max_memory > limit.memory:
            self.terminate("out of memory", key=self.__key)
        elif self.swap > limit.swap:
            self.terminate("out of memory (swap)", key=self.__key)
        else:
            return False
        return True

    def update(self, process: psutil.Process, report_frequency: int, limit: Limit, *, key: object) -> bool:
        validate("key", key, equals=self.__key)
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

        if self.__exceed_limit(limit) or self.real >= self.__last_report + report_frequency:
            self.__last_report = self.real
            return True
        return False

    def terminate(self, status: str, *, key: object) -> None:
        validate("key", key, equals=self.__key)
        validate("status", self.__status, equals="running")
        validate("status", status != self.__status, equals=True)
        self.__status = status
