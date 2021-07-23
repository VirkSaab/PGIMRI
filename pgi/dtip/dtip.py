import dicom2nifti
import zipfile
import subprocess
from typing import Callable, Union
from pathlib import Path
from pgi.utils import get_logger, SpinCursor


logger = get_logger(__name__, to_file=f"dti_processing.log")


def process_one_subject(subject_path: Union[str, Path],
                        output_folder: Union[str, Path],
                        nifti_method: str = "dcm2niix",
                        compression: bool = True,
                        reorient: bool = True) -> None:
    """Perform DTI processing on the given subject

    Args:
        > subject_path -- Path to subject folder or zip file.
        > output_folder -- Path to output save location.
        > compression -- compress .nii file to .nii.gz.
        > reorient -- reorient the dicoms according to LAS orientation.
    """
    subject_path = Path(subject_path)
    output_folder = Path(output_folder)

    logger.debug(f"outputs will be saved at `{output_folder}`")

    # Step 1: Convert DICOM images to NIfTI format
    if nifti_method == "dcm2niix":
        step1_exit_code = dicom_to_nifti_cli(
            subject_path, output_folder, compression)
    elif nifti_method == "dicom2nifti":
        step1_exit_code = dicom_to_nifti_py(
            subject_path, output_folder, compression, reorient)
    else:
        _msg = "Only 2 methods are supported. `dcm2niix` and `dicom2nifti`"
        raise NotImplementedError(_msg)

    # Step 2: TOPUP - Correcting for Susceptibility-induced Distortions


def dicom_to_nifti_py(subject_path: Union[str, Path],
                      output_folder: Union[str, Path],
                      compression: bool = True,
                      reorient: bool = True) -> None:
    """Convert DICOM to NIfTI files.

    Args:
        > subject_path -- Path to subject folder or zip file.
        > output_folder -- Path to output save location.
        > compression -- compress .nii file to .nii.gz.
        > reorient -- reorient the dicoms according to LAS orientation.
    """

    nifti_path = output_folder/f"1_nifti/{subject_path.stem}"
    nifti_path.mkdir(parents=True, exist_ok=True)

    # unzip if given input is a zip file
    if subject_path.is_file():
        extract_to_path = output_folder/"0_extracted_files"
        extract_to_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting files to `{extract_to_path}`...")

        with zipfile.ZipFile(subject_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to_path)

        logger.info(f"done.")

        subject_path = extract_to_path

    logger.info(f"Converting DICOM to NIfTI...")

    with SpinCursor("dicom2nifti..."):
        dicom2nifti.convert_directory(
            dicom_directory=subject_path, output_folder=nifti_path,
            compression=compression, reorient=reorient
        )

    logger.info(f"done.")
    return 0  # return 0 means successful execution


def dicom_to_nifti_cli(subject_path, output_folder, compression=True):
    nifti_path = output_folder/f"1_nifti/{subject_path.stem}"
    nifti_path.mkdir(parents=True, exist_ok=True)

    # unzip if given input is a zip file
    if subject_path.is_file():
        extract_to_path = output_folder/"0_extracted_files"
        extract_to_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting files to `{extract_to_path}`...")

        with zipfile.ZipFile(subject_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to_path)

        logger.info(f"done.")

        subject_path = extract_to_path/zip_ref.namelist()[0].split("/")[0]

    logger.info(f"Converting DICOM to NIfTI...")

    command = ["dcm2niix"]
    
    if compression:
        command += ['-z', 'y']

    command += ['-p', 'y', '-o', nifti_path, subject_path]
    try:
        subprocess.run(command)
        return 0
    except FileNotFoundError:
        _msg = "[dcm2niix error] Make sure `dcm2niix` is installed. If not,"
        _msg += "Try `sudo apt install dcm2niix`"
        logger.error(_msg)
        return 1






