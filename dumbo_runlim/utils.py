import concurrent.futures
import dataclasses
import pickle
import resource
import subprocess
import sys
import time
from dataclasses import InitVar
from multiprocessing import Manager, Process
from typing import Callable, Optional

import typer
from dumbo_utils.console import console
from dumbo_utils.primitives import PrivateKey
from dumbo_utils.validation import validate
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn


@dataclasses.dataclass(frozen=True)
class AppOptions:
    key: InitVar[PrivateKey]
    __key = PrivateKey()

    real_time_limit: Optional[int] = dataclasses.field(default=None)
    time_limit: int = dataclasses.field(default=resource.RLIM_INFINITY)
    memory_limit: int = dataclasses.field(default=resource.RLIM_INFINITY)
    workers: int = dataclasses.field(default=1)
    debug: bool = dataclasses.field(default=False)

    __instance = None

    def __post_init__(self, key):
        self.__key.validate(key)

    @staticmethod
    def instance():
        return AppOptions.__instance if AppOptions.__instance is not None else AppOptions(key=AppOptions.__key)

    @staticmethod
    def set(**kwargs):
        validate("once", AppOptions.__instance is None, equals=True)
        AppOptions.__instance = AppOptions(key=AppOptions.__key, **kwargs)

    @staticmethod
    def pickle():
        validate("once", AppOptions.__instance is None, equals=True)
        AppOptions.__instance = pickle.loads(sys.stdin.buffer.read())


def is_debug_on():
    return AppOptions.instance().debug


@dataclasses.dataclass(frozen=True)
class ResourceUsage:
    time_limit: InitVar[int] = dataclasses.field(default=resource.RLIM_INFINITY)
    memory_limit: InitVar[int] = dataclasses.field(default=resource.RLIM_INFINITY)

    __data: dict = dataclasses.field(default_factory=dict, init=False)

    def __post_init__(self, time_limit, memory_limit):
        resource.setrlimit(resource.RLIMIT_CPU, (time_limit, time_limit))
        resource.setrlimit(resource.RLIMIT_RSS, (memory_limit, memory_limit))

    def __str__(self):
        return (f"ResourceUsage(real_time={self.real_time_usage:.3f}, time_usage={self.time_usage:.3f}, "
                f"memory_usage={self.memory_usage:.3f})")

    def __enter__(self):
        validate("once", self.__data, max_len=0, help_msg="ResourceUsage can only be used once")
        self.__data["start"] = time.perf_counter_ns()
        return self

    def __exit__(self, exception_type, value, traceback):
        self.__data["time_usage"] = self.time_usage
        self.__data["memory_usage"] = self.memory_usage
        self.__data["end"] = time.perf_counter_ns()
        self.__data["real_time_usage"] = self.__data["end"] - self.__data["start"]

    @property
    def real_time_usage(self) -> float:
        return (self.__data["real_time_usage"] if "real_time_usage" in self.__data else
                time.perf_counter_ns() - self.__data["start"]) / 1_000_000_000

    @property
    def time_usage(self) -> float:
        return self.__data["time_usage"] if "end" in self.__data else\
            (resource.getrusage(resource.RUSAGE_SELF).ru_utime +
                resource.getrusage(resource.RUSAGE_SELF).ru_stime)

    @property
    def memory_usage(self) -> float:
        return self.__data["memory_usage"] if "end" in self.__data else\
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


# def run_on_subprocess(real_time_limit: Optional[int] = None):
#     def decorator(fun):
#         @functools.wraps(fun)
#         def wrapper(*args, **kwargs):
#             def task(the_shared_list):
#                 the_shared_list.append(fun(*args, **kwargs))
#
#             with Manager() as manager:
#                 shared_list = manager.list()
#                 process = Process(target=task, args=(shared_list,))
#                 process.start()
#                 # monitoring
#                 process.join(timeout=real_time_limit)
#                 return shared_list[0]
#         return wrapper
#     return decorator


# @run_on_subprocess(real_time_limit=AppOptions.instance().real_time_limit)
# def experiment_task(
#         task_id,
#         measured_task: tuple[Callable, dict],
#         *,
#         setup: Optional[tuple[Callable, dict]] = None,
#         teardown: Optional[tuple[Callable, dict]] = None,
# ):
#     result = None
#     if setup is not None:
#         result = setup[0](**setup[1])
#
#     with ResourceUsage(
#             time_limit=AppOptions.instance().time_limit,
#             memory_limit=AppOptions.instance().memory_limit
#     ) as resources:
#         if result is None:
#             result = measured_task[0](**measured_task[1])
#         else:
#             result = measured_task[0](**measured_task[1], result=result)
#
#     if teardown is not None:
#         if result is None:
#             result = teardown[0](**teardown[1])
#         else:
#             result = teardown[0](**teardown[1], result=result)
#
#     return task_id, resources, result


def experiment_task(
        task_id,
        measure: tuple[Callable, dict],
        *,
        setup: Optional[tuple[Callable, dict]] = None,
        teardown: Optional[tuple[Callable, dict]] = None,
):
    def task(the_shared_list):
        result = None
        if setup is not None:
            result = setup[0](**setup[1])

        with ResourceUsage(
                time_limit=AppOptions.instance().time_limit,
                memory_limit=AppOptions.instance().memory_limit
        ) as resources:
            if result is None:
                result = measure[0](**measure[1])
            else:
                result = measure[0](**measure[1], result=result)

        if teardown is not None:
            if result is None:
                result = teardown[0](**teardown[1])
            else:
                result = teardown[0](**teardown[1], result=result)

        the_shared_list.append((task_id, resources, result))

    with Manager() as manager:
        shared_list = manager.list()
        process = Process(target=task, args=(shared_list,))
        process.start()
        # monitoring
        process.join(timeout=AppOptions.instance().real_time_limit)
        return shared_list[0]


def on_complete_task(task_id, resources, result):
    console.log(f"Task {task_id}: {resources}, {result}")


def on_all_done():
    console.log("[bold red]All done![/bold red]")


def run_experiment(
        *tasks: dict,
        on_complete_task: Callable = on_complete_task,
        on_all_done: Callable = on_all_done,
):
    with concurrent.futures.ProcessPoolExecutor(max_workers=AppOptions.instance().workers) as executor:
        futures = [executor.submit(experiment_task, **task) for task in tasks]
        with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                TextColumn("[{task.completed} of {task.total}]"),
                console=console,
        ) as progress:
            task = progress.add_task("Working...", total=len(futures))
            for future in concurrent.futures.as_completed(futures):
                task_id, resources, result = future.result()
                on_complete_task(task_id, resources, result)
                progress.update(task, advance=1)
    on_all_done()


def run_external_command(directory, args):
    subprocess.Popen(args, cwd=directory, stdin=subprocess.PIPE).communicate(pickle.dumps(AppOptions.instance()))


def external_command(command):
    try:
        AppOptions.pickle()
        typer.run(command)
    except Exception as e:
        if is_debug_on():
            raise e
        else:
            console.print(f"[red bold]Error:[/red bold] {e}")
