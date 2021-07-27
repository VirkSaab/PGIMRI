import os
import click
from typing import Union
from pathlib import Path
from pgimri.dtip.dtip import *
from pgimri.dtip.extract import extract_subject
from pgimri.dtip.convert import convert_dicom_to_nifti
from pgimri.dtip.locate  import locate_data_files
from pgimri.dtip.generate import *

@click.group()
def cli():
    """
    Diffusion Tensor Imaging (DTI) Processing tool.
    """


@cli.command()
@click.argument('src_file', type=click.Path(exists=True))
@click.option('-d', '--dst_folder', type=str, default=".", help="destination folder path")
@click.option('--multi', is_flag=True, default=False, help="pass --multi for more than one zip file.")
def extract_zip(src_file:Union[str, Path], dst_folder:Union[str, Path], multi:bool):
    """Extract zip file(s). pass --multi for more than one zip file."""
    if multi:
        subjects = os.listdir(src_file)
        total_subjects = len(subjects)
        for i, subject_path in enumerate(subjects):
            subject_path = os.path.join(src_file, subject_path)
            saved_at = extract_subject(subject_path, dst_folder)
            click.echo(f"[{i}/{total_subjects}] extracted at {saved_at}")
    else:
        saved_at = extract_subject(src_file, dst_folder)
        click.echo(f"extracted at {saved_at}")



@cli.command()
@click.argument('src_folder', type=click.Path(exists=True))
@click.option('-d', '--dst_folder', default="./dicom-nifti-output", show_default=True, help="folder location to save outputs.")
@click.option('-m', '--method', type=click.Choice(['auto', 'dcm2nii', 'dcm2niix', 'dicom2nifti'], case_sensitive=False), show_default=True, default="auto", help="`auto` (whichever works best for each subject), `dicom2nifti` (python package), `dcm2nii` (MRICron), and `dcm2niix` (newer version of dcm2nii).")
@click.option('--multi', is_flag=True, default=False, help="pass --multi for more than one subject.")
def dicom_nifti(src_folder:Union[str, Path], dst_folder:Union[str, Path], method:str, multi:bool):
    """DICOM to NIfTI (.nii or .nii.gz) Conversion."""
    if multi:
        subjects = os.listdir(src_folder)
        total_subjects = len(subjects)
        for i, subject_name in enumerate(subjects):
            subject_path = os.path.join(src_folder, subject_name)
            save_folder = Path(os.path.join(dst_folder, subject_name))
            save_folder.mkdir(parents=True, exist_ok=True)
            convert_dicom_to_nifti(subject_path, dst_folder, method=method)
            click.echo(f"[{i}/{total_subjects}] extracted at {save_folder}")
    else:
        convert_dicom_to_nifti(src_folder, dst_folder, method=method)
    click.echo(f"done!")


@cli.command()
@click.argument('src_folder', type=click.Path(exists=True))
@click.argument('dst_folder')
def locate(src_folder, dst_folder):
    """Locate and copy main DTI and metadata files."""
    ret = locate_data_files(src_folder, dst_folder)
    if ret == 0:
        click.echo("Successfully copied.")


@cli.command()
@click.argument('src_filepath', type=click.Path(exists=True))
@click.option('-d', '--dst_filepath', default='index.txt', show_default=True, help="path/to/file/index.txt")
def make_index(src_filepath:str, dst_filepath:str):
    """Generate an index.txt file containing value 1 for each DTI volume"""
    ret = generate_index_file(src_filepath, dst_filepath)
    if ret == 0:
        click.echo("Done.")


@cli.command()
@click.option('-t', '--readout_time', default=0.05, show_default=True, help="Total readout time.")
@click.option('-ap', '--ap_pe', default="0,-1,0", show_default=True, help="Anterior to Posterior Phase Encoding.")
@click.option('-pa', '--pa_pe', default="0,1,0", show_default=True, help="Posterior to Anterior Phase Encoding.")
@click.option('-d', '--dst_filepath', default='acqparams.txt', show_default=True, help="path/to/file/acqparams.txt")
def make_acqparams(readout_time:float, ap_pe:list, pa_pe:list, dst_filepath:str):
    """Generate the acqparams.txt file"""
    ret = generate_acquisition_params_file(readout_time, ap_pe, pa_pe, dst_filepath)
    if ret == 0:
        click.echo("Done.")


@cli.command()
@click.argument('src_filepath', type=click.Path(exists=True))
@click.option('-d', '--dst_filepath', default='b0_nodif.nii.gz', show_default=True, help="path/to/file/b0_nodif.nii.gz")
def make_nodif(src_filepath:str, dst_filepath:str):
    """From the DTI 4D data, choose a volume without diffusion weighting 
    (e.g. the first volume). You can now extract this as a standalone 3D image,
    using `fslroi` command. This function runs the `fslroi` command internally.
    """
    ret = generate_b0_from_dti(src_filepath, dst_filepath)
    if ret == 0:
        click.echo("Done.")




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
