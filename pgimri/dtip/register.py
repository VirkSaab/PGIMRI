"""This scripts includes DTI image registration and required pre and post processing to perform correct registration. I followed the official DTI-TK tutorials. The steps listed below are taken from here:
    http://dti-tk.sourceforge.net/pmwiki/pmwiki.php?n=Documentation.Interoperability
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Union
from pgimri.config import *
from pgimri.utils import *
from pgimri.dtip.convert import fsl_to_dtitk_multi
from rich.traceback import install as rich_traceback_install


rich_traceback_install()  # For better trackback display
logger = get_logger(__name__)

__all__ = ["dtitk_register_pop_multi", "dtitk_register_multi"]


@show_exec_time
def dtitk_register_pop_multi(input_path: Union[Path, str],
                             output_path: Union[Path, str]) -> int:
    """DTI Population-based Image Registration using Diffusion Tensor Imaging ToolKit (DTI-TK)

    Args:
        input_path: folder path containing subjects' data.
        output_path: location to save the output files.

    Returns:
        exit code 0 on completion.
    """
    input_path, output_path = Path(input_path), Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # * Add dtitk tool to PATH
    dtitk_maindir = f"{Path(__file__).parent.parent.parent}/dtitk"
    os.environ["DTITK_ROOT"] = dtitk_maindir
    os.environ["PATH"] += f":{dtitk_maindir}/bin:{dtitk_maindir}/utilities:{dtitk_maindir}/scripts"

    # * Step 1: Convert FSL format to DTI-TK format and move files
    # * to `output_path`.
    exit_code = fsl_to_dtitk_multi(input_path, output_path)
    if exit_code != 0:  # Stop here if any error
        _msg = "Error in `dtitk_register_multi` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.debug(
        f"Converted `{input_path}` to DTI-TK format and saved at `{output_path}`.")

    # * SPATIAL NORMALIZATION AND ATLAS CONSTRUCTION
    # * Step 2. Bootstrapping the initial DTI template from the input DTI volumes
    # copy good aligned scans to create an initial template
    copied_files = []
    logger.debug(f"Copying these files for bootstrap template {copied_files}")
    for subject_path in output_path.glob('*'):
        if subject_path.stem in BEST_POPULATION_SUBSET:
            filename = f"{PROCESSED_DTI_FILENAME}_dtitk.nii.gz"
            filepath = f"{subject_path}/{filename}"
            dst = f"{subject_path.stem}_{filename}"
            copied_files.append(dst)
            shutil.copy2(filepath, dst)
    logger.debug("Copied!")

    # Create a file with subset names
    with open("subset.txt", "w") as subf:
        for filename in copied_files:
            subf.write(f"{filename}\n")

    # create the initial bootstrapped template with the subset data
    logger.debug(f"Creating bootstrap template using {copied_files}")
    template_path = "mean_initial.nii.gz"
    subprocess.run(['TVMean', '-in', 'subset.txt', '-out', template_path])
    logger.debug(f"Created bootstrap template @ `{template_path}`.")
    # resample the template into a voxel space with the voxel dimensions
    # being powers of 2
    logger.info(
        "Resampling template into a voxel space with the voxel dimensions being powers of 2")
    W, H, D = [str(v) for v in TEMPLATE_SPATIAL_DIMS]
    X, Y, Z = [str(v) for v in TEMPLATE_VOXEL_SPACE]
    subprocess.run([
        'TVResample', '-in', template_path, '-align', 'center', '-size',
        W, H, D, '-vsize', X, Y, Z
    ])
    logger.info("Done!")
    # remove copied files
    logger.debug("Removing copied files...")
    for filename in copied_files:
        subprocess.run(['rm', filename])
    subprocess.run(['rm', 'subset.txt'])
    logger.debug("Removed.")

    # * Step 3: Rigid Alignment of DTI Volumes
    # in the context of spatial normalization, the goal is to align a set
    # of DTI volumes
    logger.info("Starting Rigid Alignment of DTI Volumes...")
    with open("subjects.txt", "w") as sjf:
        for subject_path in output_path.glob("*"):
            if subject_path.is_dir():
                filename = f"{PROCESSED_DTI_FILENAME}_dtitk.nii.gz"
                filepath = f"{subject_path}/{filename}"
                print(filepath)
                sjf.write(f"{filepath}\n")
    logger.debug(
        "Created subjects.txt file for `dti_rigid_population` command.")

    subprocess.run([
        'dti_rigid_population', template_path, 'subjects.txt', 'EDS', str(
            NUM_ALIGN_ITERS)
    ])
    logger.info("Done!")

    # Check new affine volumes
    for subject_path in Path(output_path).glob("*"):
        if subject_path.is_dir():
            filepath = subject_path / \
                f"{PROCESSED_DTI_FILENAME}_dtitk_aff.nii.gz"
            if not filepath.exists():
                _msg = f"`{filepath}` not found at `{subject_path}`."
                _msg += "Make sure `dti_rigid_population` command ran correctly."
                _msg += " Check its log."
                raise RuntimeError(_msg)

    # * Step 4: Affine alignment with template refinement
    logger.info("Affine alignment with template refinement...")
    subprocess.run([
        'dti_affine_population', template_path, 'subjects.txt', 'EDS', str(
            NUM_ALIGN_ITERS)
    ])
    logger.info("Done!")

    # * Step 5: Deformable alignment with template refinement
    # generate the mask image
    logger.info("Generating mask...")
    subprocess.run(
        ['TVtool', '-in', f'mean_affine{NUM_ALIGN_ITERS}.nii.gz', '-tr'])
    subprocess.run([
        'BinaryThresholdImageFilter', f'mean_affine{NUM_ALIGN_ITERS}_tr.nii.gz', 'mask.nii.gz',
        '0.01', '100', '1', '0'
    ])
    logger.warning(
        "Really important to check that the mask is appropriate before embarking on the next most time-consuming step.")
    logger.info("Done!")

    # Run alignment
    logger.info("Deformable alignment with template refinement...")
    subprocess.run([
        'dti_diffeomorphic_population', f'mean_affine{NUM_ALIGN_ITERS}.nii.gz',
        'subjects_aff.txt', 'mask.nii.gz', '0.002'
    ])
    logger.info("Done!")

    # Move extra generated files to output_path folder
    logger.info(f"Moving all generated files to `{output_path}`")
    for filename in Path('.').glob("*"):
        if filename.is_file():
            filename = str(filename)
            # collect NIfTI mean files
            if filename.startswith('mean_') and filename.endswith('.nii.gz'):
                print(f"Moving `{filename}` to `{output_path}`")
                shutil.move(filename, output_path/filename)
            # collect mask file
            if filename == "mask.nii.gz":
                print(f"Moving `{filename}` to `{output_path}`")
                shutil.move(filename, output_path/filename)
            # collect subjects
            if filename.startswith('subjects') and filename.endswith('.txt'):
                print(f"Moving `{filename}` to `{output_path}`")
                shutil.move(filename, output_path/filename)
            # collect affine and diffeo text files
            if filename == "affine.txt" or filename == "diffeo.txt":
                print(f"Moving `{filename}` to `{output_path}`")
                shutil.move(filename, output_path/filename)
    logger.info("Done!")

    return 0


@show_exec_time
def dtitk_register_multi(input_path: Union[Path, str],
                         template_path: Union[Path, str],
                         output_path: Union[Path, str]) -> int:
    """DTI existing Template-based Image Registration using Diffusion Tensor Imaging ToolKit (DTI-TK)

    Args:
        input_path: folder path containing a subject's data.
        template_path: Path of the template to use for registration.
        output_path: location to save the output files.

    Returns:
        exit code 0 on completion.
    """
    input_path, output_path = Path(input_path), Path(output_path)
    template_path = Path(template_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # * Add dtitk tool to PATH
    dtitk_maindir = f"{Path(__file__).parent.parent.parent}/dtitk"
    os.environ["DTITK_ROOT"] = dtitk_maindir
    os.environ["PATH"] += f":{dtitk_maindir}/bin:{dtitk_maindir}/utilities:{dtitk_maindir}/scripts"

    # * Step 1: Convert FSL format to DTI-TK format and move files
    # * to `output_path`.
    exit_code = fsl_to_dtitk_multi(input_path, output_path)
    if exit_code != 0:  # Stop here if any error
        _msg = "Error in `dtitk_register_multi` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.debug(
        f"Converted `{input_path}` to DTI-TK format and saved at `{output_path}`.")

    # * SPATIAL NORMALIZATION AND ATLAS CONSTRUCTION
    # * Step 2. Bootstrapping the initial DTI template from the input DTI volumes

    # Get subjects' DTI file paths
    subs_filepaths = []
    for subject_path in output_path.glob("*"):
        if subject_path.is_dir():
            filename = f"{PROCESSED_DTI_FILENAME}_dtitk.nii.gz"
            filepath = f"{subject_path}/{filename}"
            subs_filepaths.append(filepath)

    # Create a file with subset names
    subs_filepath = output_path/"subs.txt"
    with open(subs_filepath, "w") as subf:
        for filepath in subs_filepaths:
            subf.write(f"{filepath}\n")

    # Run the `dti_template_bootstrap` command
    subprocess.run([
        "dti_template_bootstrap", template_path, subs_filepath
    ])

    # Move the mean_initial.nii.gz file to `output_path`
    # template_path = output_path/"mean_initial.nii.gz"
    # shutil.move("mean_initial.nii.gz", template_path)

    template_path = "mean_initial.nii.gz"
    subprocess.run([
        'TVResample', '-in', template_path,
        '-out', 'mean_initial_resampled.nii.gz',
        '-align', 'center', 
        '-size', X_SIZE, Y_SIZE, Z_SIZE,
        '-vsize', '1', '1', '1'
    ])
    template_path = 'mean_initial_resampled.nii.gz'

    # Check new affine volumes
    for subject_path in Path(output_path).glob("*"):
        if subject_path.is_dir():
            filepath = subject_path / \
                f"{PROCESSED_DTI_FILENAME}_dtitk_aff.nii.gz"
            if not filepath.exists():
                _msg = f"`{filepath}` not found at `{subject_path}`."
                _msg += "Make sure `dti_rigid_population` command ran correctly."
                _msg += " Check its log."
                raise RuntimeError(_msg)

    # * Step 3: Rigid Alignment of DTI Volumes (SKIPPED AS PER INSTRUCTIONS IN THE DTI-TK TUTORIAL)
    # This step is not required when step 2 is performed with existing template.

    # * Step 4: Affine alignment with template refinement
    logger.info("Affine alignment with template refinement...")
    for i, subject_path in enumerate(subs_filepaths, start=1):
        logger.info(f"[{i}/{len(subs_filepaths)}] Affine alignment of `{subject_path}`...")
        subprocess.run([
            'dti_affine_reg', template_path, subject_path,
            'EDS', '4', '4', '4', '0.01', '1'
        ])
        logger.info("Done!")
    logger.info("Affine alignment completed!")

    # * Step 5: Deformable alignment with template refinement
    # Get subjects' DTI file paths
    for subject_path in output_path.glob("*"):
        if subject_path.is_dir():
            logger.info(f"Deformable alignment of subject `{subject_path}`...")
            filename = f"{PROCESSED_DTI_FILENAME}_dtitk_aff.nii.gz"
            filepath = f"{subject_path}/{filename}"
            # generate the mask image
            logger.info("Generating mask...")
            # mask_path = output_path/'mask.nii.gz'
            subprocess.run(['TVtool', '-in', template_path, '-tr', '-out', 'template_tr.nii.gz'])
            subprocess.run([
                'BinaryThresholdImageFilter', 'template_tr.nii.gz', 'mask.nii.gz',
                '0.01', '100', '1', '0'
            ])
            logger.warning(
                "Really important to check that the mask is appropriate before embarking on the next most time-consuming step.")
            logger.info("Done!")

            # Run alignment
            logger.info("Deformable alignment with template refinement...")
            subprocess.run([
                'dti_diffeomorphic_reg', 
                template_path, filepath, 'mask.nii.gz',
                '1', '6', '0.002'
            ])
            logger.info("Done!")

    # Move extra generated files to output_path folder
    logger.info(f"Moving all generated files to `{output_path}`")
    for filename in Path('.').glob("*"):
        if filename.is_file():
            filename = str(filename)
            # collect NIfTI mean files
            if filename.startswith('mean_') and filename.endswith('.nii.gz'):
                print(f"Moving `{filename}` to `{output_path}`")
                shutil.move(filename, output_path/filename)
            # collect mask file
            if filename == "mask.nii.gz":
                print(f"Moving `{filename}` to `{output_path}`")
                shutil.move(filename, output_path/filename)
            if filename.startswith('template'):
                print(f"Moving `{filename}` to `{output_path}`")
                shutil.move(filename, output_path/filename)
    logger.info("Registration complete!")

    return 0