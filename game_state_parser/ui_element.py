import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import elements
from glom import glom


class UIElement(ABC):
    """
    Base class for UI elements in the game state parser.
    The child classes should match the structure of the game state JSON.
    """

    def __init__(self, tree: Dict[str, Any]):
        self.child_tree = tree
        self.children: Dict[str, "UIElement"] = {}
        pass

    def glom(self, path: str, default=None) -> Any | None:
        """
        Helper method to extract data from the child tree using glom.
        You can use this instead of using direcly dict
        Example
        ```
        # glom
        self.glom("CampaignTeamSelectUIPresenter.BattleName")
        # equivalent to
        self.child_tree["CampaignTeamSelectUIPresenter"]["BattleName"]
        ```
        """
        return glom(self.child_tree, path, default=default)

    def glom_summary(self, path: str) -> "UIElement":
        """
        Helper method to extract UIElement from child tree using glom.
        Example:
        ```
        # glom_summary
        self.glom_summary("TeamSelectBaseUIPresenter.SelectedChampions")
        # equivalent to
        self.children["TeamSelectBaseUIPresenter"].children["SelectedChampions"]
        """
        return glom(self.children, path)

    def first(self, name: str) -> Optional["UIElement"]:
        """
        Returns first `UIElement` with the given name in children.
        """
        if name in self.children:
            return self.children[name]
        else:
            for child in self.children.values():
                result = child.first(name)
                if result:
                    return result
        return None

    def __getitem__(self, item: str):
        return self.children.get(item)

    def __getattr__(self, item: str):
        if item in self.children:
            return self.children[item]

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{item}'"
        )

    @abstractmethod
    def build_prompt(self) -> str:
        """
        Returns full description of the UI element with brif overview of the content.
        It should also guide the LLM to use uxHelper to get more details.
        """
        pass

    @abstractmethod
    def build_summary(self) -> str:
        """
        Returns short summary of the UI element.
        """
        pass


def get_class_by_name(class_name: str):
    try:
        return getattr(elements, class_name)
    except (ImportError, AttributeError) as e:
        print(f"Error retrieving class '{class_name}': {e}")
        return None


def parse_screen_data(screenData: dict):
    Screen = screenData["Screen"]

    ScreenData = screenData["ScreensData"]

    rootClass = get_class_by_name(Screen)
    if not rootClass:
        raise ValueError(f"Unknown screen class: {Screen}")

    rootElement = rootClass(ScreenData)

    def parse_recursive(data: dict, parent: UIElement):
        for key, value in data.items():
            if isinstance(value, dict):
                childClass = get_class_by_name(key)

                if childClass:
                    childElement = childClass(value)
                    parent.children[key] = childElement
                    parse_recursive(value, childElement)

    parse_recursive(ScreenData, rootElement)

    return rootElement


def parse_ui_tree(json_raw: str) -> UIElement:
    data = json.loads(json_raw)

    screenData = data["screenData"]

    return parse_screen_data(screenData)


if __name__ == "__main__":
    path = "game_state_parser/20250715_100642_6310eb1e.json"
    with open(path, "r") as file:
        json_data = file.read()

    ui_tree = parse_ui_tree(json_data)
    print(ui_tree.build_prompt())
    champs = ui_tree.first("SelectedChampions")
    if champs:
        print(champs.build_prompt())
