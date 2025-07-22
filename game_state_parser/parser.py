import json
import logging

import elements

from game_state_parser.ui_element import UIElement

logger = logging.getLogger("GameStateParser")


def get_class_by_name(class_name: str):
    try:
        return getattr(elements, class_name)
    except (ImportError, AttributeError) as e:
        logger.debug(f"Error retrieving class '{class_name}': {e}")
        return None


def parse_recursive(data: dict, parent: UIElement):
    for key, value in data.items():
        if isinstance(value, dict):
            childClass = get_class_by_name(key)

            if childClass:
                childElement = childClass(value)
                parent.children[key] = childElement
                parse_recursive(value, childElement)


def parse_screen_data(screenData: dict):
    Screen = screenData["Screen"]
    ScreenData = screenData["ScreensData"]

    rootClass = get_class_by_name(Screen)
    if not rootClass:
        raise ValueError(f"Unknown screen class: {Screen}")

    rootElement = rootClass(ScreenData)

    parse_recursive(ScreenData, rootElement)

    return rootElement


def parse_ui_tree(json_raw: str) -> UIElement:
    data = json.loads(json_raw)

    screenData = data["screenData"]

    return parse_screen_data(screenData)


class GameStateParser:
    def __init__(self, json_raw: str):
        self.ui_tree = parse_ui_tree(json_raw)

    def build_prompt(self) -> str:
        try:
            return self.ui_tree.build_prompt()
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            return f"You are on the {self.ui_tree.__class__.__name__} screen. No further details available."

    def first(self, name: str) -> str:
        return ""


if __name__ == "__main__":
    path = "game_state_parser/20250715_100642_6310eb1e.json"
    with open(path, "r") as file:
        json_data = file.read()

    ui_tree = parse_ui_tree(json_data)
    print(ui_tree.build_prompt())
    champs = ui_tree.first("SelectedChampions")
    if champs:
        print(champs.build_prompt())
