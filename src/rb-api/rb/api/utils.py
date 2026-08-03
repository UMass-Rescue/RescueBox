import argparse
from collections.abc import Callable
from typing import Any

from rb.api.models import FloatRangeDescriptor, IntRangeDescriptor


def get_int_range_check_func_arg_parser(
    range: IntRangeDescriptor,
) -> Callable[[Any], int]:
    def check_func(value: Any) -> int:
        try:
            value = int(value)
        except Exception:
            raise argparse.ArgumentTypeError(f"{value} is not a valid integer")
        if value < range.min or value > range.max:
            raise argparse.ArgumentTypeError(
                f"{value} is not in the range [{range.min}, {range.max}]"
            )
        return value

    return check_func


def get_float_range_check_func_arg_parser(
    range: FloatRangeDescriptor,
) -> Callable[[Any], float]:
    def check_func(value: Any) -> float:
        try:
            value = float(value)
        except Exception:
            raise argparse.ArgumentTypeError(f"{value} is not a valid float")
        if value < range.min or value > range.max:
            raise argparse.ArgumentTypeError(
                f"{value} is not in the range [{range.min}, {range.max}]"
            )
        return value

    return check_func


def string_to_dict(s):
    s = s.strip("{}")
    pairs = s.split(",")
    result = {}
    for pair in pairs:
        key, value = pair.split(":")
        if isinstance(value.strip(), int):
            result[key.strip().replace("'", "")] = int(value.strip())
        elif isinstance(value.strip(), float):
            result[key.strip().replace("'", "")] = float(value.strip())
        else:
            result[key.strip().replace("'", "")] = value.strip()
        # logger.info(f'string_to_dict {key} {value}')
    return result
