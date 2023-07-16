"""This module contains functions that return colors based on the delay."""

HEX_TO_CSS = {
    "FFC72C": "filter: invert(66%) sepia(78%) saturate(450%) hue-rotate(351deg) brightness(108%) contrast(105%);",
    "7C878E": "filter: invert(57%) sepia(2%) saturate(1547%) hue-rotate(160deg) brightness(91%) contrast(103%);",
    "003DA5": "filter: invert(13%) sepia(61%) saturate(5083%) hue-rotate(215deg) brightness(96%) contrast(101%);",
    "008EAA": "filter: invert(40%) sepia(82%) saturate(2802%) hue-rotate(163deg) brightness(88%) contrast(101%);",
    "80276C": "filter: invert(20%) sepia(29%) saturate(3661%) hue-rotate(283deg) brightness(92%) contrast(93%);",
    "006595": "filter: invert(21%) sepia(75%) saturate(2498%) hue-rotate(180deg) brightness(96%) contrast(101%);",
    "00843D": "filter: invert(31%) sepia(99%) saturate(684%) hue-rotate(108deg) brightness(96%) contrast(101%);",
    "DA291C": "filter: invert(23%) sepia(54%) saturate(7251%) hue-rotate(355deg) brightness(90%) contrast(88%);",
    "ED8B00": "filter: invert(46%) sepia(89%) saturate(615%) hue-rotate(1deg) brightness(103%) contrast(104%);",
    "ffffff": "filter: invert(100%) sepia(93%) saturate(19%) hue-rotate(314deg) brightness(105%) contrast(104%);",
}


def return_delay_colors(delay: int) -> str:
    """Returns a color based on the delay.

    Args:
        delay (int): delay in minutes
    Returns:
        str: color
    """

    delay_dict = {
        "#ffff00": 5 <= delay < 10,
        "#ff0000": 10 <= delay < 15,
        "#800000": delay >= 15,
    }

    for color, condition in delay_dict.items():
        if condition:
            return color

    return "#ffffff"


def hex_to_css(hex_code: str) -> str:
    """Returns css filter based on hex color.

    Args:
        hex_code (str): hex color code, e.g. 'ffffff'
    Returns:
        str: css filter, e.g. 'filter: invert(100%) sepia(93%) saturate(19%) hue-rotate(314deg) brightness(105%) contrast(104%);'
    """
    return HEX_TO_CSS.get(hex_code, HEX_TO_CSS.get("ffffff"))
