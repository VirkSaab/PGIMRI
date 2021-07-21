import dicom2nifti
import zipfile
from typing import Union
from pathlib import Path
from pgi.utils import get_logger, SpinCursor2


logger = get_logger(__name__, to_file=f"dti_processing.log")


def process_one_subject(subject_path: Union[str, Path],
                        output_folder: Union[str, Path], 
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
    nifti_path = output_folder/"1_nifti"
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
    with SpinCursor2("dicom2nifti..."):
        dicom2nifti.convert_directory(
            dicom_directory=subject_path, output_folder=nifti_path,
            compression=compression, reorient=reorient
        )
    
    logger.info(f"done.")
