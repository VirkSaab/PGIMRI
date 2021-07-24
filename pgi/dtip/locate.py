import os
import re
import shutil
from typing import Union
from pathlib import Path
import nibabel as nib
from pgi.utils import get_logger, SpinCursor
from pgi.config import *

logger = get_logger(__name__)


def locate_data_files(src_folder: Union[str, Path],
                      dst_folder: Union[str, Path],
                      file_names: list = ["dti_medium_iso", "dtimediumiso"],
                      exclude: list = ["reg", "fareg"],
                      extensions: list = ['.bval', '.bvec', '.json']) -> dict:
    """Locate main DTI data file and related metadata files.

    Args:
        > src_folder -- folder path where to look for files.
        > dst_folder -- copy located files (if any) to `dst_folder` 
        and renamed as `dtidata.<extension>.`
        > file_names -- name(s) of file(s) to search for. By default, main file
        has names given in `file_names`. For example, main files will have a name 
        `<...> DTI medium iso <...>.nii.gz` or uncompressed .nii with 17 volumes.
        > exclude -- Suppose you want a file named `DTImediumiso` but not
        `RegDTImediumiso`. then add `reg` in the `exclude` list.
        > extensions -- Other than main DTI data, metadata files such as
        `.bval` and `.bvec` files might be required for further processing.
        Usually, these metadata files will have same name with different extension.
        
    Returns:
        dict object containing relevant files with full path.
    """

    src_folder, dst_folder = Path(src_folder), Path(dst_folder)

    extensions += ['.nii', '.nii.gz'] # DTI data files format

    # Get all filenames in `src_folder`
    all_filenames = os.listdir(src_folder)
    # _extensions = '|'.join([f"{ext}$" for ext in extensions])

    relevant_files = []
    # First match filenames
    for filename in all_filenames:
        for name in file_names:
            if name in filename.lower():
                _flag = False
                # Remove any file matching exclude list
                for exc in exclude:
                    if exc in filename.lower():
                        _flag = True
                        break
                if _flag == False:
                    relevant_files.append(filename)
    
    logger.debug(f"Found {len(relevant_files)} relevant files.")
    
    # group according to extensions
    files_dict = {ext:[] for ext in extensions}
    for ext in extensions:
        for filename in relevant_files:
            # Keep files whose extension match with `extensions`
            found = re.search(fr"{ext}$", filename.lower())
            if found:
                files_dict[ext].append(filename)

    # Filter DTI data and pick most relevant file
    logger.warning("TWO KEYS? .nii and .nii.gz, how to merge?")
    for idx, f in enumerate(files_dict[".nii.gz"]):
        img = nib.load(src_folder/f)
        z, y, z, t = img.shape
        # Check if file has desired diffusion dimesion.
        if t != N_DTI_VOLUMES: # Remove DTI files if volumes are more or less.
            files_dict[".nii.gz"].pop(idx)

    # Find the most common series left in all files
    series_dict = {}
    for k in files_dict.keys():
        for f in files_dict[k]:
            # This regex search for series numbers like s<series>.nii or s<series>a...
            series = re.search(r"s[0-9]+(\.|a)", f.lower())
            _from, _to = series.span()
            # +1 and -1 remove `s` and (`a` or `.`)
            series = f[_from+1:_to-1]

            # Check if series is persent as a key. Else create new
            if series not in series_dict.keys():
                series_dict[series] = []
                series_dict[series].append(f)
            else:
                series_dict[series].append(f)

    # Get series which has left maximum number of files
    best_series = max(series_dict, key=lambda k: len(series_dict[k]))
    if len(series_dict) > 1:
        logger.info(f"Selecting series number {series} out of {list(series_dict.keys())} series.")
        _msg = f"Files with series {best_series} will be used for further processing."
        logger.info(_msg)
    else:
        logger.debug(f"Only 1 series left. Series number is {best_series}.")

    # Copy the filtered files to `dst_folder`
    dst_folder.mkdir(parents=True, exist_ok=True)

    #TODO RESOLVE THESE
    logger.warning("What if all the mentioned files are not in best_series?")
    logger.warning("How to handle multiple file in one series?")
    
    logger.debug(f"Copying files to {dst_folder}")
    total_files_left = len(series_dict[best_series])
    for i, filename in enumerate(series_dict[best_series], start=1):
        filepath = os.path.join(src_folder, filename)
        savepath = dst_folder/filename
        shutil.copy(filepath, savepath)
        logger.debug(f"[{i}/{total_files_left}] Copied `{filepath}` to `{savepath}`.")
    
    logger.info(f"Total files obtained = {total_files_left}")
    logger.debug("ALL DONE!")
    
    