def get_complaint_list_cache_key():
    """
    Generate a cache key for the complaint list.
    """
    return "complaint_list"


def get_complaint_cache_key(complaint_id):
    """
    Generate a cache key for a specific complaint.
    """
    return f"complaint_{complaint_id}"
