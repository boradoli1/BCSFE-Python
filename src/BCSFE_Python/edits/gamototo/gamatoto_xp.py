"""Handler for editing gamatoto xp"""
from typing import Any

from ... import helper, user_input_handler, item, game_data_getter

def get_boundaries(is_jp: bool) -> list[int]:
    """Get the xp requirements for each level"""

    boundaries = game_data_getter.get_file_latest(
        "DataLocal", "GamatotoExpedition.csv", is_jp
    ).decode("utf-8").splitlines()
    previous = 0
    xp_requirements: list[int] = []
    previous = 0
    for line in boundaries:
        requirement = int(line.split(",")[0])
        if previous >= requirement:
            break
        xp_requirements.append(requirement)
        previous = requirement
    return xp_requirements


def get_level_from_xp(gamatoto_xp: int, is_jp: bool) -> dict[str, Any]:
    """Get the level from the xp amount"""

    xp_requirements = get_boundaries(is_jp)
    level = 1
    for requirement in xp_requirements:
        if gamatoto_xp >= requirement:
            level += 1
    return {
        "level": level,
        "max_level": len(xp_requirements),
        "max_xp": xp_requirements[-2],
    }


def get_xp_from_level(level: int, is_jp: bool) -> int:
    """Get the xp amount from the level"""

    xp_requirements = get_boundaries(is_jp)
    if level <= 1:
        gamatoto_xp = 0
    else:
        gamatoto_xp = xp_requirements[level - 2]
    return gamatoto_xp


def edit_gamatoto_xp(save_stats: dict[str, Any]) -> dict[str, Any]:
    """Handler for gamatoto xp"""

    gamatoto_xp = save_stats["gamatoto_xp"]

    data = get_level_from_xp(gamatoto_xp["Value"], helper.check_data_is_jp(save_stats))
    level = data["level"]

    helper.colored_text(f"Gamatoto xp: &{gamatoto_xp['Value']}&\nLevel: &{level}&")
    raw = user_input_handler.colored_input(
        "Do you want to edit raw xp(&1&) or the level(&2&)?:"
    ) == "1"

    if raw:
        gam_xp = item.Item(
            name="Gamatoto XP",
            value=gamatoto_xp["Value"],
            max_value=None,
            edit_name="value",
        )
        gam_xp.edit()
        gamatoto_xp["Value"] = gam_xp.value
    else:
        gam_level = item.Item(
            name="Gamatoto Level",
            value=level,
            max_value=data["max_level"],
            edit_name="level",
        )
        gam_level.edit()
        gamatoto_xp["Value"] = get_xp_from_level(int(gam_level.value), helper.check_data_is_jp(save_stats))

    save_stats["gamatoto_xp"] = gamatoto_xp
    return save_stats
