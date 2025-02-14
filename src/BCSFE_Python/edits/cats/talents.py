"""Handler to edit cat talents"""
from typing import Any

from ... import helper, item, csv_handler, game_data_getter
from . import cat_id_selector


def get_talent_data(save_stats: dict[str, Any]) -> dict[Any, Any]:
    """Get talent data for all cats"""

    talent_data_raw = helper.parse_int_list_list(
        csv_handler.parse_csv(
            game_data_getter.get_file_latest(
                "DataLocal", "SkillAcquisition.csv", helper.check_data_is_jp(save_stats)
            ).decode("utf-8"),
        )
    )
    talent_names = csv_handler.parse_csv(
        game_data_getter.get_file_latest(
            "resLocal", "SkillDescriptions.csv", helper.check_data_is_jp(save_stats)
        ).decode("utf-8"),
        helper.get_text_splitter(helper.check_data_is_jp(save_stats)),
    )
    columns = helper.int_to_str_ls(talent_data_raw[0])
    new_talent_data: dict[Any, Any] = {}
    for j in range(1, len(talent_data_raw)):
        data = talent_data_raw[j]
        cat_id: int = int(data[0])
        new_talent_data[cat_id] = {}

        for data_i, column in zip(data, columns):
            new_talent_data = replace_name(
                cat_id=cat_id,
                column=column,
                data=data_i,
                talent_names=talent_names,
                new_data=new_talent_data,
            )
    return new_talent_data


def replace_name(
    cat_id: int,
    column: str,
    data: int,
    talent_names: list[list[str]],
    new_data: dict[Any, Any],
) -> dict[str, Any]:
    """Replace the text ids with the corresponding names"""

    new_data[cat_id][column] = data
    if (
        "textID" in column or "tFxtID_F" in column
    ):  # ponos made a typo, should be textID_F
        new_data[cat_id][column] = talent_names[data][1]
        stop_at = "<br>"
        if stop_at in new_data[cat_id][column]:
            index = new_data[cat_id][column].index(stop_at)
            new_data[cat_id][column] = new_data[cat_id][column][:index]
    return new_data


def find_order(
    cat_talents: list[dict[str, Any]], cat_talent_data: dict[str, Any]
) -> list[str]:
    """Find what talent slot each letter corresponds to"""

    letters = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
    ]
    letter_order: list[str] = []

    for i, talent in enumerate(cat_talents):
        if i == 0:
            continue
        talent_id = talent["id"]
        for letter in letters:
            ability_id = int(cat_talent_data[f"abilityID_{letter}"])
            if ability_id == talent_id:
                letter_order.append(letter)
    return letter_order


def get_cat_talents(
    cat_talents: list[dict[str, Any]], cat_talent_data: dict[str, Any]
) -> dict[Any, Any]:
    """Get the name and max value of each talent for a specific cat"""

    data: dict[Any, Any] = {}
    letter_order = find_order(cat_talents, cat_talent_data)
    for i in range(len(cat_talents) - 1):
        cat_data = {}
        if letter_order[i] == "F":
            text_id_str = "tFxtID_F"  # ponos made a typo, should be textID_F
        else:
            text_id_str = f"textID_{letter_order[i]}"
        cat_data["name"] = cat_talent_data[text_id_str].strip("\n")
        cat_data["max"] = int(cat_talent_data[f"MAXLv_{letter_order[i]}"])
        if cat_data["max"] == 0:
            cat_data["max"] = 1
        data[i] = cat_data
    return data


def get_talent_levels(
    talent_data: dict[int, Any], talents: dict[int, Any], cat_id: int
) -> list[int]:
    """Get the level of each talent for a specific cat"""

    cat_talent_data = talent_data[cat_id]
    cat_talents = talents[cat_id]
    cat_talent_data_formatted = get_cat_talents(cat_talents, cat_talent_data)
    cat_talents_levels: list[int] = []
    for talent_formatted in cat_talent_data_formatted.values():
        max_val = talent_formatted["max"]
        cat_talents_levels.append(max_val)
    return cat_talents_levels


def max_all_talents(save_stats: dict[str, Any]):
    """Max all talents for all cats"""
    talents = save_stats["talents"]

    ids = cat_id_selector.select_cats(save_stats)

    talent_data = get_talent_data(save_stats)
    cat_talents_levels: list[int] = []
    for cat_id in ids:
        if cat_id not in talents or cat_id not in talent_data:
            continue
        cat_talents = talents[cat_id]
        cat_talents_levels = get_talent_levels(talent_data, talents, cat_id)
        for i, cat_talent_level in enumerate(cat_talents_levels):
            cat_talents[i + 1]["level"] = cat_talent_level
        save_stats["talents"] = talents

    print("Successfully set talents")
    return save_stats


def edit_talents_individual(save_stats: dict[str, Any]) -> dict[str, Any]:
    """Handler for editing talents"""

    talents = save_stats["talents"]
    ids = cat_id_selector.select_cats(save_stats)

    talent_data = get_talent_data(save_stats)
    cat_talents_levels: list[int] = []
    for cat_id in ids:
        if cat_id not in talents or cat_id not in talent_data:
            # don't spam the user with messages if they selected alot of ids at once
            if len(ids) < 20:
                helper.colored_text(f"Error cat &{cat_id}& does not have any talents", helper.RED, helper.WHITE)
            continue
        cat_talent_data = talent_data[cat_id]
        cat_talents = talents[cat_id]
        cat_talent_data_formatted = get_cat_talents(cat_talents, cat_talent_data)
        names: list[str] = []
        maxes: list[int] = []
        for talent_index, cat_talent_formatted in cat_talent_data_formatted.items():
            names.append(cat_talent_formatted["name"])
            cat_talents_levels.append(cat_talents[talent_index + 1]["level"])
            maxes.append(cat_talent_formatted["max"])
        helper.colored_text(f"Cat &{cat_id}& is slected:")
        cat_talents_levels_g = item.create_item_group(
            names=names,
            values=cat_talents_levels,
            maxes=maxes,
            edit_name="talents",
            group_name="Talents",
        )
        cat_talents_levels_g.edit()
        cat_talents_levels = helper.parse_int_list(cat_talents_levels_g.values, 0)
        for i, cat_talent_level in enumerate(cat_talents_levels):
            cat_talents[i + 1]["level"] = cat_talent_level
        save_stats["talents"] = talents

    print("Successfully set talents")
    return save_stats
