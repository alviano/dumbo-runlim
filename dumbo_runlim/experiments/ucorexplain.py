from pathlib import Path

import typer

from dumbo_runlim.utils import run_external_command


def command(
        output_file: Path = typer.Option(
            "output.csv", "--output-file", "-o",
            help="File to store final results",
        ),
) -> None:
    """
    Experiment for the ICLP 2024 paper.
    """
    # git clone...
    # git pull...
    run_external_command("../dumbo-runlim-ucorexplain", [
        "poetry", "run", "python", "-m", "ucorexplain",
        "-o", output_file.absolute(),
    ])
