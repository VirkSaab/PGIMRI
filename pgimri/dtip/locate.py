import os
import re
import shutil
from typing import Union
from pathlib import Path
import nibabel as nib
from pgimri.utils import get_logger
from pgimri.config import *


__all__ = ["locate_data_files"]

logger = get_logger(__name__)


def locate_data_files(input_path: Union[str, Path],
                      output_path: Union[str, Path],
                      file_names: list = DTI_FILENAMES_LIST,
                      exclude: list = EXCLUDE_LIST,
                      extensions: list = META_EXTENSIONS) -> dict:
    """Locate main DTI data file and related metadata files.

    Args:
        input_path: folder path where to look for files.
        output_path: copy located files (if any) to `output_path` and renamed as `dtidata.<extension>.`
        file_names: name(s) of file(s) to search for. By default, main file has names given in `file_names`. For example, main files will have a name `<...> DTI medium iso <...>.nii.gz` or uncompressed .nii with 17 volumes.
        exclude: Suppose you want a file named `DTImediumiso` but not `RegDTImediumiso`. then add `reg` in the `exclude` list.
        extensions: Other than main DTI data, metadata files such as `.bval` and `.bvec` files might be required for further processing. Usually, these metadata files will have same name with different extension.
        
    Returns:
        `dict` with selected files paths where key is file extension and value is the file path.
    """

    input_path, output_path = Path(input_path), Path(output_path)

    extensions.append('.nii.gz') # DTI data files format

    # Get all filenames in `input_path`
    all_filenames = os.listdir(input_path)
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
        img = nib.load(input_path/f)
        if len(img.shape) != 4:
            files_dict[".nii.gz"].pop(idx)
            continue
        # print("IMG SHAPE =", img.shape, f)
        x, y, z, t = img.shape
        # Check if file has desired diffusion dimesion.
        if t != N_DTI_VOLUMES: # Remove DTI files if volumes are more or less.
            files_dict[".nii.gz"].pop(idx)

    # Find the most common series left in all files
    series_dict = {}
    for k in files_dict.keys():
        for f in files_dict[k]:
            # This regex search for series numbers like s<series>.nii
            # or s<series>a...
            series = re.search(r"s[0-9]+(\.|a)", f.lower())
            _from, _to = series.span()
            # +1 and -1 remove `s` and (`a` or `.`)
            series = f[_from+1:_to-1]

            # Check if series is persent as a key. Else create new
            if series not in series_dict.keys():
                series_dict[series] = [f]
            else:
                series_dict[series].append(f)

    # Get series which has left maximum number of files
    if not series_dict:
        _msg = f"No DTI specific files found related to {DTI_FILENAMES_LIST}."
        _msg += f" Please check manually."
        raise RuntimeError(_msg)
    best_series = max(series_dict, key=lambda k: len(series_dict[k]))
    if len(series_dict) > 1:
        logger.info(f"Selecting series number {series} out of {list(series_dict.keys())} series.")
        _msg = f"Files with series {best_series} will be used for further processing."
        logger.info(_msg)
    else:
        logger.debug(f"Only 1 series left. Series number is {best_series}.")

    # Copy the filtered files to `output_path`
    output_path.mkdir(parents=True, exist_ok=True)

    #TODO RESOLVE THESE
    logger.warning("What if all the mentioned files are not in best_series?")
    logger.warning("How to handle multiple file in one series?")
    
    # Choose one .nii.gz file if there are more than one
    selected_files = [
        file for file in series_dict[best_series]
        if file.endswith(".nii.gz") and file.startswith("x")
    ]

    # if no `x` type data file found then choose any one .nii.gz file.
    # print("BEFORE =", selected_files)
    if len(selected_files) == 0:
        selected_files = [
            file for file in series_dict[best_series]
            if file.endswith(".nii.gz")
        ]
    # print("BEFORE1 =", selected_files)
    if len(selected_files) > 1:
        selected_files = [selected_files[0]]
    elif len(selected_files) == 0:
        raise ValueError("No matching DTI volume found.")
    
    # print("AFTER =", selected_files)
    # Add rest of the metadata files
    for file in series_dict[best_series]:
            if not file.endswith(".nii.gz"):
                selected_files.append(file)

    logger.debug(f"Finally {len(selected_files)} files are selected.")
    logger.debug(f"Copying files to {output_path}")
    total_files_left, ret_dict = len(selected_files), {}
    for i, filename in enumerate(selected_files, start=1):
        # Copy Paste selected files to new location
        filepath = os.path.join(input_path, filename)
        savepath = output_path/filename
        shutil.copy(filepath, savepath)
        logger.debug(f"[{i}/{total_files_left}] Copied `{filepath}` to `{savepath}`.")

        # add the selected filepath to return dict
        if filename.endswith(".nii.gz"):
            ret_dict[".nii.gz"] = savepath
        else:
            ret_dict[savepath.suffix] = savepath
    
    logger.info(f"Total files obtained = {total_files_left}")
    logger.debug("ALL DONE!")
    
    return ret_dict
