from pathlib import Path

import typer

from dumbo_runlim.utils import run_external_command, git_pull


def command(
        output_file: Path = typer.Option(
            "output.csv", "--output-file", "-o",
            help="File to store final results",
        ),
) -> None:
    """
    Experiment for the ICLP 2024 paper.
    """
    path = "../dumbo-runlim-ucorexplain"
    git_pull("git@github.com:alviano/dumbo-runlim-ucorexplain.git", path)
    run_external_command(path, [
        "poetry", "run", "python", "-m", "ucorexplain",
        "-o", output_file.absolute(),
    ])
