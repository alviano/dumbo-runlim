from pathlib import Path

import typer

from dumbo_runlim.utils import run_external_command, git_pull, poetry_update


def command(
        output_file: Path = typer.Option(
            "output.csv", "--output-file", "-o",
            help="File to store final results",
        ),
        skip_update: bool = typer.Option(
            False, "--skip-update",
            help="Don't update the github repository",
        ),
        no_cache: bool = typer.Option(
            False, "--no-cache",
            help="Don't use cache when updating dependencies",
        ),
) -> None:
    """
    Experiment for the ICLP 2024 paper.
    """
    module = "dumbo-runlim-ucorexplain"
    path = f"../{module}"
    if not skip_update:
        git_pull(f"git@github.com:alviano/{module}.git", path)
        poetry_update(path, no_cache)
    run_external_command(path, [
        "poetry", "run", "python", "-m", module,
        "-o", output_file.absolute(),
    ])
