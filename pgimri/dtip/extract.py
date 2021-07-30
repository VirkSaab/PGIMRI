import os
import zipfile
from pathlib import Path
from typing import Union

from pgimri.utils import get_logger, SpinCursor
from pgimri.config import *

logger = get_logger(__name__)


def extract_subject(src_file:Union[str, Path], dst_folder:Union[str, Path]='.') -> str:
    """Extract zip file of a subject

    Args:
        src_file: subject zip file path.
        dst_folder: folder where extract files will be saved. [default: same as `src_file`]

    Returns:
        extracted folder path.

    Example:

        .. code-block:: python
        
            input_path = "path/to/example_subject.zip"
            output_path = "example_outputs"
            extract_subject(input_path, output_path)

    """

    src_file, dst_folder = Path(src_file), Path(dst_folder)

    # Check if the `src_file` path is a file
    if not src_file.is_file():
        _msg = f"src_file `{src_file}` if not a zip file."
        logger.error(_msg)
        raise ValueError(_msg)
    
    # Extract files at `dst_folder`
    logger.debug(f"Extracting files to `{dst_folder}`...")
    with SpinCursor("Extracting..."):
        with zipfile.ZipFile(src_file, 'r') as zip_ref:
            zip_ref.extractall(dst_folder)
            dst_folder.mkdir(parents=True, exist_ok=True)
            sub_new_name = get_parent_folder(zip_ref.namelist()[0])
            dst_folder = dst_folder/sub_new_name
    logger.debug(f"done.")
    return dst_folder


def get_parent_folder(path:Union[str, Path]) -> str:
    """To get parent folder if subject files are extracted from a zip file."""

    path = str(path)
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