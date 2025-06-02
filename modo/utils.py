import re
from collections import defaultdict


def parse_nested_form_data(data, files=None):
    """
    Convert flat form keys like 'questions[0][title]' into nested Python structures.
    Supports both data (request.data) and files (request.FILES).
    """
    combined = dict(data)
    if files:
        combined.update(files)

    result = {}

    for flat_key, value in combined.items():
        keys = re.findall(
            r"\w+", flat_key
        )  # e.g. 'questions[0][title]' → ['questions', '0', 'title']
        current = result

        for i, key in enumerate(keys):
            is_last = i == len(keys) - 1

            # Convert numeric keys to int for lists
            if key.isdigit():
                key = int(key)

            if is_last:
                if isinstance(current, list):
                    _ensure_list_index(current, key)
                    current[key] = value
                else:
                    current[key] = value
            else:
                next_key = keys[i + 1]
                is_next_list = next_key.isdigit()

                if isinstance(current, list):
                    _ensure_list_index(current, key)
                    if not isinstance(current[key], (dict, list)):
                        current[key] = [] if is_next_list else {}
                    current = current[key]
                else:
                    if key not in current:
                        current[key] = [] if is_next_list else {}
                    current = current[key]

    return result


def _ensure_list_index(lst, index):
    """Ensure the list is big enough to access index."""
    while len(lst) <= index:
        lst.append({})


def clean_parsed_data(data):
    """
    Recursively clean parsed form data:
    - Extract single values from 1-element lists
    - Convert 'true'/'false' strings to booleans
    - Force specific fields (like 'questions') to be lists
    - Strip whitespace
    """
    list_fields = {
        "questions",
        "answer_options",
        "contents",
    }  # ← Add your multi-item fields here

    if isinstance(data, list):
        return [clean_parsed_data(item) for item in data]

    elif isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, list) and len(value) == 1:
                value = value[0]

            # Convert string booleans
            if isinstance(value, str):
                value = value.strip()
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False

            # Wrap specific keys into lists if needed
            if key in list_fields:
                if isinstance(value, dict):
                    value = [value]  # Wrap single dict into list
                elif not isinstance(value, list):
                    value = [value]  # Fallback for any scalar value

            cleaned[key] = clean_parsed_data(value)

        return cleaned

    else:
        return data
