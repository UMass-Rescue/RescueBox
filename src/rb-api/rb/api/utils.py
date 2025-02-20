import os, tempfile
from typing import Any, Callable, Union, assert_never
import argparse
from rb.api.models import FloatRangeDescriptor, InputType, IntRangeDescriptor, NewFileInputType


# https://stackoverflow.com/a/34102855/10505724

ERROR_INVALID_NAME = 123


def get_path_validator_func(input_type: Union[InputType, NewFileInputType]):
    match input_type:
        case InputType.FILE | InputType.DIRECTORY | InputType.BATCHFILE | InputType.BATCHDIRECTORY | NewFileInputType():
            return is_pathname_valid_arg_parser
        case InputType.TEXT | InputType.BATCHTEXT | InputType.TEXTAREA:
            return str
        case _:  # pragma: no cover
            assert_never(input_type)
            
def is_pathname_valid(pathname: str) -> bool:
    """
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    """
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        if os.path.isfile(pathname) or os.path.isdir(pathname):
            return True
        else:
            return False
    except TypeError:
        return False



def is_path_sibling_creatable(pathname: str) -> bool:
    """
    `True` if the current user has sufficient permissions to create **siblings**
    (i.e., arbitrary files in the parent directory) of the passed pathname;
    `False` otherwise.
    """
    # Parent directory of the passed path. If empty, we substitute the current
    # working directory (CWD) instead.
    dirname = os.path.dirname(pathname) or os.getcwd()

    try:
        # For safety, explicitly close and hence delete this temporary file
        # immediately after creating it in the passed path's parent directory.
        with tempfile.TemporaryFile(dir=dirname):
            pass
        return True
    # While the exact type of exception raised by the above function depends on
    # the current version of the Python interpreter, all such types subclass the
    # following exception superclass.
    except EnvironmentError:
        return False


def is_path_exists_or_creatable_portable(pathname: str) -> bool:
    """
    `True` if the passed pathname is a valid pathname on the current OS _and_
    either currently exists or is hypothetically creatable in a cross-platform
    manner optimized for POSIX-unfriendly filesystems; `False` otherwise.

    This function is guaranteed to _never_ raise exceptions.
    """
    try:
        # To prevent "os" module calls from raising undesirable exceptions on
        # invalid pathnames, is_pathname_valid() is explicitly called first.
        return is_pathname_valid(pathname) and (
            os.path.exists(pathname) or is_path_sibling_creatable(pathname)
        )
    # Report failure on non-fatal filesystem complaints (e.g., connection
    # timeouts, permissions issues) implying this path to be inaccessible. All
    # other exceptions are unrelated fatal issues and should not be caught here.
    except OSError:
        return False

def is_path_exists_or_creatable_portable_arg_parser(path: str) -> str:
    if is_path_exists_or_creatable_portable(path):
        return path
    else:
        raise ValueError(f"{path} is not a valid path")

def is_pathname_valid_arg_parser(pathname: str) -> str:
    if is_pathname_valid(pathname):
        return pathname
    else:
        raise ValueError(f"'{pathname}' is not a valid pathname")

def get_int_range_check_func_arg_parser(range: IntRangeDescriptor) -> Callable[[Any], int]:
    def check_func(value: Any) -> int:
        try:
            value = int(value)
        except:
            raise argparse.ArgumentTypeError(f"{value} is not a valid integer")
        if value < range.min or value > range.max:
            raise argparse.ArgumentTypeError(f"{value} is not in the range [{range.min}, {range.max}]")
        return value
    return check_func

def get_float_range_check_func_arg_parser(range: FloatRangeDescriptor) -> Callable[[Any], float]:
    def check_func(value: Any) -> float:
        try:
            value = float(value)
        except:
            raise argparse.ArgumentTypeError(f"{value} is not a valid float")
        if value < range.min or value > range.max:
            raise argparse.ArgumentTypeError(f"{value} is not in the range [{range.min}, {range.max}]")
        return value
    return check_func

def string_to_dict(s):
    s = s.strip('{}')
    pairs = s.split(',')
    result = {}
    for pair in pairs:
        key, value = pair.split(':')
        if isinstance(value.strip(), int):
           result[key.strip().replace("'",'')] = int(value.strip())
        elif isinstance(value.strip(), float):
           result[key.strip().replace("'",'')] = float(value.strip())
        else:
           result[key.strip().replace("'",'')] =value.strip()
        #logger.info(f'string_to_dict {key} {value}')
    return result