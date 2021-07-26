import os
import click
from pgimri.config import LOG_LEVEL
from pgimri.utils import get_logger, addLoggingLevel


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
            ctx: click context object
            name: name of the folder from which cli.py file should be loaded
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
    """Welcome to PGIMRI CLI tool.

        dtip - Diffusion Tensor Imaging (DTI) processing pipeline CLI.
        
        dkip - Diffusion Kurtosis Imaging (DKI) processing pipeline CLI.
    """
    logger.setLevel(LOG_LEVEL)
