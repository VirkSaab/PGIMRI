import os
import shutil
import subprocess
import nibabel as nib
from typing import Union
from pathlib import Path
from pgi.utils import SpinCursor
from pgi.config import *


__all__ = [
    "generate_index_file", "generate_acquisition_params_file",
    "generate_b0_from_dti"
]


def generate_index_file(src_filepath: Union[str, Path],
                        dst_filepath: Union[str, Path] = 'index.txt') -> int:
    """Create an index file with 1 per DTI volume.
    For example, there are 17 DTI volume (4th dimension) in DTIdata.nii.gz.
    Then, the index file will contain value 1 in 17 rows.

    Args:
        > src_filepath -- <DTI data file>.nii.gz file path.
        > dst_filepath -- name and path of the index file 
        like `save/here/index.txt`

    Returns:
        exit_code 0 if successfully executed.
    """

    img = nib.load(src_filepath)
    x, y, z, t = img.shape
    with open(dst_filepath, 'w') as idx_file:
        for _ in range(t):
            idx_file.write(f"1\n")
    return 0


def generate_acquisition_params_file(readout_time: float = READOUT_TIME,
                                     AP_PE: Union[list, str] = AP_PE,
                                     PA_PE: Union[list, str] = PA_PE,
                                     dst_filepath: Union[str,
                                                         Path] = "acqparams.txt"
                                     ) -> int:
    """Create the acquisition parameters file.
    This file contains the information with the PE direction, the sign of the
    AP and PA volumes and some timing information obtained by the acquisition. 
    The first three elements of each line comprise a vector that specifies the 
    direction of the phase encoding. The non-zero number in the second column 
    means that is along the y-direction. A -1 means that k-space was traversed 
    Anterior→Posterior and a 1 that it was traversed Posterior→Anterior. 
    The final column specifies the "total readout time", which is the time 
    (in seconds) between the collection of the centre of the first echo and the 
    centre of the last echo.

    Args:
        > readout_time -- "total readout time", which is the time (in seconds) 
        between the collection of the centre of the first echo and the 
        centre of the last echo.
        > AP_PE -- Anterior→Posterior Phase Encoding. Such as [0, -1, 0] 
        for y-direction or `j` vector. or '0,-1,0' as a string.
        > PA_PE -- Posterior→Anterior Phase Encoding.
        > dst_filepath -- path/to/file/acqparams.txt

    Returns:
        exit_code 0 if successfully executed.
    """
    if isinstance(AP_PE, str):
        AP_PE = AP_PE.split(",")
    if isinstance(PA_PE, str):
        PA_PE = PA_PE.split(",")

    first_line = f"{' '.join(AP_PE)} {readout_time}\n"
    second_line = f"{' '.join(PA_PE)} {readout_time}"

    with open(dst_filepath, 'w') as acq_file:
        acq_file.write(first_line)
        acq_file.write(second_line)

    return 0


def generate_b0_from_dti(src_filepath: Union[str, Path],
                         dst_filepath: Union[str, Path] = "b0_nodif.nii.gz",
                         b0_idx: int = 0) -> int:
    """Extract 3D B0 volume from 4D DTI nifti file. Usually first volume.

    Args:
        > src_filepath -- path/to/existing/DTIdata.nii.gz
        > dst_filepath -- path/to/save/b0.nii.gz
        > b0_idx -- b0 volume index number. Starting from zero.
    """
    dst_filepath = Path(dst_filepath)

    # With `fslsplit` command
    # with SpinCursor("Creating b0...", end=f"Saved at `{dst_filepath}`"):
    #     # Run the fslsplit command
    #     subprocess.run(['fslsplit', src_filepath, 'b0_tmp_'])
    #     # Copy the desired file
    #     shutil.move(f"b0_tmp_000{b0_idx}.nii.gz", dst_filepath)
    #     # Remove other unwanted files
    #     for name in [n for n in os.listdir(".") if n.startswith("b0_tmp_")]:
    #         os.remove(name)


    # With `fslroi` command
    with SpinCursor("Creating nodif...", end=f"Saved at `{dst_filepath}`"):
        # Run the fslsplit command
        subprocess.run(['fslroi', src_filepath, dst_filepath, str(b0_idx), '1'])
    return 0
