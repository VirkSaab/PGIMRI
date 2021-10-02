import os
import click
from typing import Union
from pathlib import Path
from rich.traceback import install as rich_traceback_install
from pgimri.dtip.process import process_one_subject, process_multi_subjects
from pgimri.dtip.extract import extract_subject
from pgimri.dtip.convert import convert_dicom_to_nifti, dtitk_to_fsl_multi
from pgimri.dtip.locate import locate_data_files
from pgimri.dtip.generate import *
from pgimri.dtip.register import *

rich_traceback_install()  # Pretty traceback


# ------------------------------- `dtip` main command
@click.group()
def cli():
    """
    Diffusion Tensor Imaging (DTI) Processing tool. This tool is a part of
    PGIMRI package.

    This tool is created for Phillips MRI scanner DICOM data format. The data is acquired by dual-echo FSE. Other method is opposite phase encoding acqusition (create AP and PA images).
    """

# ------------------------------- dtip > extract module


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('-o', '--output_path', type=str, default=".", help="destination folder path")
@click.option('--multi', is_flag=True, default=False, help="pass --multi for more than one zip file.")
def extract_zip(input_path: Union[str, Path], output_path: Union[str, Path], multi: bool):
    """Extract zip file(s). pass --multi for more than one zip file."""
    if multi:
        subjects = os.listdir(input_path)
        total_subjects = len(subjects)
        for i, subject_path in enumerate(subjects):
            subject_path = os.path.join(input_path, subject_path)
            saved_at = extract_subject(subject_path, output_path)
            click.echo(f"[{i}/{total_subjects}] extracted at {saved_at}")
    else:
        saved_at = extract_subject(input_path, output_path)
        click.echo(f"extracted at {saved_at}")

# ------------------------------- dtip > convert module


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('-o', '--output_path', default="./dicom-nifti-output", show_default=True, help="folder location to save outputs.")
@click.option('-m', '--method', type=click.Choice(['auto', 'dcm2nii', 'dcm2niix', 'dicom2nifti'], case_sensitive=False), show_default=True, default="auto", help="`auto` (whichever works best for each subject), `dicom2nifti` (python package), `dcm2nii` (MRICron), and `dcm2niix` (newer version of dcm2nii).")
@click.option('--multi', is_flag=True, default=False, help="pass --multi for more than one subject.")
def dicom_nifti(input_path: Union[str, Path], output_path: Union[str, Path], method: str, multi: bool):
    """DICOM to NIfTI (.nii or .nii.gz) Conversion."""
    if multi:
        subjects = os.listdir(input_path)
        total_subjects = len(subjects)
        for i, subject_name in enumerate(subjects):
            subject_path = os.path.join(input_path, subject_name)
            save_folder = Path(os.path.join(output_path, subject_name))
            save_folder.mkdir(parents=True, exist_ok=True)
            convert_dicom_to_nifti(subject_path, output_path, method=method)
            click.echo(f"[{i}/{total_subjects}] extracted at {save_folder}")
    else:
        convert_dicom_to_nifti(input_path, output_path, method=method)
    click.echo(f"done!")

# -------------------------------- dtip > locate module


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path')
def locate(input_path, output_path):
    """Locate and copy main DTI and metadata files."""
    ret = locate_data_files(input_path, output_path)
    if ret == 0:
        click.echo("Successfully copied.")

# -------------------------------- dtip > generate module


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('-d', '--output_path', default='index.txt', show_default=True, help="path/to/file/index.txt")
def make_index(input_path: str, output_path: str):
    """Generate an index.txt file containing value 1 for each DTI volume"""
    ret = generate_index(input_path, output_path)
    if ret == 0:
        click.echo("Done.")


@cli.command()
@click.option('-t', '--readout_time', default=0.05, show_default=True, help="Total readout time.")
@click.option('-ap', '--ap_pe', default="0,-1,0", show_default=True, help="Anterior to Posterior Phase Encoding.")
@click.option('-pa', '--pa_pe', default="0,1,0", show_default=True, help="Posterior to Anterior Phase Encoding.")
@click.option('-d', '--output_path', default='acqparams.txt', show_default=True, help="path/to/file/acqparams.txt")
def make_acqparams(readout_time: float, ap_pe: list, pa_pe: list, output_path: str):
    """Generate the acqparams.txt file"""
    ret = generate_acquisition_params(readout_time, ap_pe, pa_pe, output_path)
    if ret == 0:
        click.echo("Done.")


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('-o', '--output_path', default='b0.nii.gz', show_default=True, help="path/to/file/b0.nii.gz")
@click.option('-idx', default=0, show_default=True, help="volume index to extract.")
def make_b0(input_path: str, output_path: str, idx: str):
    """From the DTI 4D data, choose a volume without diffusion weighting 
    (e.g. the first volume). You can now extract this as a standalone 3D image,
    using `fslroi` command. This function runs the `fslroi` command internally.
    """
    ret = generate_b0_from_dti(input_path, output_path, b0_idx=idx)
    if ret == 0:
        click.echo("Done.")

# --------------------------------- dtip > process module


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option("-o", "--output_path", default="./dtip_output", show_default=True, help="folder location to save output files.")
@click.option("-nm", "--nifti_method", type=click.Choice(['auto', 'dcm2nii', 'dcm2niix', 'dicom2nifti'], case_sensitive=False), default="auto", show_default=True, help="`auto` uses dcm2niix and dcm2nii to get best data and metadata. `dcm2niix` is Mricron's subpackage. `dcm2nii` is the previous version of dcm2niix. `dicom2nifti` is python package.")
@click.option('--strip_skull/--no-strip_skull', default=True, show_default=True, help="Perform skull stripping on DTI data. This step will be performed on eddy corrected DTI data.")
def process(input_path, output_path, nifti_method, strip_skull):
    """Perform DTI processing on one subject.

        INPUT_PATH - path to subject folder or zip file.
    """
    process_one_subject(input_path, output_path,
                        nifti_method=nifti_method,
                        strip_skull=strip_skull)
    # click.echo(click.format_filename(subject_path))


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option("-o", "--output_path", default="./dtip_output", show_default=True, help="folder location to save output files.")
@click.option("-nm", "--nifti_method", type=click.Choice(['auto', 'dcm2nii', 'dcm2niix', 'dicom2nifti'], case_sensitive=False), default="auto", show_default=True, help="`auto` uses dcm2niix and dcm2nii to get best data and metadata. `dcm2niix` is Mricron's subpackage. `dcm2nii` is the previous version of dcm2niix. `dicom2nifti` is python package.")
@click.option('--strip_skull/--no-strip_skull', default=True, show_default=True, help="Perform skull stripping on DTI data. This step will be performed on eddy corrected DTI data.")
@click.option("-ex", "--exclude", type=str, default='', show_default=True, help="pass a .txt file with the subject names you do not want to process in the given folder. Add one subject name per line.")
def process_multi(input_path, output_path, nifti_method, strip_skull, exclude):
    """Perform DTI processing on multiple subjects.

        INPUT_PATH - path to subjects folder containing each subjects DICOM data in a folder or zip file.
    """
    if exclude:
        with open(exclude) as ef:
            exclude_list = ef.read().split("\n")
            exclude_list = [n for n in exclude_list if n]
            # print(exclude_list)
    else:
        exclude_list = []
    process_multi_subjects(input_path, output_path,
                           nifti_method=nifti_method,
                           strip_skull=strip_skull,
                           exclude_list=exclude_list)

    # click.echo(click.format_filename(input_path))


# --------------------------------- dtip > register module

@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('-o', '--output_path', default='./register_pop_output', show_default=True, help="path/to/processed/subject_folder")
def register_pop_multi(input_path: str, output_path: str):
    """Perform population-based image registeration on the given subject using DTI-TK toolkit.

    Args:
        input_path: subject's preprocessed folder path. Perform `dtip process` command to process the subject before registration.
        output_path: location to save the registration output files.

    Returns:
        exit code 0 on successful execution.
    """
    ret = dtitk_register_pop_multi(input_path, output_path)
    if ret == 0:
        click.echo("Done.")


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('template_path', type=click.Path(exists=True))
@click.option('-mit', '--mean_initial_template_path', type=click.Path(exists=True), default=None, show_default=True)
@click.option('-o', '--output_path', default='./register_output', show_default=True, help="path/to/processed/subject_folder")
def register_multi(input_path: str, template_path: str, mean_initial_template_path: Union[str, None], output_path: str):
    """Perform image registeration using existing template on the given subjects using DTI-TK toolkit.

    Args:
        input_path: subject's preprocessed folder path. Perform `dtip process-multi` command to preprocess the subjects before registration.
        template_path: Path of the template to use for registration.
        mean_initial_template_path: A manually created mean_initial template using pecific subjects. This file can be created using `dtip make-template` CLI command.
        output_path: location to save the registration output files.

    Returns:
        exit code 0 on successful execution.
    """
    ret = dtitk_register_multi(input_path, template_path, mean_initial_template_path, output_path)
    if ret == 0:
        click.echo("Done.")


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('template_path', type=click.Path(exists=True))
@click.option('-mit', '--mean_initial_template_path', type=click.Path(exists=True), default=None, show_default=True)
@click.option('-o', '--output_path', default='./register_output', show_default=True, help="path/to/processed/subject_folder")
@click.option('--no_diffeo', is_flag=True, default=False, show_default=True)
def register(input_path: str, template_path: str, mean_initial_template_path:str, output_path: str, no_diffeo: bool):
    """Perform image registeration using existing template for single subject using DTI-TK toolkit.

    Args:
        input_path: subject's preprocessed folder path. Perform `dtip process` command to preprocess the subject before registration.
        template_path: Path of the template to use for registration.
        output_path: location to save the registration output files.

    Returns:
        exit code 0 on successful execution.
    """
    ret = dtitk_register(input_path, template_path, mean_initial_template_path, output_path, no_diffeo=no_diffeo)
    if ret == 0:
        click.echo("Done.")


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('template_path', type=click.Path(exists=True))
@click.option('-o', '--output_path', default='.', show_default=True, help="path/to/processed/subject_folder")
def make_template(input_path: str, template_path: str, output_path: str):
    """Create the initial template manually from selected subjects for ITS data.

    Args:
        input_path: folder path containing subjects' data given in `config.BEST_POPULATION_SUBSET` list. 
        template_path: Path of the template to use for registration.
        output_path: location to save the registration output files.

    Returns:
        exit code 0 on successful execution.
    """
    ret = make_initial_template_from_pop(input_path, template_path, output_path)
    if ret == 0:
        click.echo("Done.")


# --------------------------------- dtip > mapping module
@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('-o', '--output_path', default='dtitk_to_fsl_output', show_default=True, help="path/to/processed/subject_folder")
def dtitk_fsl_multi(input_path: str, output_path: str):
    """Convert DTI-TK specific format to FSL

        This function converts the registred files using DTI-TK back to FSL format. This function runs DTI-TK's `TVEigenSystem` command per subject and move the files to `output_path`.
    Args:
        input_path: folder path containing registred files in DTI-TK .nii.gz format.
        output_path: Move the converted files to this location.
    """
    ret = dtitk_to_fsl_multi(input_path, output_path)
    if ret == 0:
        click.echo("Done.")



if __name__ == '__main__':
    cli()
