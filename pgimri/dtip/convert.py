import os
import shutil
import subprocess
import dicom2nifti
from typing import Union, Tuple
from pathlib import Path
from pgimri.utils import get_logger, SpinCursor
from pgimri.config import *
from rich.progress import track

logger = get_logger(__name__)

__all__ = [
    "convert_dicom_to_nifti", "fsl_to_dtitk_multi",
]


def convert_dicom_to_nifti(input_path: Union[str, Path],
                           output_path: Union[str, Path],
                           method: str = "auto",
                           compression: bool = True,
                           reorient: bool = True) -> int:
    """Convert all DICOM files in `input_path` to NIfTI (.nii or .nii.gz) files.

    Args:
        input_path: folder path containing DICOM files of a subject.
        output_path: folder path where output files will be saved.
        method: Choose one of the following conversion methods: 
        `auto` (whichever works best for each subject), `dicom2nifti` (python package), `dcm2nii` (MRICron), and
        `dcm2niix` (newer version of dcm2nii). [default: `auto`]
        compression: compress .nii file to .nii.gz.
        reorient: reorient the dicoms according to LAS orientation.

    Returns:
        Nothing
    """

    input_path, output_path = Path(input_path), Path(output_path)

    if not input_path.is_dir():
        raise NotADirectoryError("DICOM files must be in a folder.")

    output_path.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Converting `{input_path}` using {method}...")

    if method == "auto":
        exit_code = method_dcm2nii(input_path, output_path, compression)
        x_exit_code = method_dcm2niix(input_path, output_path, compression)
    elif method == "dcm2nii":
        exit_code = method_dcm2nii(input_path, output_path, compression)
    elif method == "dcm2niix":
        exit_code = method_dcm2niix(input_path, output_path, compression)
    elif method == "dicom2nifti":
        exit_code = method_dicom2nifti(
            input_path, output_path, compression, reorient)
    else:
        _msg = f"Given {method} method not supported."
        _msg += "Only supports `auto`, `dcm2nii`, `dcm2niix`, or `dicom2nifti`"
        raise NotImplementedError(_msg)

    return 0


def method_dcm2nii(input_path: Union[str, Path],
                   output_path: Union[str, Path],
                   compression: bool = True,
                   reorient: bool = True) -> int:
    """DICOM to NIfTI conversion using dcm2nii command.

    Args:
        input_path: folder path containing DICOM files of a subject.
        output_path: folder path where output files will be saved.
        compression: compress .nii file to .nii.gz.
        reorient: reorient the dicoms according to LAS orientation.

    Returns:
        exit_code 0 if no errors. else 1.
    """

    command = ['dcm2nii', '-4', 'Y']
    if compression:
        command += ['-g', 'Y']
    if reorient:
        command += ['-x', 'Y']
    command += ['-t', 'Y', '-d', 'N', '-o', output_path, input_path]

    with SpinCursor("dcm2nii conversion..."):
        try:
            subprocess.run(command)  # Run command
            return 0

        except FileNotFoundError:
            _msg = "[dcm2nii error] Make sure `dcm2nii` is installed."
            logger.error(_msg)
            return 1


def method_dcm2niix(input_path: Union[str, Path],
                    output_path: Union[str, Path],
                    compression: bool = True,
                    reorient: bool = True) -> int:
    """DICOM to NIfTI conversion using dcm2niix command.

    Args:
        input_path: folder path containing DICOM files of a subject.
        output_path: folder path where output files will be saved.
        compression: compress .nii file to .nii.gz.
        reorient: reorient the dicoms according to LAS orientation.

    Returns:
        exit_code 0 if no errors. else 1.
    """

    command = ["dcm2niix"]

    if compression:
        command += ['-z', 'y']
    if reorient:
        command += ['-x', 'y']
    command += ['-p', 'y', '-f', '%p_s%s', '-o', output_path, input_path]

    with SpinCursor("dcm2niix conversion..."):
        try:
            subprocess.run(command)  # Run command
            return 0

        except FileNotFoundError:
            _msg = "[dcm2niix error] dcm2niix not found on system."
            logger.error(_msg)
            return 1


def method_dicom2nifti(input_path: Union[str, Path],
                       output_path: Union[str, Path],
                       compression: bool = True,
                       reorient: bool = True) -> int:
    """DICOM to NIfTI conversion using dicom2nifti python package.

    Args:
        input_path: folder path containing DICOM files of a subject.
        output_path: folder path where output files will be saved.
        compression: compress .nii file to .nii.gz.
        reorient: reorient the dicoms according to LAS orientation.

    Returns:
        exit_code 0 if no errors. else 1.
    """

    with SpinCursor("dicom2nifti conversion..."):
        try:
            dicom2nifti.convert_directory(
                dicom_directory=input_path, output_folder=output_path,
                compression=compression, reorient=reorient
            )
            return 0
        except:
            logger.error("Error occurred at `method_dicom2nifti` function")
            return 1


def fsl_to_dtitk_multi(input_path: Union[Path, str],
                       output_path: Union[Path, str]) -> int:
    """Convert FSL to DTI-TK specific format
    Args:
        input_path: folder path containing subjects' data.

    """
    input_path, output_path = Path(input_path), Path(output_path)

    subjects = list(Path(input_path).glob("*"))
    total_subjects = len(subjects)
    for i, subject_path in enumerate(subjects, start=1):
        basename = f"{subject_path}/{PROCESSED_DTI_FILENAME}"
        subprocess.run(["fsl_to_dtitk", basename])
        print(f"[{i}/{total_subjects}] Converted `{subject_path}`.")

        # Move output files to `output_path`
        move_to = output_path/subject_path.stem
        move_to.mkdir(parents=True, exist_ok=True)
        # print("MOVED HERE =", move_to)
        dtitk_basename = f"{PROCESSED_DTI_FILENAME}_dtitk"
        for dtitk_filepath in Path(subject_path).glob("*"):
            if str(dtitk_filepath.stem).startswith(dtitk_basename):
                # print("FILE =", dtitk_filepath.name)
                shutil.move(dtitk_filepath, move_to/dtitk_filepath.name)
    
    print("Done!")
    return 0 # exit code 0 for successful execution.
