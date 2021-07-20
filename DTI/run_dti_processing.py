import os
import click




def run_one_subject(datadir):
    datadir = os.path.abspath(datadir)
    print(datadir)


@click.command()
@click.argument("datadir")
# @click.option("-d", "--datadir", type=str, required=True, help="path to subject data folder")
def dtip(datadir:str) -> None:
    """Run DTI processing for ITC cases.
    DATADIR - path to subject's data folder.
    """
    ret_out = run_one_subject(datadir)
    click.echo("DONE!")
    pass


if __name__ == "__main__":
    dtip()