#!/usr/bin/env python3
"""
T3rn Agent
Main agent with internal tool loop using ChatGPT-4o-mini
Replaces QuestionAnalyzer with direct tool execution and response generation
"""

import json
import os
import random
import time
from typing import List, Type

import openai
from openai import NOT_GIVEN
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
)

from agents.agent_prompts import T3RN_FINAL_ITERATION_PROMPT
from agents.base_agent import (
    Agent,
    AgentResult,
    chat_response_to_str,
    chat_response_toolcalls,
)
from agents.modules import (
    basic_tools,
    champion_comp,
    champion_tools,
    proactive_smalltalk,
    random_greetings,
    screen_injector,
    summary,
)
from agents.modules.module import (
    T3RNModule,
    build_system_instructions_from_tools,
    get_tool_by_name,
)
from channel_logger import ChannelLogger
from session import Session
from tools.db_get_champions_list import db_get_champions_list_text
from tools_functions import T3RNTool
from workload_config import AGENT_CONFIG


class T3RNAgent(Agent):
    def __init__(self, session: "Session", channel_logger: "ChannelLogger"):
        super().__init__(session, channel_logger)

        self.openai_client = None

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)

        self.MODULES: List[T3RNModule] = []

        self.add_module(screen_injector.ScreenContextInjector)
        self.add_module(summary.SummaryInjector)
        self.add_module(basic_tools.BasicTools)
        self.add_module(champion_tools.ChampionTools)
        self.add_module(champion_comp.ChampionCompTools)
        self.add_module(random_greetings.RandomGreetings)
        self.add_module(proactive_smalltalk.ProactiveSmalltalk)

    def add_module(self, module_class: Type[T3RNModule]) -> None:
        module = module_class(self.channel_logger)
        module_name = module.__class__.__name__

        if module_name not in AGENT_CONFIG:
            self.channel_logger.log_to_logs(
                f"⚠️ Module {module_name} not defined in AGENT_CONFIG, disabling it"
            )
            return

        if not AGENT_CONFIG.getboolean(module_name, "enabled", fallback=True):
            self.channel_logger.log_to_logs(
                f"⚠️ Module {module_name} is disabled in AGENT_CONFIG"
            )
            return

        for key, value in AGENT_CONFIG[module_name].items():
            setattr(module, key, value)

        self.MODULES.append(module)
        self.channel_logger.log_to_logs(f"✅ Module {module_name} is loaded")

    def collect_tools(self) -> List["T3RNTool"]:
        tools: List["T3RNTool"] = []
        for module in self.MODULES:
            tools.extend(module.define_tools(self.session_data))
        return tools

    def _get_character(self):
        t3rn_weight = AGENT_CONFIG.getfloat(
            "T3RNAgent", "t3rn_character_weight", fallback=0.5
        )
        t4rn_weight = 1.0 - t3rn_weight

        character_prompt = random.choices(
            ["CHARACTER_BASE_T3RN", "CHARACTER_BASE_T4RN"],
            weights=[t3rn_weight, t4rn_weight],
        )[0]
        return character_prompt

    def get_system_prompt(self, tools: List["T3RNTool"]) -> str:
        self.champions_list = db_get_champions_list_text()
        champions_and_bosses = f"""# CHAMPIONS LIST:\n{self.champions_list}"""
        tool_prompts = build_system_instructions_from_tools(tools)

        character_prompt = self._get_character()

        if hasattr(self, "channel_logger") and self.channel_logger:
            self.channel_logger.log_to_logs(
                f"🎲 Selected character: {character_prompt}"
            )

        return self.build_prompt(
            character_prompt,
            "GAME_CONTEXT",
            "QUESTION_ANALYZER_INITIAL_TASK",
            "QUESTION_ANALYZER_RULES",
            "CHAMPIONS_AND_BOSSES",
            champions_and_bosses,
            "CONTENT_RESTRICTIONS",
            tool_prompts,
            "TOOL_RESULTS_ANALYSIS",
            "MOBILE_FORMAT",
        )

    def call_llm(
        self,
        messages: List["ChatCompletionMessageParam"],
        tools: List["T3RNTool"],
        use_tools: bool = True,
        use_json: bool = False,
    ) -> "ChatCompletion":
        if self.openai_client is not None:
            try:
                start_time = time.time()
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=AGENT_CONFIG.getfloat("T3RNAgent", "agent_temperature"),
                    max_completion_tokens=AGENT_CONFIG.getint(
                        "T3RNAgent", "max_completion_tokens"
                    ),
                    tools=[tool.get_function_schema() for tool in tools],
                    tool_choice="auto" if use_tools else "none",
                    response_format={"type": "json_object"} if use_json else NOT_GIVEN,
                )

                elapsed_time = time.time() - start_time

                prompt_tokens = response.usage.prompt_tokens if response.usage else 0
                completion_tokens = (
                    response.usage.completion_tokens if response.usage else 0
                )
                total_tokens = response.usage.total_tokens if response.usage else 0

                self.channel_logger.log_to_logs(
                    f"⚡ gpt-4o-mini completed in {elapsed_time:.3f}s ({prompt_tokens}+{completion_tokens}={total_tokens} tokens)"
                )

                self._log_state(
                    messages,
                    chat_response_to_str(response),
                )

                return response

            except Exception as e:
                self.channel_logger.log_to_logs(f"❌ OpenAI API call failed: {str(e)}")
                raise Exception(f"T3rnAgent OpenAI API call failed: {str(e)}")
        else:
            raise Exception("OpenAI API not available or not configured")

    def _is_tool_result_error(self, result_str: str) -> bool:
        import json

        try:
            result_json = json.loads(result_str)
            return (
                isinstance(result_json, dict) and result_json.get("status") == "error"
            )
        except (json.JSONDecodeError, TypeError):
            return (
                result_str.strip()
                .lower()
                .startswith(("error:", "tool execution error:"))
            )

    def process_and_execute_tools(
        self,
        tool_calls: List["ChatCompletionMessageToolCall"],
        tools: List["T3RNTool"],
    ) -> List["ChatCompletionMessageParam"]:
        result_messages: List["ChatCompletionMessageParam"] = []
        if not tool_calls:
            self.channel_logger.log_to_logs("⚠️ No tool calls provided")
            return []

        self.channel_logger.log_to_logs(
            f"🔧 Will execute {len(tool_calls)} tools total (including complementary)"
        )

        for idx, tool_call in enumerate(tool_calls):
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments

            try:
                if isinstance(function_args, str):
                    try:
                        function_args = json.loads(function_args)
                    except json.JSONDecodeError as e:
                        error_msg = f"Invalid JSON in arguments: {str(e)}"
                        self.channel_logger.log_to_tools(error_msg)
                        # TODO more soft error handling
                        raise Exception(f"Tool execution failed: {error_msg}")

                tool_function = get_tool_by_name(tools, function_name)

                if tool_function is None:
                    error_msg = f"Unknown tool: {function_name}"
                    # TODO more soft error handling
                    raise Exception(f"Tool execution failed: {error_msg}")

                start_time = time.time()
                try:
                    result = tool_function(**function_args)
                except Exception as e:
                    raise Exception(f"Tool execution failed in dramatic way: {e}")

                elapsed_time = time.time() - start_time

                self.channel_logger.log_to_logs(
                    f"🔧 {function_name} executed in {elapsed_time:.3f}s ({len(str(result))} chars)"
                )
                self.channel_logger.log_tool_call(
                    function_name, function_args, result, idx + 1
                )

                result_messages.append(
                    {
                        "role": "assistant",
                        "function_call": {
                            "name": function_name,
                            "arguments": tool_call.function.arguments
                            if isinstance(tool_call.function.arguments, str)
                            else json.dumps(tool_call.function.arguments),
                        },
                    }
                )
                result_messages.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": str(json.dumps(result))
                        if isinstance(result, dict)
                        else str(result),
                    }
                )

            except Exception as e:
                self.channel_logger.log_to_logs(f"❌ Error during tool execute: {e}")
                self.channel_logger.log_to_tools(f"❌ Error during tool execute: {e}")
                raise Exception(f"Tool execution failed: {str(e)}")

        return result_messages

    def execute(self, user_message: str) -> AgentResult:
        self.channel_logger.log_to_logs("🚀 T3rnAgent starting with internal tool loop")

        if self.memory_manager is None:
            raise Exception("MemoryManager not set - should be passed from session")

        self.memory_manager.memory["last_user_message"] = user_message

        for module in self.MODULES:
            self.session_data = module.before_user_message(self.session_data)

        tools = self.collect_tools()

        memory_messages = self.memory_manager.prepare_messages_for_agent()

        # Messages added to the beginning of the conversation
        system_messages: List["ChatCompletionMessageParam"] = []
        # Messages from the current iterations of LLM (e.g. tool calls and responses)
        current_messages: List["ChatCompletionMessageParam"] = []

        # system messages are always on the begining of the conv.
        system_prompt = self.get_system_prompt(tools)
        system_messages.append({"role": "system", "content": system_prompt})

        for module in self.MODULES:
            system_messages.extend(module.inject_start_and_log(self.session_data))

        for module in self.MODULES:
            memory_messages.extend(
                module.inject_before_user_message_and_log(self.session_data)
            )

        memory_messages.append({"role": "user", "content": user_message})

        for module in self.MODULES:
            memory_messages.extend(
                module.inject_after_user_message_and_log(self.session_data)
            )

        self.channel_logger.log_to_logs(
            f"🧠 Memory: {len(memory_messages)} context messages loaded"
        )

        MAX_ITERATIONS = AGENT_CONFIG.getint("T3RNAgent", "max_iterations")
        iteration = 0

        try:
            while iteration < MAX_ITERATIONS:
                iteration += 1
                self.channel_logger.log_to_logs(f"🔄 T3rnAgent iteration {iteration}")

                try:
                    if iteration == MAX_ITERATIONS:
                        messages = (
                            system_messages
                            + memory_messages
                            + current_messages
                            + [
                                {
                                    "role": "system",
                                    "content": T3RN_FINAL_ITERATION_PROMPT,
                                }
                            ]
                        )

                        response = self.call_llm(messages, tools=tools, use_tools=False)
                    else:
                        messages = system_messages + memory_messages + current_messages
                        response = self.call_llm(messages, tools=tools, use_tools=True)

                    tool_calls = chat_response_toolcalls(response)

                    if iteration < MAX_ITERATIONS and len(tool_calls) > 0:
                        self.channel_logger.log_to_logs(
                            f"🔧 T3RNAgent requested {len(tool_calls)} tools"
                        )

                        tools_executed = self.process_and_execute_tools(
                            tool_calls, tools
                        )

                        current_messages.extend(tools_executed)

                        continue

                    response_content = chat_response_to_str(response, content_only=True)

                    current_messages.append(
                        {"role": "assistant", "content": response_content}
                    )

                    self.channel_logger.log_to_logs(
                        f"✅ T3RNAgent completed after {iteration} iterations"
                    )

                    messages = memory_messages + current_messages
                    result = AgentResult(messages)

                    self.memory_manager.finalize_current_cycle(result.messages)

                    for module in self.MODULES:
                        self.session_data = module.after_user_message(self.session_data)

                    return result

                except Exception as llm_error:
                    self.channel_logger.log_to_logs(
                        f"❌ T3RNAgent error in iteration {iteration}: {str(llm_error)}"
                    )
                    raise llm_error

            # This should never be reached now
            raise Exception("T3RNAgent loop logic error")

        except Exception as main_error:
            # T3RNAgent failed - let workload_agent_system handle fallback
            self.channel_logger.log_to_logs(f"🚨 T3RNAgent failed: {str(main_error)}")

            result = AgentResult(messages)
            result.error_content = (
                f"T3RN AGENT ERROR: Failed in iteration {iteration} - {str(main_error)}"
            )

            return result
