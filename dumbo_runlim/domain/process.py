import dataclasses
import os
import subprocess
import sys
import threading
import time
from typing import Callable

import psutil
from dumbo_utils.primitives import bounded_string
from dumbo_utils.validation import validate

from dumbo_runlim.domain.resources import Limit, UsageSummary


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


@dataclasses.dataclass(frozen=True)
class Process:
    command: str
    tag: Tag = dataclasses.field(default=Tag("UNTAGGED"))
    cpu_affinity: CPUAffinity = dataclasses.field(default=CPUAffinity())
    cpu_nice: int = dataclasses.field(default=20)
    report_frequency: int = dataclasses.field(default=10)
    limit: Limit = dataclasses.field(default=Limit())
    stream_callback: Callable[[str, str, bool, UsageSummary], bool] = dataclasses.field(
        default_factory=lambda: Process._default_stream_callback)
    report_callback: Callable[[str, UsageSummary], bool] = dataclasses.field(
        default_factory=lambda: Process._default_report_callback)

    __lock = threading.Lock()

    @staticmethod
    def _default_stream_callback(tag: Tag, line: str, is_err: bool, usage_summary: UsageSummary) -> bool:
        print(f"{tag}[{'e' if is_err else 'o'}{usage_summary.real:12.3f}]", line if line[-1] != '\n' else line[:-1],
              file=sys.stderr)
        return False

    @staticmethod
    def _default_report_callback(tag: Tag, usage_summary: UsageSummary) -> bool:
        print(
            f"[{tag}] "
            f"time: {usage_summary.real:10.1f} {usage_summary.time:10.1f}; "
            f"memory: {usage_summary.max_memory:10.0f} {usage_summary.memory:10.0f} {usage_summary.swap:10.0f}"
        )
        return False

    def __post_init__(self):
        validate("cpu_nice", self.cpu_nice, min_value=-20, max_value=20)
        validate("report_frequency", self.report_frequency, min_value=1, max_value=3600)

    def run(self):
        usage_key = object()
        usage_summary = UsageSummary(usage_key)

        def reader(stream, *, is_err):
            while True:
                line = stream.readline().decode()
                if not line:
                    break
                self.__lock.acquire()
                if self.stream_callback(self.tag, line, is_err, usage_summary):
                    usage_summary.terminate("interrupted by stream callback", key=usage_key)
                self.__lock.release()

        def waiter():
            waiter.result = process.wait()

        def kill():
            try:
                subprocesses = process.children(recursive=True)
            except psutil.NoSuchProcess:
                subprocesses = []
            subprocesses.append(process)

            for proc in subprocesses:
                try:
                    proc.terminate()
                except psutil.NoSuchProcess:
                    pass

            gone, alive = psutil.wait_procs(subprocesses, timeout=1)
            for proc in alive:
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass

        cmd = self.command.replace('"', '\\"')
        process = psutil.Popen(
            ["bash", "-c", f"PYTHONHASHSEED=0 {cmd}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        process.cpu_affinity(self.cpu_affinity.value)
        process.nice(self.cpu_nice)

        def sample():
            if usage_summary.update(process, self.report_frequency, self.limit, key=usage_key):
                self.__lock.acquire()
                if self.report_callback(self.tag, usage_summary):
                    usage_summary.terminate("interrupted by report callback", key=usage_key)
                self.__lock.release()

        out_reader = threading.Thread(target=lambda: reader(process.stdout, is_err=False))
        err_reader = threading.Thread(target=lambda: reader(process.stderr, is_err=True))
        wait = threading.Thread(target=waiter)
        out_reader.start()
        err_reader.start()
        wait.start()
        while wait.is_alive():
            time.sleep(
                0.10 if usage_summary.real < 1 else
                0.25 if usage_summary.real < 3 else
                0.50 if usage_summary.real < 10 else
                1.00
            )
            sample()
            if usage_summary.terminated:
                kill()
        wait.join()
        out_reader.join()
        err_reader.join()