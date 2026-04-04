"""Entry point for running ripper as a module (python -m ripper)."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def _load_env_or_exit():
    ripper_env = os.environ.get("RIPPER_ENV")
    local = Path.cwd() / ".env"

    if ripper_env:
        ripper_path = Path(ripper_env)
        if ripper_path.is_file():
            load_dotenv(ripper_path)
            return
        if local.is_file():
            load_dotenv(local)
            return
        sys.exit(
            f"Error: .env not found at RIPPER_ENV path '{ripper_env}' or at local '{local}'.\n"
            "Please place your .env file's path into the RIPPER_ENV environment variable."
        )

    # RIPPER_ENV not set; try local .env
    if local.is_file():
        load_dotenv(local)
        return

    sys.exit(
        "Error: No .env file found. Set the RIPPER_ENV environment variable to the path of your .env file."
    )


_load_env_or_exit()

from ripper.cli import main


if __name__ == "__main__":
    main()
