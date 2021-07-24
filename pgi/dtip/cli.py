import click
from pgi.dtip.dtip import *
from pgi.dtip.extract import extract_subject
from pgi.dtip.convert import convert_dicom_to_nifti


@click.group()
def cli():
    """
    Welcome to DTI processing tool for ITC cases.
    """



@cli.command()
@click.argument('src_file', type=click.Path(exists=True))
@click.option('-d', '--dst_folder', type=str, default=".", help="destination folder path")
@click.option('--multi', is_flag=True, default=False, help="pass --multi for more than one zip file.")
def extract_zip(src_file:Union[str, Path], dst_folder:Union[str, Path], multi:bool):
    """Extract zip file(s). pass --multi for more than one zip file."""
    if multi:
        subs = os.listdir(src_file)
        total_subs = len(subs)
        for i, subject_path in enumerate(subs):
            subject_path = os.path.join(src_file, subject_path)
            saved_at = extract_subject(subject_path, dst_folder)
            click.echo(f"[{i}/{total_subs}] extracted at {saved_at}")
    else:
        saved_at = extract_subject(src_file, dst_folder)
        click.echo(f"extracted at {saved_at}")



@cli.command()
@click.argument('src_folder', type=click.Path(exists=True))
@click.option('-d', '--dst_folder', default="./dicom-nifti-output", show_default=True, help="folder location to save outputs.")
@click.option('-m', '--method', type=click.Choice(['auto', 'dcm2nii', 'dcm2niix', 'dicom2nifti'], case_sensitive=False), show_default=True, default="auto", help="`auto` (whichever works best for each subject), `dicom2nifti` (python package), `dcm2nii` (MRICron), and `dcm2niix` (newer version of dcm2nii).")
def dicom_nifti(src_folder:Union[str, Path], dst_folder:Union[str, Path], method:str):
    """DICOM to NIfTI (.nii or .nii.gz) Conversion."""
    convert_dicom_to_nifti(src_folder, dst_folder, method=method)
    click.echo(f"done!")



@cli.command()
@click.argument('subject_path', type=click.Path(exists=True))
@click.option("-o", "--output_folder", default="./dtip_outputs", show_default=True, help="folder location to save outputs.")
@click.option("-nm", "--nifti_method", type=click.Choice(['auto', 'dcm2nii', 'dcm2niix', 'dicom2nifti'], case_sensitive=False), default="auto", show_default=True, help="dcm2niix is Mricron's subpackage. dicom2nifti is python package.")
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
