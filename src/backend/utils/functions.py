from datetime import date
from typing import Any


def flatten_lists(nested_list: list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_lists(item))  # Recursively flatten the sublist
        else:
            flat_list.append(item)  # Add the non-list item directly to the flat list
    return flat_list


def flatten_dict(d, parent_key="", sep="."):
    """
    Flattens an arbitrarily nested dictionary of dictionaries into a dictionary
    with one level of nesting, where the outermost keys are merged into one
    "."-separated key and the inner dictionaries are preserved as values.

    :param d: Dictionary to flatten
    :param parent_key: The base key for the current recursion level
    :param sep: The separator for joining nested keys
    :return: Flattened dictionary with one level of nesting
    """
    flattened = {}

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            # Preserve one level of nesting, do not flatten the nested dictionary
            flattened[new_key] = v
        else:
            flattened[new_key] = v

    return flattened


def is_quant(item: Any) -> bool:
    """Determines if item is a quantitative value. Need to update."""
    if isinstance(item, (int, float, date)):
        return True
    elif type(item) is str:
        return not any(char.isalpha() for char in item)
    else:
        raise ValueError("Incompatible meta property value")
