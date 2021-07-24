import os
import shutil
import dicom2nifti
import zipfile
import subprocess
from typing import Union
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

    # Step 0: Extract files if given subject is a zip file.
    if subject_path.is_file():
        extract_to_path = output_folder/"0_extracted_files"
        extract_to_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(subject_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to_path)
            sub_new_name = get_parent_folder(zip_ref.namelist()[0])
            subject_path = extract_to_path/sub_new_name
            logger.info(f"files extracted at `{subject_path}`")

        logger.info(f"done.")

    #* Step 1: Convert DICOM images to NIfTI format
    logger.debug("[STEP 1 - START] DICOM to NIfTI conversion")
    if nifti_method == "dcm2niix":
        step1_exit_code, nifti_dirpath = dicom_to_nifti_cli(
            subject_path, output_folder, compression)
    elif nifti_method == "dicom2nifti":
        step1_exit_code, nifti_dirpath = dicom_to_nifti_py(
            subject_path, output_folder, compression, reorient)
    else:
        _msg = "Only 2 methods are supported. `dcm2niix` and `dicom2nifti`"
        raise NotImplementedError(_msg)

    if step1_exit_code == 0:
        logger.debug("<< [STEP 1 - END] >>")
    else:
        return 1

    #* Step 2: Some small tasks like file renaming, generating brain mask
    logger.debug("[STEP 2 - START] Get relevant data files.")
    
    # Save relevant data files like DTI nifti data, json, brain_mask etc.
    # to new folder for further processing
    interm_dirpath = (output_folder/"2_interm_data")/sub_new_name.replace(" ", "_")
    interm_dirpath.mkdir(parents=True, exist_ok=True)

    # Get fullpaths of data files
    nifti_filepath, json_filepath = locate_dti_data_file(nifti_dirpath)
    if nifti_filepath:
        logger.debug(f"Fount data file at `{nifti_filepath}`")
    else:
        logger.error("DTI data file not found :(")
    if json_filepath:
        logger.debug(f"Found json metadata at `{json_filepath}`")
    else:
        logger.info(f"metadata json file not found related to DTI data.")

    logger.info(f"Copying DTI data files to `{interm_dirpath}`")
    shutil.copy(nifti_filepath, interm_dirpath/"dtidata.nii.gz")
    shutil.copy(json_filepath, interm_dirpath/"dtidata.json")
    logger.info("done!")
    logger.debug("<< [STEP 2 - END] >>")


    # Step 2: TOPUP - Susceptibility-induced Distortions Correction
    # logger.debug("[STEP 2] TOPUP is not implemented yet.")

    # # Step 3: EDDY - Eddy Currents Correction
    # logger.debug("[STEP 3 - START] eddy current correction")
    # # eddy_currents_correction()
    # logger.debug("<< [STEP 3 - END] >>")

    # # Step 4: DTIFIT - fitting diffusion tensors
    # logger.debug("[STEP 4 - START] Fit diffusion tensors")
    # logger.debug("<< [STEP 4 - END] >>")
    
    

def get_parent_folder(path):
    """To get parent folder if subject files are extracted from a zip file."""
    out = path
    max_depth, counter = 50, 0
    while True:
        out = list(os.path.split(out))
        name = out.pop(-1)
        out = out[0]
        if len(out) == 0:
            break
        if counter >= max_depth:
            _msg = f"[Step 0 Error] max search depth reached!"
            _msg += " Cannot figure out root folder :("
            logger.error(_msg)
            raise Exception(_msg)        
    return name
    
def dicom_to_nifti_py(subject_path: Union[str, Path],
                      output_folder: Union[str, Path],
                      compression: bool = True,
                      reorient: bool = True) -> None:
    """Convert DICOM to NIfTI files using dicom2nifti Python package.

    Args:
        > subject_path -- Path to subject folder or zip file.
        > output_folder -- Path to output save location.
        > compression -- compress .nii file to .nii.gz.
        > reorient -- reorient the dicoms according to LAS orientation.
    """

    nifti_path = output_folder/f"1_nifti/{subject_path.stem.replace(' ', '_')}"
    nifti_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Converting DICOM to NIfTI...")

    with SpinCursor("dicom2nifti..."):
        dicom2nifti.convert_directory(
            dicom_directory=subject_path, output_folder=nifti_path,
            compression=compression, reorient=reorient
        )

    logger.info(f"done.")
    return 0, nifti_path  # return 0 means successful execution


def dicom_to_nifti_cli(subject_path: Union[str, Path],
                       output_folder: Union[str, Path],
                       compression: bool = True):
    """Convert DICOM to NIfTI files using dcm2niix command.

    Args:
        > subject_path -- Path to subject folder or zip file.
        > output_folder -- Path to output save location.
        > compression -- compress .nii file to .nii.gz.
    """
    nifti_path = output_folder/f"1_nifti/{subject_path.stem.replace(' ', '_')}"
    nifti_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Converting DICOM to NIfTI...")

    command = ["dcm2niix"]

    if compression:
        command += ['-z', 'y']

    command += ['-p', 'y', '-o', nifti_path, subject_path]

    try:
        subprocess.run(command) # Run dcm2nii command
        return 0, nifti_path

    except FileNotFoundError:
        _msg = "[dcm2niix error] Make sure `dcm2niix` is installed. If not,"
        _msg += "Try `sudo apt install dcm2niix`"
        logger.error(_msg)
        return 1, nifti_path

def locate_dti_data_file(subject_path:Union[str, Path], return_fullpath:bool=True):
    """Get ITC relevant DTI data files"""

    subject_path = Path(subject_path)
    
    # Look for DTI nifti and related json file
    files_list, nifti_file, json_file = [], None, None
    for filename in os.listdir(subject_path):
        if 'dti_medium_iso' in filename.lower():
            files_list.append(filename)

    if (len(files_list) == 1):
        filename, file_ext = os.path.splitext(files_list[0])
        if file_ext == '.gz':
            if os.path.splitext(filename)[-1] == '.nii':
                nifti_file = files_list[0]
            else:
                raise FileNotFoundError("Could not locate NIfTI file.")
        elif file_ext == '.nii':
            nifti_file = files_list[0]
        else:
            raise FileNotFoundError("Could not locate NIfTI file.")
            
    if (len(files_list) == 2):
        file_ext = os.path.splitext(files_list[0])[-1]
        if (file_ext == '.gz') or (file_ext == '.nii'):
            next_file_must_be = 'json'
            nifti_file = files_list[0]
        elif file_ext == '.json':
            json_file = files_list[0]
            next_file_must_be = 'data'
        else:
            raise ValueError("File mismatch")
        
        if (next_file_must_be == "json") and \
            (os.path.splitext(files_list[1])[-1]) == ".json":
            json_file = files_list[1]
        elif (next_file_must_be == "data") and \
            (os.path.splitext(files_list[1])[-1]) in ['.gz', '.nii']:
            nifti_file = files_list[1]
    
    if len(files_list) > 2:
        _msg = "Multiple DTI files exists. Not supported yet."
        logger.warning(_msg)
        raise NotImplementedError(_msg)

    if (nifti_file == None) and (json_file == None):
        raise FileNotFoundError("Could not locate NIfTI file.")

    # return full path to files
    if return_fullpath:
        nifti_file = subject_path/nifti_file
        json_file = subject_path/json_file

    return nifti_file, json_file


            

def get_brain_mask(subject_path):
    pass

def eddy_currents_correction():
    pass
