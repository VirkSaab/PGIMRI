import click
from pgi.dtip.dtip import *


@click.group()
def cli():
    """
    Welcome to DTI processing tool for ITC cases.

    """


@cli.command()
@click.argument('subject_path', type=click.Path(exists=True))
@click.option("-o", "--output_folder", default="./dtip_outputs", show_default=True,
              help="folder location to save outputs.")
@click.option("-nm", "--nifti_method", 
type=click.Choice(['auto', 'dcm2nii', 'dcm2niix', 'dicom2nifti'], case_sensitive=False),
default="auto",help="dcm2niix is Mricron's subpackage. dicom2nifti is python package."
)
def process_subject(subject_path, output_folder, nifti_method):
    """Perform DTI processing on one subject.

        SUBJECT_PATH - path to subject folder or zip file.
    """
    process_one_subject(subject_path, output_folder,nifti_method=nifti_method)
    # click.echo(click.format_filename(subject_path))


@cli.command()
@click.argument('datadir', type=click.Path(exists=True))
def process_subjects(datadir):
    """Perform DTI processing on multiple subjects"""

    # click.echo(click.format_filename(datadir))
    pass


if __name__ == '__main__':
    cli()
