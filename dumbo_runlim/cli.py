import os
import resource
import signal
import time
from typing import Optional

import typer
from dumbo_utils.console import console

from dumbo_runlim.experiments import example, ucorexplain
from dumbo_runlim.utils import AppOptions, is_debug_on

app = typer.Typer()


def run_app():
    os.setpgrp()

    def signal_handler(the_signal, frame):
        os.killpg(0, signal.SIGINT)
        time.sleep(1)
        os.killpg(0, signal.SIGKILL)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        app()
    except Exception as e:
        os.killpg(0, signal.SIGKILL)
        if is_debug_on():
            raise e
        else:
            console.print(f"[red bold]Error:[/red bold] {e}")


def version_callback(value: bool):
    if value:
        import importlib.metadata
        __version__ = importlib.metadata.version("dumbo-runlim")
        console.print("dumbo-runlim", __version__)
        raise typer.Exit()


@app.callback()
def main(
        debug: bool = typer.Option(False, "--debug", help="Print stack trace in case of errors"),
        real_time_limit: Optional[int] = typer.Option(
            None, "--real-time-limit", "-r",
            help="Maximum real time (in seconds) to complete each task (including set up and tear down operations)",
        ),
        time_limit: int = typer.Option(
            resource.RLIM_INFINITY, "--time-limit", "-t",
            help="Maximum time (user+system; in seconds) to complete each task"
        ),
        memory_limit: int = typer.Option(
            resource.RLIM_INFINITY, "--memory-limit", "-m",
            help="Maximum memory (in MB) to complete each task",
        ),
        workers: int = typer.Option(
            1, "--workers", "-w",
            help="Number of workers to use for parallel execution of the experiment",
        ),
        version: bool = typer.Option(False, "--version", callback=version_callback, is_eager=True,
                                     help="Print version and exit"),
):
    """
    A simple CLI to run experiments
    """
    AppOptions.set(
        real_time_limit=real_time_limit,
        time_limit=time_limit,
        memory_limit=memory_limit,
        workers=workers,
        debug=debug,
    )


app.command(name="example")(example.command)
app.command(name="ucorexplain")(ucorexplain.command)
