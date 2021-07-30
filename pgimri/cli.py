import os
import click
from pyfiglet import Figlet
from rich.console import Console
from pgimri.config import LOG_LEVEL
from pgimri.utils import get_logger
from rich.traceback import install
install()

# This generates `PGI MRI` banner in CLI.
f = Figlet(font='smslant')
console = Console()
console.print(f"[bold cyan]{f.renderText('P G I  -  M R I')}[/bold cyan]")
CONTEXT_SETTINGS = dict(auto_envvar_prefix="COMPLEX")
ROOTDIR = os.path.abspath(os.path.dirname(__file__))


class ComplexCLI(click.MultiCommand):
    """CLI files finder and loader class"""

    def list_commands(self, ctx) -> list:
        """
        This function creates a list of command (`cli.py`) files
        """
        cli_files_list = []
        # Look for modules that should be loaded with CLI
        for name in os.listdir(ROOTDIR):
            # Remove any __pycache__ like folders
            if name.startswith("__"):
                continue
            # Get full path of the module
            dirname = os.path.join(ROOTDIR, name)
            # Look for dtip and dkip like folders
            if os.path.isdir(dirname):
                # name of the folder that contains `cli.py` file
                cli_files_list.append(name)
        cli_files_list.sort()
        return cli_files_list

    def get_command(self, ctx, name: str) -> click.core.Command:
        """This function imports commands from `cli.py` files

        Args:
            > ctx -- click context object
            > name -- name of the folder from which cli.py file should be loaded
        """

        try:
            # {name} is the package like `dtip` and `dkip` and
            # `.cli` is the `cli.py` file inside these.
            mod = __import__(f"pgimri.{name}.cli", None, None, ["cli"])
        except ImportError:
            return

        return mod.cli


logger = get_logger("pgimri_main")


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
def cli():
    """Welcome to PGI-MRI CLI tool.

        This CLI is a Python wrapper for ``dcm2nii``
        This tool supports two MR modalities:
        
        1. DKI - Diffusion Kurtosis Imaging
        
        2. DTI - Diffusion Tensor Imaging
    """

    logger.setLevel(LOG_LEVEL)
