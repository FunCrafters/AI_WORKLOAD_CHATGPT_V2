import json
import logging
from typing import Optional, Type

from . import elements
from .ui_element import UIElement

logger = logging.getLogger("GameStateParser")


def get_class_by_name(class_name: str) -> Optional[Type[UIElement]]:
    try:
        return getattr(elements, class_name)
    except (ImportError, AttributeError) as e:
        logger.debug(f"Error retrieving class '{class_name}': {e}")
        return None


def parse_recursive(data: dict, parent: UIElement):
    for key, value in data.items():
        if isinstance(value, dict):
            ChildClass = get_class_by_name(key)

            if ChildClass:
                childElement = ChildClass(value)
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
    try:
        screenData = data["screenData"]
        return parse_screen_data(screenData)
    except KeyError:
        logger.warning("Provided JSON does not match any known screen type. Using UnknownScreen.")

        return parse_screen_data({"Screen": "UnknownScreen", "ScreensData": data})


class GameStateParser:
    def __init__(self, json_raw: str):
        self.ui_tree = parse_ui_tree(json_raw)

    def build_prompt(self) -> str:
        try:
            return self.ui_tree.build_prompt()
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            return f"You are on the {self.ui_tree.__class__.__name__} screen. No further details available."

    def get_details(self, name: str) -> str:
        try:
            element = self.ui_tree.first(name)
            if element:
                return element.build_prompt()
            else:
                return f"No UI Element found for '{name}'"
        except Exception as e:
            logger.error(f"Error retrieving details for '{name}': {e}")
            return f"Error retrieving details for '{name}'"

    def get_keys(self) -> list:
        return self.ui_tree.get_keys()

    def get_context_heros(self, querry: str) -> str | None:
        # TODO
        # if there is given hero / character in context of the screen
        # this function should return info about it.
        # if there is multiple, it should return all of them.
        # and notice that there is multiple and why there is multiple.
        return None


if __name__ == "__main__":
    path = "game_state_parser/20250715_100642_6310eb1e.json"
    with open(path, "r") as file:
        json_data = file.read()

    ui_tree = parse_ui_tree(json_data)
    print(ui_tree.build_prompt())
    champs = ui_tree.first("SelectedChampions")
    if champs:
        print(champs.build_prompt())

    keys = ui_tree.get_keys()
    print(f"Keys in UI tree: {keys}")
