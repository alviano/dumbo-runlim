import dataclasses
import os
import subprocess
import sys
import threading
import time

import psutil
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


@dataclasses.dataclass(frozen=True)
class Process:
    command: str
    cpu_affinity: CPUAffinity = dataclasses.field(default=CPUAffinity())
    cpu_nice: int = dataclasses.field(default=20)
    report_frequency: int = dataclasses.field(default=10)
    limit: Limit = dataclasses.field(default=Limit())

    def __post_init__(self):
        validate("cpu_nice", self.cpu_nice, min_value=-20, max_value=20)
        validate("report_frequency", self.report_frequency, min_value=1, max_value=3600)

    def run(self):
        start_time = time.time()
        usage_summary = UsageSummary()
        lock = threading.Lock()

        def reader(stream, prefix):
            while True:
                line = stream.readline().decode()
                if not line:
                    break
                real = time.time() - start_time
                lock.acquire()
                print(f"[{prefix}{real:12.3f}]", line if line[-1] != '\n' else line[:-1], file=sys.stderr)
                lock.release()

        def waiter():
            waiter.result = process.wait()

        def kill():
            try:
                subprocesses = process.children(recursive=True)
            except psutil.NoSuchProcess:
                subprocesses = []
            subprocesses = [p for p in subprocesses if p.cmdline != process.cmdline]

            for p in subprocesses:
                try:
                    p.terminate()
                except psutil.NoSuchProcess:
                    pass

            gone, alive = psutil.wait_procs(subprocesses, timeout=10)
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass

        cmd = self.command.replace('"', '\\"')
        process = psutil.Popen(
            ["bash", "-c", f"PYTHONHASHSEED=0 trap '' SIGINT SIGTERM; ({cmd})"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        process.cpu_affinity(self.cpu_affinity.value)
        process.nice(self.cpu_nice)

        def sample():
            if usage_summary.update(process, self.report_frequency):
                print(
                    f"time: {usage_summary.real:10.1f} {usage_summary.time:10.1f}; "
                    f"memory: {usage_summary.max_memory:10.0f} {usage_summary.memory:10.0f} {usage_summary.swap:10.0f}"
                )

        out_reader = threading.Thread(target=lambda: reader(process.stdout, "o"))
        err_reader = threading.Thread(target=lambda: reader(process.stderr, "e"))
        wait = threading.Thread(target=waiter)
        out_reader.start()
        err_reader.start()
        wait.start()
        while wait.is_alive():
            time.sleep(.1)
            if usage_summary.exceed_limit(self.limit):
                kill()
            sample()
        wait.join()
        out_reader.join()
        err_reader.join()
