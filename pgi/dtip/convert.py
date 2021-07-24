import os
import subprocess
import dicom2nifti
from typing import Union, Tuple
from pathlib import Path
from pgi.utils import get_logger, SpinCursor
from pgi.config import *

logger = get_logger(__name__)


def convert_dicom_to_nifti(src_folder: Union[str, Path],
                           dst_folder: Union[str, Path],
                           method: str = "auto",
                           compression: bool = True,
                           reorient: bool = True) -> None:
    """Convert all DICOM files in `src_folder` to NIfTI (.nii or .nii.gz) files.

    Args:
        > src_folder -- folder path containing DICOM files of a subject.
        > dst_folder -- folder path where output files will be saved.
        > method -- Choose one of the following conversion methods: 
        `auto` (whichever works best for each subject), `dicom2nifti` (python package), `dcm2nii` (MRICron), and
        `dcm2niix` (newer version of dcm2nii). [default: `auto`]
        > compression -- compress .nii file to .nii.gz.
        > reorient -- reorient the dicoms according to LAS orientation.

    Returns:
        Nothing
    """

    src_folder, dst_folder = Path(src_folder), Path(dst_folder)

    if not src_folder.is_dir():
        raise NotADirectoryError("DICOM files must be in a folder.")

    dst_folder.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Converting `{src_folder}` using {method}...")

    if method == "auto":
        exit_code = method_dcm2nii(src_folder, dst_folder, compression)
        x_exit_code = method_dcm2niix(src_folder, dst_folder, compression)
    elif method == "dcm2nii":
        exit_code = method_dcm2nii(src_folder, dst_folder, compression)
    elif method == "dcm2niix":
        exit_code = method_dcm2niix(src_folder, dst_folder, compression)
    elif method == "dicom2nifti":
        exit_code = method_dicom2nifti(
            src_folder, dst_folder, compression, reorient)
    else:
        _msg = f"Given {method} method not supported."
        _msg += "Only supports `auto`, `dcm2nii`, `dcm2niix`, or `dicom2nifti`"
        raise NotImplementedError(_msg)


def method_dcm2nii(src_folder: Union[str, Path],
                   dst_folder: Union[str, Path],
                   compression: bool = True,
                   reorient: bool = True) -> int:
    """DICOM to NIfTI conversion using dcm2nii command.

    Args:
        > src_folder -- folder path containing DICOM files of a subject.
        > dst_folder -- folder path where output files will be saved.
        > compression -- compress .nii file to .nii.gz.
        > reorient -- reorient the dicoms according to LAS orientation.

    Returns:
        exit_code 0 if no errors. else 1.
    """

    command = ['dcm2nii', '-4', 'Y']
    if compression:
        command += ['-g', 'Y']
    if reorient:
        command += ['-x', 'Y']
    command += ['-t', 'Y', '-d', 'N', '-o', dst_folder, src_folder]

    with SpinCursor("dcm2nii conversion..."):
        try:
            subprocess.run(command)  # Run command
            return 0

        except FileNotFoundError:
            _msg = "[dcm2nii error] Make sure `dcm2nii` is installed."
            logger.error(_msg)
            return 1


def method_dcm2niix(src_folder: Union[str, Path],
                    dst_folder: Union[str, Path],
                    compression: bool = True,
                    reorient: bool = True) -> int:
    """DICOM to NIfTI conversion using dcm2niix command.

    Args:
        > src_folder -- folder path containing DICOM files of a subject.
        > dst_folder -- folder path where output files will be saved.
        > compression -- compress .nii file to .nii.gz.
        > reorient -- reorient the dicoms according to LAS orientation.

    Returns:
        exit_code 0 if no errors. else 1.
    """

    command = ["dcm2niix"]

    if compression:
        command += ['-z', 'y']
    if reorient:
        command += ['-x', 'y']
    command += ['-p', 'y', '-f', '%p_s%s', '-o', dst_folder, src_folder]

    with SpinCursor("dcm2niix conversion..."):
        try:
            subprocess.run(command)  # Run command
            return 0

        except FileNotFoundError:
            _msg = "[dcm2niix error] dcm2niix not found on system."
            logger.error(_msg)
            return 1


def method_dicom2nifti(src_folder: Union[str, Path],
                       dst_folder: Union[str, Path],
                       compression: bool = True,
                       reorient: bool = True) -> int:
    """DICOM to NIfTI conversion using dicom2nifti python package.

    Args:
        > src_folder -- folder path containing DICOM files of a subject.
        > dst_folder -- folder path where output files will be saved.
        > compression -- compress .nii file to .nii.gz.
        > reorient -- reorient the dicoms according to LAS orientation.

    Returns:
        exit_code 0 if no errors. else 1.
    """

    with SpinCursor("dicom2nifti conversion..."):
        try:
            dicom2nifti.convert_directory(
                dicom_directory=src_folder, output_folder=dst_folder,
                compression=compression, reorient=reorient
            )
            return 0
        except:
            logger.error("Error occurred at `method_dicom2nifti` function")
            return 1
