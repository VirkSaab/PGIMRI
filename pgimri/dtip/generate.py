import shutil
import subprocess
import nibabel as nib
from typing import Union
from pathlib import Path
from pgimri.utils import SpinCursor, show_exec_time
from pgimri.dtip.register import dtitk_register
from pgimri.config import *


__all__ = [
    "generate_index", "generate_acquisition_params",
    "generate_b0_from_dti", "generate_avg_b0", "generate_brain_mask",
    "make_initial_template_from_pop"
]


def generate_b0_from_dti(input_path: Union[str, Path],
                         output_path: Union[str, Path] = "b0.nii.gz",
                         b0_idx: int = 0) -> int:
    """Extract 3D B0 volume from 4D DTI nifti file. Usually first volume.

    Args:
        input_path: path/to/existing/DTIdata.nii.gz
        output_path: path/to/save/b0.nii.gz
        b0_idx: b0 volume index number. Starting from zero.

    Returns:
        exit_code 0 if successfully executed.
    """
    output_path = Path(output_path)

    # With `fslsplit` command
    # with SpinCursor("Creating b0...", end=f"Saved at `{output_path}`"):
    #     # Run the fslsplit command
    #     subprocess.run(['fslsplit', input_path, 'b0_tmp_'])
    #     # Copy the desired file
    #     shutil.move(f"b0_tmp_000{b0_idx}.nii.gz", output_path)
    #     # Remove other unwanted files
    #     for name in [n for n in os.listdir(".") if n.startswith("b0_tmp_")]:
    #         os.remove(name)

    # With `fslroi` command
    with SpinCursor("Creating b0...", end=f"Saved at `{output_path}`"):
        subprocess.run(['fslroi', input_path, output_path, str(b0_idx), '1'])
    return 0


def generate_acquisition_params(readout_time: float = READOUT_TIME,
                                AP_PE: Union[list, str] = AP_PE,
                                PA_PE: Union[list, str] = PA_PE,
                                output_path: Union[str, Path] = "acqp.txt"
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
        readout_time: "total readout time", which is the time (in seconds) between the collection of the centre of the first echo and the centre of the last echo.
        AP_PE: Anterior→Posterior Phase Encoding. Such as [0, -1, 0] for y-direction or `j` vector. or '0,-1,0' as a string.
        PA_PE: Posterior→Anterior Phase Encoding.
        output_path: path/to/file/acqparams.txt

    Returns:
        exit_code 0 if successfully executed.
    """
    if isinstance(AP_PE, str):
        AP_PE = AP_PE.split(",")
    if isinstance(PA_PE, str):
        PA_PE = PA_PE.split(",")

    first_line = f"{' '.join(map(str, AP_PE))} {readout_time}\n"
    if PA_PE:
        second_line = f"{' '.join(map(str, AP_PE))} {readout_time}"

    with open(output_path, 'w') as acq_file:
        acq_file.write(first_line)
        if PA_PE:
            acq_file.write(second_line)

    return 0


def generate_index(input_path: Union[str, Path],
                   output_path: Union[str, Path] = 'index.txt') -> int:
    """Create an index file with value 1 in each row per DTI volume.

    For example, there are 17 DTI volume (4th dimension) in DTIdata.nii.gz.
    Then, the index file will contain value 1 in 17 rows.

    Args:
        input_path: <DTI data file>.nii.gz file path.
        output_path: name and path of the index file like `save/here/index.txt`

    Returns:
        exit_code 0 if successfully executed.
    """

    img = nib.load(input_path)
    x, y, z, t = img.shape
    with open(output_path, 'w') as idx_file:
        for _ in range(t):
            idx_file.write(f"1\n")
    return 0


def generate_avg_b0(input_path: Union[str, Path],
                    output_path: Union[str, Path] = 'b0') -> int:
    # With `fslmaths` command
    with SpinCursor("Creating averaged b0...", end=f"Saved at `{output_path}`"):
        subprocess.run(['fslmaths', input_path, '-Tmean', output_path])
    return 0


def generate_brain_mask(input_path: Union[str, Path],
                        output_path: Union[str, Path] = 'b0_brain',
                        f_value: float = 0.2) -> int:
    # With `fslmaths` command
    with SpinCursor("Creating brain mask...", end=f"Saved at `{output_path}`"):
        subprocess.run([
            'bet', input_path, output_path,
            '-m', '-f', str(f_value)
        ])
    return 0

@show_exec_time
def make_initial_template_from_pop(input_path: Union[str, Path],
                                   template_path: Union[str, Path],
                                   output_path: Union[str, Path]):
    """Create the initial template manually from selected subjects for ITS data.

    Args:
        input_path: folder path containing subjects' data given in `config.BEST_POPULATION_SUBSET` list. 
        template_path: Path of the template to use for registration.
        output_path: location to save the registration output files.

    Returns:
        exit code 0 on successful execution.
    """
    input_path, template_path = Path(input_path), Path(template_path)
    orig_output_path, output_path = Path(output_path), Path(".tmp_mit")
    output_path.mkdir(exist_ok=True)

    subs_filepaths = []
    for subject_name in BEST_POPULATION_SUBSET:
        subject_path = input_path/subject_name
        ret = dtitk_register(subject_path, template_path, mean_initial_template_path=None, output_path=output_path, no_diffeo=True)
        if ret != 0:
            raise RuntimeError("Something wrong in the registration.")

        filename = f"{PROCESSED_DTI_FILENAME}_dtitk_aff.nii.gz"
        filepath = f"{output_path/subject_name}/{filename}"
        subs_filepaths.append(filepath)

    # Create a file with subset names
    subs_filepath = output_path/"template_subs.txt"
    with open(subs_filepath, "w") as subf:
        for filepath in subs_filepaths:
            subf.write(f"{filepath}\n")

    # Run the `dti_template_bootstrap` command
    subprocess.run([
        "dti_template_bootstrap", template_path, subs_filepath, '-SMOption', 'EDS', '4', '4', '4', '0.0001'
    ])

    X_SIZE, Y_SIZE, Z_SIZE = TEMPLATE_SPATIAL_DIMS
    XV, YV, ZV = TEMPLATE_VOXEL_SPACE
    OX, OY, OZ = TEMPLATE_ORIGIN
    resample_cmd = [
        'TVResample', '-in', "mean_initial.nii.gz",
        '-out', "mean_initial.nii.gz",
        '-align', 'center',
        '-size', str(X_SIZE), str(Y_SIZE), str(Z_SIZE),
        '-vsize', str(XV), str(YV), str(ZV),
    ]
    if OX and OY and OZ:
        resample_cmd += ['-origin', str(OX), str(OY), str(OZ)]
    subprocess.run(resample_cmd)
    
    print(f"Resampled mean_initial image to ({X_SIZE}, {Y_SIZE}, {Z_SIZE}). Saved at `mean_initial.nii.gz`.")

    # Reset the origin to zero
    subprocess.run([
        'TVAdjustVoxelspace',
        '-in', 'mean_initial.nii.gz',
        '-out', 'mean_initial.nii.gz',
        '-origin', '0', '0', '0'
    ])

    # Threshold the trailing borders
    subprocess.run([
        'fslmaths', 'mean_initial.nii.gz', '-thr', '0.30', 'mean_initial.nii.gz'
    ])

    # Move the created `mean_initial.nii.gz` to output_path location
    save_path = orig_output_path/"mean_initial_template.nii.gz"
    shutil.move("mean_initial.nii.gz", save_path)
    print(f"New template saved at `{save_path}`.")
    
    # Remove extra files generated for this template
    # shutil.rmtree(output_path)
    return 0