def get_league_cache_key(pk):
    """
    Generate a cache key for a league instance.
    """
    return f"league_{pk}"


def get_league_list_cache_key():
    """
    Generate a cache key for the list of leagues.
    """
    return "leagues_list"


def get_league_group_cache_key(pk):
    """
    Generate a cache key for a league group instance.
    """
    return f"league_group_{pk}"


def get_league_group_list_cache_key(league_id=None):
    """
    Generate a cache key for the list of league groups.
    """
    if league_id:
        print(f"Generating cache key for league groups with league_id: {league_id}")
        return f"league_groups_list_{league_id}"
    print("Generating cache key for all league groups")
    return "league_groups_list"


def get_league_group_participant_list_cache_key(league_group_id):
    """
    Generate a cache key for the list of league group participants.
    """
    return f"league_group_participants_list_{league_group_id}"
