from dataclasses import dataclass
from typing import Any, Callable

from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params.function_parameters import FunctionParameters


@dataclass
class T3RNTool:
    """
    Represents a tool function for the T3RN agent.
    This tool can be dependent on current session of LLM agent.
    """

    name: str
    function: Callable[..., dict | str]
    description: str
    system_prompt: str
    parameters: FunctionParameters

    def __call__(self, *args: Any, **kwds: Any) -> dict | str:
        return self.function(*args, **kwds)

    def get_function_schema(self) -> "ChatCompletionToolParam":
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
