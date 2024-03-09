import os
import signal
from typing import Optional

import resource
import typer
from dumbo_utils.console import console

from dumbo_runlim.experiments import ucorexplain, example
from dumbo_runlim.utils import AppOptions

app = typer.Typer()


def is_debug_on():
    return AppOptions.instance().debug


def run_app():
    os.setpgrp()
    try:
        app()
    except Exception as e:
        os.killpg(0, signal.SIGKILL)
        if is_debug_on():
            raise e
        else:
            console.print(f"[red bold]Error:[/red bold] {e}")
    finally:
        os.killpg(0, signal.SIGKILL)


def version_callback(value: bool):
    if value:
        import importlib.metadata
        __version__ = importlib.metadata.version("dumbo-run-lim")
        console.print("asp-chef-cli", __version__)
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


app.command(name="example-command")(example.command)
app.command(name="ucorexplain-iclp-2024")(ucorexplain.iclp_2024)
