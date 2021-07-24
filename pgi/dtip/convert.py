import os
import subprocess
from typing import Union, Tuple
from pathlib import Path
from pgi.utils import get_logger, SpinCursor
from pgi.config import *

logger = get_logger(__name__)


def convert_dicom_to_nifti(src_folder: Union[str, Path],
                           dst_folder: Union[str, Path],
                           method: str = "auto",
                           compression: bool = True,
                           reorient: bool = True) -> str:
    """Convert all DICOM files in `src_folder` to NIfTI (.nii or .nii.gz) files.

    Args:
        > src_folder -- folder path containing DICOM files of a subject.
        > dst_folder -- folder path where output files will be saved.
        > method -- Choose one of the following conversion methods: 
        `auto` (whichever works best for each subject), `dicom2nifti` (python package), `dcm2nii` (MRICron), and
        `dcm2niix` (newer version of dcm2nii). [default: `auto`]
        > compression -- compress .nii file to .nii.gz.
        > reorient -- reorient the dicoms according to LAS orientation.
    """

    src_folder, dst_folder = Path(src_folder), Path(dst_folder)
    
    if not src_folder.is_dir():
        raise NotADirectoryError("DICOM files must be in a folder.")
    
    dst_folder.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Converting `{src_folder}` using {method}...")

    if method == "auto":
        raise NotImplementedError
    elif method == "dcm2nii":
        exit_code = method_dcm2nii(src_folder, dst_folder, compression)
    elif method == "dcm2niix":
        raise NotImplementedError
    elif method == "dicom2nifti":
        raise NotImplementedError
    else:
        _msg = f"Given {method} method not supported."
        _msg += "Only supports `auto`, `dcm2nii`, `dcm2niix`, or `dicom2nifti`"
        raise NotImplementedError(_msg)


def method_dcm2nii(src_folder: Union[str, Path],
                   dst_folder: Union[str, Path],
                   compression: bool = True,
                   reorient: bool = True) -> Tuple[str, str]:
    """DICOM to NIfTI conversion using dcm2nii command.

    Args:
        > src_folder -- folder path containing DICOM files of a subject.
        > dst_folder -- folder path where output files will be saved.
        > compression -- compress .nii file to .nii.gz.
        > reorient -- reorient the dicoms according to LAS orientation.
    """

    command = ['dcm2nii', '-4', 'Y']
    if compression:
        command += ['-g', 'Y']
    command += ['-x', 'Y', '-t', 'Y', '-o', dst_folder, src_folder]

    with SpinCursor("dcm2nii conversion..."):
        try:
            subprocess.run(command) # Run command
            return 0

        except FileNotFoundError:
            _msg = "[dcm2nii error] Make sure `dcm2nii` is installed."
            logger.error(_msg)
            return 1