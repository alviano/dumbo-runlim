import random
import time

from dumbo_runlim.utils import run_experiment


def measure():
    value = random.random() * 2
    time.sleep(value)
    return value


def command() -> None:
    run_experiment(*[
        {"task_id": index, "measure": (measure, {})}
        for index in range(10)
    ])
