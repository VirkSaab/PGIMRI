"""This module implements the DTI preprocessing pipeline for one and multi
    subject DTI data.

    The steps involved in this pipeline are:
    
    0. Extract data from subject's zip file, if input is a zip file.
    1. convert DICOM files to NIfTI.
    2. locate relevant DTI data and metadata files and saved them separately.
    3. TOPUP - Susceptibility-induced distortions corrections. Also, generate acqparams.txt and b0.nii.gz files from existing data to perform this step.
    4. EDDY - Eddy currents corrections. This step will also generate averaged b0 and brain mask NifTI files from existing data to perform this step.
    5. DTIFIT - fitting diffusion tensors
"""

import subprocess
from typing import Union
from pathlib import Path
from rich.traceback import install as rich_traceback_install
from pgimri.utils import get_logger, SpinCursor
from pgimri.dtip.extract import extract_subject
from pgimri.dtip.convert import convert_dicom_to_nifti
from pgimri.dtip.locate import locate_data_files
from pgimri.dtip.generate import *


__all__ = ["process_one_subject", "process_multi_subjects"]

rich_traceback_install() # For better trackback display
logger = get_logger(__name__)



def run_dtifit(input_path: Union[str, Path],
               brain_mask_path: Union[str, Path],
               bvecs_path: Union[str, Path],
               bvals_path: Union[str, Path],
               output_path: Union[str, Path]) -> int:

    with SpinCursor("Running dtifit...", end=f"Saved at `{output_path}`"):
        subprocess.run([
            "dtifit",
            f"--data={input_path}",
            f"--mask={brain_mask_path}",
            f"--bvecs={bvecs_path}",
            f"--bvals={bvals_path}",
            f"--out={output_path}"
        ])

    return 0


def run_topup(input_path: Union[str, Path],
              acqp_path: Union[str, Path],
              output_path: Union[str, Path]) -> int:

    iout_output_path = f"{output_path}_iout"
    fout_output_path = f"{output_path}_fout"

    with SpinCursor("Running topup...", end=f"Saved at `{output_path}`"):
        subprocess.run([
            "topup",
            f"--imain={input_path}",
            f"--datain={acqp_path}",
            f"--out={output_path}",
            f"--iout={iout_output_path}",
            f"--fout={fout_output_path}"
        ])

    return 0


def run_eddy(input_path: Union[str, Path],
             brain_mask_path: Union[str, Path],
             index_path: Union[str, Path],
             acqp_path: Union[str, Path],
             bvecs_path: Union[str, Path],
             bvals_path: Union[str, Path],
             topup_path: Union[str, Path],
             output_path: Union[str, Path] = "eddy_unwarped_images",
             json_path: Union[str, Path] = None,
             flm: str = "quadratic",
             fwhm: int = 0, shelled: bool = False) -> int:

    with SpinCursor("Running eddy...", end=f"Saved at `{output_path}`"):
        command = [
            "eddy",
            f"--imain={input_path}",
            f"--mask={brain_mask_path}",
            f"--index={index_path}",
            f"--acqp={acqp_path}",
            f"--bvecs={bvecs_path}",
            f"--bvals={bvals_path}",
            f"--fwhm={fwhm}",
            f"--topup={topup_path}",
            f"--flm={flm}",
            f"--out={output_path}",
            "--estimate_move_by_susceptibility", # Estimate how susceptibility field changes with subject movement
            "--repol" # Detect and replace outlier slices
            # "--mporder=16" # Not implemented for CPU
        ]
        if json_path:
            command.append(f"--json={json_path}",)
        if shelled:
            command.append("--data_is_shelled")
        subprocess.run(command)
    return 0


def process_one_subject(input_path: Union[str, Path],
                        output_path: Union[str, Path],
                        nifti_method: str = "auto",
                        compression: bool = True,
                        reorient: bool = True) -> int:
    """Process DTI data for one subject.

    The steps involved in this pipeline are:
    
    0. Extract data from subject's zip file, if input is a zip file.
    1. convert DICOM files to NIfTI.
    2. locate relevant DTI data and metadata files and saved them separately.
    3. TOPUP - Susceptibility-induced distortions corrections. Also, generate acqparams.txt and b0.nii.gz files from existing data to perform this step.
    4. EDDY - Eddy currents corrections. This step will also generate averaged b0 and brain mask NifTI files from existing data to perform this step.
    5. DTIFIT - fitting diffusion tensors

    Args:
        input_path: path to subject's zip file or folder containing DICOM files.
        output_path: folder location where outputs will be saved.
        nifti_method: select a DICOM to NIfTI conversion method. Choose one of
            the following conversion methods: `auto` (whichever works best for
            each subject), `dicom2nifti` (python package), `dcm2nii` (MRICron),
            and `dcm2niix` (newer version of dcm2nii). [default: `auto`]
        compression: compress .nii to .nii.gz
        reorient: reorient the dicoms according to LAS orientation.

    Returns:
        exit code 0 upon successful execution. 
        Otherwise, throws corresponding error
    """

    input_path, output_path = Path(input_path), Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.debug(f"outputs will be saved at `{output_path}`")

    # * Step 0: Extract data if zip file
    if input_path.is_file():
        if input_path.suffix == ".zip":
            logger.debug("Extracting files...")
            # Create a new folder where files will be extracted
            extract_to = output_path/f"0_extracted"
            extract_to.mkdir(parents=True, exist_ok=True)
            datapath = extract_subject(input_path, extract_to)
            subject_name = datapath.stem

            logger.debug(f"Extracted @ {datapath}")
            logger.debug("done.")
        else:  # If given file is not zip then throw error.
            raise ValueError(
                "Only `.zip` files are supported. Please extract the subject data manually and pass the folder path to `input_path` argument.")
    elif input_path.is_dir():
        datapath = input_path
        subject_name = datapath.stem
    else:  # input should be folder or file. This step catches other exceptions
        _msg = f"Given path `{input_path}` is neither a zip file nor a folder."
        raise ValueError(_msg)

    logger.debug(
        f"Using first folder `{subject_name}` as subject name for further processing.")

    # * Step 1: Convert DICOM images to NIfTI
    logger.debug("Converting DICOM to NIfTI...")
    # Create new folder to store nifti files
    nifti_path = output_path/f"1_nifti/{subject_name}"
    exit_code = convert_dicom_to_nifti(datapath, nifti_path, method=nifti_method,
       compression=compression, reorient=reorient)
    if exit_code != 0: # Stop here if any error
        _msg = "Error in `convert_dicom_to_nifti` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)

    logger.debug(f"Saved @ {nifti_path}")
    logger.debug("done.")

    # * Step 2: locate relevant DTI data and metadata files and saved them separately.
    # create new folder to store intermediate data.
    interm_path = output_path/f"2_interm/{subject_name}"
    interm_path.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Copying DTI data and metadata files to `{interm_path}`.")

    # This function finds DTI data and metadata files such as bval, bvec, and
    # json metadata. This is my project specific step. Check the output files.
    selected_files_dict = locate_data_files(nifti_path, interm_path)

    logger.info(f"Files saved at `{interm_path}`.")
    logger.debug("done.")

    # * Step 3: TOPUP - Susceptibility-induced Distortions Corrections.
    # Create b0 file from the dwidata. Choose a volume without diffusion weighting (e.g. the first volume).
    b0_path = interm_path/"b0.nii.gz"
    exit_code = generate_b0_from_dti(selected_files_dict[".nii.gz"], output_path=b0_path)
    if exit_code != 0: # Stop here if any error
        _msg = "Error in `generate_b0_from_dti` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.info(f"Created b0 file at `{b0_path}`.")

    # Create acquisition parameters file
    acqp_path = interm_path/"acqparams.txt"
    exit_code = generate_acquisition_params(output_path=acqp_path)
    if exit_code != 0: # Stop here if any error
        _msg = "Error in `generate_acquisition_params` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.info(f"Created acquisition parameters file at `{acqp_path}`.")

    # TOPUP
    logger.debug("Running topup...")
    topup_output_path = interm_path/"topup_b0"
    exit_code = run_topup(b0_path, acqp_path, output_path=topup_output_path)
    if exit_code != 0: # Stop here if any error
        _msg = "Error in `run_topup` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.debug("done.")

    # * Step 4: EDDY - Eddy currents corrections.
    # compute the average image of the corrected b0 volumes
    topup_iout_path = topup_output_path.parent/"topup_b0_iout"
    avg_b0_path = interm_path/"hifi_b0"
    exit_code = generate_avg_b0(topup_iout_path, avg_b0_path)
    if exit_code != 0: # Stop here if any error
        _msg = "Error in `generate_avg_b0` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.info(f"Created avg b0 file at `{avg_b0_path}`.")

    # use BET on the averaged b0. create a binary brain mask, with a fraction
    # intensity threshold of 0.2.
    brain_mask_path = interm_path/"hifi_b0_brain"
    exit_code = generate_brain_mask(avg_b0_path, brain_mask_path)
    if exit_code != 0: # Stop here if any error
        _msg = "Error in `generate_brain_mask` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.info(f"Created b0 brain mask file at `{brain_mask_path}`.")

    # Create index.txt file
    index_path = interm_path/"index.txt"
    exit_code = generate_index(selected_files_dict[".nii.gz"], output_path=index_path)
    if exit_code != 0: # Stop here if any error
        _msg = "Error in `generate_index` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.info(f"Created index file at `{index_path}`.")

    # Run eddy
    eddy_output_path = interm_path/"eddy_unwarped_images"
    logger.debug("Running eddy...")
    exit_code = run_eddy(input_path=selected_files_dict[".nii.gz"],
             brain_mask_path=brain_mask_path,
             index_path=index_path,
             acqp_path=acqp_path,
             bvecs_path=selected_files_dict[".bvec"],
             bvals_path=selected_files_dict[".bval"],
             topup_path=topup_output_path,
             output_path=eddy_output_path,
             json_path=None # Multiband info (Getting `SliceTiming` error)
    )
    logger.warning(">> ADD EDDY QC <<")
    if exit_code != 0: # Stop here if any error
        _msg = "Error in `run_eddy` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.debug("done.")

    # * Step 5: DTIFIT - fitting diffusion tensors
    processed_path = output_path/f"3_processed/{subject_name}"
    processed_path.mkdir(parents=True, exist_ok=True)
    fit_output_path = processed_path/"dti"
    logger.debug("Running dtifit...")
    exit_code = run_dtifit(selected_files_dict[".nii.gz"],
               brain_mask_path,
               bvecs_path=selected_files_dict[".bvec"],
               bvals_path=selected_files_dict[".bval"],
               output_path=fit_output_path)
    if exit_code != 0: # Stop here if any error
        _msg = "Error in `run_dtifit` execution :(. Stopped."
        logger.error(_msg)
        raise RuntimeError(_msg)
    logger.debug("done.")

    # Sanity check

    logger.info(f"The output files are saved at `{processed_path}`")


    return 0
