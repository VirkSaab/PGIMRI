
from pathlib import Path
from typing import Union


def extract_one_subject(src:Union[str, Path], dst:Union[str, Path]='.'):
    """Extract zip file of a subject

    Args:
    > src -- subject zip file path.
    > dst -- folder where extract files will be saved. [default: same as `src`]
    """

    src = Path(src)

    if src.is_file():
        pass