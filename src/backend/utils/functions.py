def flatten_lists(nested_list: list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_lists(item))  # Recursively flatten the sublist
        else:
            flat_list.append(item)  # Add the non-list item directly to the flat list
    return flat_list
