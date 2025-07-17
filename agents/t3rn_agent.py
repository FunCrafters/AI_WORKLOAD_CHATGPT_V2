#!/usr/bin/env python3
"""
T3rn Agent
Main agent with internal tool loop using ChatGPT-4o-mini
Replaces QuestionAnalyzer with direct tool execution and response generation
"""
import os
import time
import random
import json
import time
from typing import Callable, List, Optional
from agents.modules import screen_injector
from agents.modules.module import T3RNModule
from tools_functions import available_llm_functions
from openai import NOT_GIVEN
from agents.agent_prompts import T3RN_FINAL_ITERATION_PROMPT

from channel_logger import ChannelLogger
from session import Session
from openai.types.chat import ChatCompletionMessageParam, ChatCompletion, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
import openai

from agents.base_agent import Agent, AgentResult
from tools_functions import get_function_schemas
from tools.db_get_champions_list import db_get_champions_list_text


class T3RNAgent(Agent):    
    def __init__(self, 
                 session: 'Session', 
                 channel_logger: 'ChannelLogger'):
        super().__init__(session, channel_logger)
        self.tools = get_function_schemas() 
        
        self.openai_client = None

        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
        
        self.COMPLEMENTARY_MAPPING = {
            'db_rag_get_champion_details': 'db_get_champion_details',
            'db_get_champion_details': 'db_rag_get_champion_details',
            # Add more mappings here as needed
        }

        self.MODULES: List[T3RNModule] = []

        self.MODULES.append(screen_injector.ScreenContextInjector(self.channel_logger))
        
        try:
            self.champions_list = db_get_champions_list_text()
        except Exception:
            self.champions_list = "Champions list not available"
    
    def get_system_prompt(self) -> str:        
        champions_and_bosses = f"""CHAMPIONS LIST: {self.champions_list}"""
        
        character_prompt = random.choice(['CHARACTER_BASE_T3RN', 'CHARACTER_BASE_T4RN'])
        
        if hasattr(self, 'channel_logger') and self.channel_logger:
            self.channel_logger.log_to_logs(f"🎲 Selected character: {character_prompt}")
        
        return self.build_prompt(
            character_prompt,
            'GAME_CONTEXT',
            'QUESTION_ANALYZER_INITIAL_TASK',
            'QUESTION_ANALYZER_RULES',
            'CHAMPIONS_AND_BOSSES',
            champions_and_bosses,
            'CONTENT_RESTRICTIONS',
            'QUESTION_ANALYZER_TOOLS',
            'TOOL_RESULTS_ANALYSIS',
            'MOBILE_FORMAT'
        )

    def call_llm(self, 
                 messages: List['ChatCompletionMessageParam'], 
                 tools: Optional[List] = None, 
                 use_json: bool = False) -> 'ChatCompletion':

        if self.openai_client is not None:
            try:
                start_time = time.time()
                response = self.openai_client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=messages,
                    temperature=0.3,
                    max_completion_tokens=8000,
                    tools = tools if tools else NOT_GIVEN,
                    tool_choice = 'auto' if tools else NOT_GIVEN,
                    response_format = {'type': 'json_object'} if use_json else NOT_GIVEN
                )
                
                elapsed_time = time.time() - start_time
                
                prompt_tokens = response.usage.prompt_tokens if response.usage else 0
                completion_tokens = response.usage.completion_tokens if response.usage else 0
                total_tokens = response.usage.total_tokens if response.usage else 0
                
                self.channel_logger.log_to_logs(f"⚡ gpt-4o-mini completed in {elapsed_time:.3f}s ({prompt_tokens}+{completion_tokens}={total_tokens} tokens)")
                
                self._log_state(messages, response.choices[0].message.content if response.choices else None)

                return response
                
            except Exception as e:
                self.channel_logger.log_to_logs(f"❌ OpenAI API call failed: {str(e)}")
                raise Exception(f"T3rnAgent OpenAI API call failed: {str(e)}")
        else:
            raise Exception("OpenAI API not available or not configured")
    
    # TODO Complementary tools:
    # This function adds simillar tools based on the original tool call.
    # So if db_rag_get_champion_details is called, it will also add db_get_champion_details
    # it also prevents duplicates by checking if the complementary tool with the same parameters already exists.
    # I think that this should not be nesessery.
    def add_complementary_tools(self, tool_calls: List['ChatCompletionMessageToolCall']) -> List['ChatCompletionMessageToolCall']:
        # Create a new list with original + complementary tools
        enhanced_tool_calls = list(tool_calls)  # Copy original list
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments
            
            # Check if this function has a complementary tool
            if function_name in self.COMPLEMENTARY_MAPPING:
                complementary_function = self.COMPLEMENTARY_MAPPING[function_name]
                
                # Check if complementary function is already called with these specific parameters
                complementary_already_exists = False
                for existing_call in enhanced_tool_calls:
                    if (existing_call.function.name == complementary_function and
                        existing_call.function.arguments == function_args):
                        complementary_already_exists = True
                        break
                
                if not complementary_already_exists:
                    complementary_call = ChatCompletionMessageToolCall(
                        id=f"toolcall-{complementary_function}", 
                        type="function",
                        function=Function(
                            name=complementary_function,
                            arguments=function_args
                        )
                    )
                    enhanced_tool_calls.append(complementary_call)
                    
                    self.channel_logger.log_to_logs(f"🔗 Added complementary tool: {complementary_function} for {function_name}")
                else:
                    self.channel_logger.log_to_logs(f"⚠️ Complementary tool {complementary_function} already exists with same parameters, skipping")
        
        return enhanced_tool_calls
    
    def _is_tool_result_error(self, result_str: str) -> bool:
        import json

        try:
            result_json = json.loads(result_str)
            return isinstance(result_json, dict) and result_json.get("status") == "error"
        except (json.JSONDecodeError, TypeError):
            return result_str.strip().lower().startswith(("error:", "tool execution error:"))
    
    def process_and_execute_tools(
        self,
        tool_calls: List['ChatCompletionMessageToolCall'],
    ) -> List['ChatCompletionMessageParam']:
        result_messages: List['ChatCompletionMessageParam'] = [] 
        if not tool_calls:
            self.channel_logger.log_to_logs("⚠️ No tool calls provided")
            return []

        enhanced_tool_calls = self.add_complementary_tools(tool_calls)
        self.channel_logger.log_to_logs(f"🔧 Will execute {len(enhanced_tool_calls)} tools total (including complementary)")

        for idx, tool_call in enumerate(enhanced_tool_calls):
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

                if function_name not in available_llm_functions:
                    error_msg = f"Unknown tool: {function_name}"
                    # TODO more soft error handling
                    raise Exception(f"Tool execution failed: {error_msg}")

                tool_function: Callable[..., dict] = available_llm_functions[function_name]['function']
                start_time = time.time()
                try:
                    result = tool_function(**function_args)
                except Exception as e:
                    raise Exception(f"Tool execution failed in dramatic way: {e}")
                
                elapsed_time = time.time() - start_time

                self.channel_logger.log_to_logs(f"🔧 {function_name} executed in {elapsed_time:.3f}s ({len(str(result))} chars)")
                self.channel_logger.log_tool_call(function_name, function_args, result, idx + 1)

                result_messages.append({
                    "role": "assistant",
                    "function_call": {
                        "name": function_name,
                        "arguments": tool_call.function.arguments if isinstance(tool_call.function.arguments, str)
                                    else json.dumps(tool_call.function.arguments)
                    }
                })
                result_messages.append({
                    "role": "function",
                    "name": function_name,
                    "content": str(json.dumps(result)) if isinstance(result, dict) else str(result)
                })

            except Exception as e:
                self.channel_logger.log_to_logs(f"❌ Error during tool execute: {e}")
                self.channel_logger.log_to_tools(f"❌ Error during tool execute: {e}")
                raise Exception(f"Tool execution failed: {str(e)}")

        return result_messages
    
    
    def execute(self, user_message: str) -> AgentResult:        
        self.channel_logger.log_to_logs("🚀 T3rnAgent starting with internal tool loop")
                
        if self.memory_manager is None:
            raise Exception("MemoryManager not set - should be passed from session")

        for module in self.MODULES:
            self.session_data = module.before_user_message(self.session_data)
        
        memory_messages = self.memory_manager.prepare_messages_for_agent()

        # Messages added to the beginning of the conversation        
        system_messages: List['ChatCompletionMessageParam'] = []
        # Messages from the current iterations of LLM (e.g. tool calls and responses)
        current_messages: List['ChatCompletionMessageParam'] = []

        # system messages are always on the begining of the conv.
        system_prompt = self.get_system_prompt()
        system_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        for module in self.MODULES:
            system_messages.extend(
                module.inject_start_and_log(self.session_data)
            )

        for module in self.MODULES:
            memory_messages.extend(
                module.inject_before_user_message_and_log(self.session_data)
            )
        
        memory_messages.append({
            "role": "user",
            "content": user_message
        })

        for module in self.MODULES:
            memory_messages.extend(
                module.inject_after_user_message_and_log(self.session_data)
            )
        
        self.channel_logger.log_to_logs(f"🧠 Memory: {len(memory_messages)} context messages loaded")
        
        MAX_ITERATIONS = 4
        iteration = 0
        
        try:
            while iteration < MAX_ITERATIONS:
                iteration += 1
                self.channel_logger.log_to_logs(f"🔄 T3rnAgent iteration {iteration}")
                
                try:
                    if iteration == MAX_ITERATIONS:
                        # TODO if we are about to keep this message then will it degenerate 
                        # TODO performance of chatbot (it will try to answer in next iteration)
                        messages = system_messages + memory_messages + current_messages+[{
                            "role": "system",
                            "content": T3RN_FINAL_ITERATION_PROMPT
                        }]
                        
                        response = self.call_llm(messages, tools=None)
                    else:
                        messages = system_messages + memory_messages + current_messages 
                        response = self.call_llm(messages, tools=self.tools)
                    
                    if iteration < MAX_ITERATIONS and hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                        tool_calls = response.choices[0].message.tool_calls
                        self.channel_logger.log_to_logs(f"🔧 T3RNAgent requested {len(tool_calls)} tools")
                        
                        tools_executed = self.process_and_execute_tools(tool_calls)

                        current_messages.extend(tools_executed)

                        continue

                    response_content = response.choices[0].message.content or ""
                    
                    current_messages.append({
                        "role": "assistant",
                        "content": response_content
                    })
                    
                    self.channel_logger.log_to_logs(f"✅ T3RNAgent completed after {iteration} iterations")
                    
                    messages = memory_messages + current_messages
                    result = AgentResult(messages)

                    self.memory_manager.finalize_current_cycle(
                        result.messages
                    )
                    
                    for module in self.MODULES:
                        self.session_data = module.after_user_message(self.session_data)
                                
                    return result
                        
                except Exception as llm_error:
                    self.channel_logger.log_to_logs(f"❌ T3RNAgent error in iteration {iteration}: {str(llm_error)}")
                    raise llm_error
            
            # This should never be reached now
            raise Exception(f"T3RNAgent loop logic error")
            
        except Exception as main_error:
            # T3RNAgent failed - let workload_agent_system handle fallback
            self.channel_logger.log_to_logs(f"🚨 T3RNAgent failed: {str(main_error)}")            
            
            result = AgentResult(messages)
            result.error_content = f"T3RN AGENT ERROR: Failed in iteration {iteration} - {str(main_error)}"
            
            return result
