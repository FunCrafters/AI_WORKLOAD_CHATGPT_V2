import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict, Optional

from glom import glom

logger = logging.getLogger("GameStateParser")


def safe_output(default_value=""):
    """
    Decorator that catches all exceptions and returns a default value.
    Logs the exception for debugging purposes.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__qualname__}: {e}", exc_info=True)
                return default_value

        return wrapper

    return decorator


class UIElement(ABC):
    """
    Base class for UI elements in the game state parser.
    The child classes should match the structure of the game state JSON.
    """

    def __init__(self, tree: Dict[str, Any]):
        self.child_tree = tree
        self.children: Dict[str, "UIElement"] = {}
        pass

    def glom(self, path: str) -> Any:
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
        try:
            return glom(self.child_tree, path)
        except KeyError as e:
            logger.error(f"KeyError in {self.__class__.__name__} glom for path '{path}': {e}")
            return f"{path}"

    def glom_summary(self, path: str) -> str:
        """
        Helper method to extract UIElement from child tree using glom.
        Example:
        ```
        # glom_summary
        self.glom_summary("TeamSelectBaseUIPresenter.SelectedChampions")
        # equivalent to
        self.children["TeamSelectBaseUIPresenter"].children["SelectedChampions"].build_summary()
        """
        try:
            return glom(self.children, path).build_summary()
        except KeyError as e:
            logger.error(f"KeyError in {self.__class__.__name__} glom_summary for path '{path}': {e}")
            return path

    def glom_prompt(self, path: str) -> str:
        """
        Helper method to extract UIElement from child tree using glom.
        Example:
        ```
        # glom_prompt
        self.glom_prompt("TeamSelectBaseUIPresenter.SelectedChampions")
        # equivalent to
        self.children["TeamSelectBaseUIPresenter"].children["SelectedChampions"].build_prompt()
        """
        try:
            return glom(self.children, path).build_prompt()
        except KeyError as e:
            logger.error(f"KeyError in {self.__class__.__name__} glom_prompt for path '{path}': {e}")
            return path

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

    def get_keys(self) -> list:
        """
        Returns a list of keys in children and all its descendants.
        """
        keys = list(self.children.keys())
        for child in self.children.values():
            keys.extend(child.get_keys())
        return keys

    def __getitem__(self, item: str):
        return self.children.get(item)

    def __getattr__(self, item: str):
        if item in self.children:
            return self.children[item]

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    @abstractmethod
    def build_prompt(self) -> str:
        """
        Returns full description of the UI element with brif overview of the content.
        It should also guide the LLM to use uxHelper to get more details.
        Use glom functions to access data from the child tree or get summary of the child element.
        """
        pass

    @abstractmethod
    def build_summary(self) -> str:
        """
        Returns short summary of the UI element.
        """
        pass
