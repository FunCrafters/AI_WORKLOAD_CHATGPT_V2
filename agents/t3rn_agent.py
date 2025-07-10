#!/usr/bin/env python3
"""
T3rn Agent
Main agent with internal tool loop using ChatGPT-4o-mini
Replaces QuestionAnalyzer with direct tool execution and response generation
"""
import os
import time
import random
from typing import List, Dict, Any, Optional
from tools_functions import available_llm_functions
from openai import NOT_GIVEN

from channel_logger import ChannelLogger
from session import Session
from openai.types.chat import ChatCompletionMessageParam, ChatCompletion, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from agents.base_agent import Agent, AgentContext, AgentResult
from tools_functions import get_function_schemas

class T3RNAgent(Agent):
    """Main agent that analyzes questions, executes tools, and generates responses"""
    
    def __init__(self, 
                 session: 'Session', 
                 channel_logger: 'ChannelLogger'):
        super().__init__(session, channel_logger)
        self.tools = get_function_schemas()  # All available tools
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and api_key != 'your_openai_api_key_here':
                self.openai_client = openai.OpenAI(api_key=api_key)
                self.openai_enabled = True
            else:
                self.openai_client = None
                self.openai_enabled = False
        else:
            self.openai_client = None
            self.openai_enabled = False
        
        # Complementary tools mapping (copied from QuestionAnalyzer)
        self.COMPLEMENTARY_MAPPING = {
            'db_rag_get_champion_details': 'db_get_champion_details',
            'db_get_champion_details': 'db_rag_get_champion_details',
            # Add more mappings here as needed
        }
        
        # Get available tools info (copied from QuestionAnalyzer)
        try:
            from tools.db_get_champions_list import db_get_champions_list_text
            self.champions_list = db_get_champions_list_text()
        except Exception:
            self.champions_list = "Champions list not available"
    
    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt - randomly choose between T3RN and T4RN"""
        
        champions_and_bosses = f"""CHAMPIONS LIST: {self.champions_list}"""
        
        # Randomly choose between CHARACTER_BASE_T3RN and CHARACTER_BASE_T4RN
        character_prompt = random.choice(['CHARACTER_BASE_T3RN', 'CHARACTER_BASE_T4RN'])
        
        # Log which character was chosen
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
        """Make OpenAI API call with error handling, copied from response_agent_gpt.py"""
        
        # Log LLM call to Prompts channel BEFORE making the call
        if self.channel_logger:
            self._log_llm_call_to_prompts_channel(messages, tools, use_json)
        
        # Try OpenAI first if available and configured
        if self.openai_enabled and self.openai_client:
            try:
                start_time = time.time()
                response = self.openai_client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=messages,
                    temperature=0.3,
                    max_tokens=8000,
                    tools = tools if tools else NOT_GIVEN,
                    tool_choice = 'auto' if tools else NOT_GIVEN,
                    response_format = {'type': 'json_object'} if use_json else NOT_GIVEN
                )
                
                elapsed_time = time.time() - start_time
                
                # Log consolidated model call info
                prompt_tokens = response.usage.prompt_tokens if response.usage else 0
                completion_tokens = response.usage.completion_tokens if response.usage else 0
                total_tokens = response.usage.total_tokens if response.usage else 0
                
                self.channel_logger.log_to_logs(f"⚡ gpt-4o-mini completed in {elapsed_time:.3f}s ({prompt_tokens}+{completion_tokens}={total_tokens} tokens)")
                return response
                
            except Exception as e:
                self.channel_logger.log_to_logs(f"❌ OpenAI API call failed: {str(e)}")
                raise Exception(f"T3rnAgent OpenAI API call failed: {str(e)}")
        else:
            raise Exception("OpenAI API not available or not configured")
    # TODO Complementary tools:
    # This function adds complementary tools based on the original tool calls.
    # So if db_rag_get_champion_details is called, it will also add db_get_champion_details
    # it also prevents duplicates by checking if the complementary tool with the same parameters already exists.
    def add_complementary_tools(self, tool_calls: List['ChatCompletionMessageToolCall']) -> List['ChatCompletionMessageToolCall']:
        """Add complementary tools - copied from QuestionAnalyzer"""
        
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
                
                # Only add if complementary function with these specific parameters doesn't exist
                if not complementary_already_exists:
                    complementary_call = ChatCompletionMessageToolCall(
                        id=f"toolcall-{complementary_function}",  # Use a unique or generated ID if needed
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
    
    def process_and_execute_tools(self, tool_calls: List['ChatCompletionMessageToolCall'], response_content: str, messages: List['ChatCompletionMessageParam']) -> bool:
        # Filter out agent spawning tools (we handle everything internally)
        regular_tool_calls = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            regular_tool_calls.append(tool_call)
        
        if not regular_tool_calls:
            self.channel_logger.log_to_logs("⚠️ No regular tools to execute")
            return False
        
        # Add complementary tools
        enhanced_tool_calls = self.add_complementary_tools(regular_tool_calls)
        
        # Log total number of tools that will actually be executed
        self.channel_logger.log_to_logs(f"🔧 Will execute {len(enhanced_tool_calls)} tools total (including complementary)")
        
        # Execute tools one by one and add to messages immediately
        for idx, tool_call in enumerate(enhanced_tool_calls):
            try:
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments
                
                # Parse arguments if they're a string
                if isinstance(function_args, str):
                    import json
                    try:
                        function_args = json.loads(function_args)
                    except json.JSONDecodeError as e:
                        error_msg = f"Invalid JSON in arguments: {str(e)}"
                        self.channel_logger.log_to_logs(f"❌ {function_name}: {error_msg}")
                        # TODO Check this call
                        self.channel_logger.log_tool_call(function_name, function_args, f"Parameter validation error: {error_msg}", idx + 1)
                        raise Exception(f"Tool execution failed: {error_msg}")
                    
                # TODO Why wont you let LLM call function second time if it wants?
                # Check if tool is already in current messages to avoid duplicates
                if self.memory_manager.is_tool_already_in_current_messages(messages, function_name, function_args):
                    self.channel_logger.log_to_logs(f"⚠️ {function_name} already in current messages, skipping")
                    continue
                
                # Check cache first
                cache_entry = self.memory_manager.lookup_tool_in_cache(self.session_data.get_memory(), function_name, function_args)
                
                if cache_entry:
                    # Use cached result
                    result = cache_entry['result']
                    self.channel_logger.log_to_logs(f"♻️ {function_name} from cache ({len(str(result))} chars)")
                    self.channel_logger.log_tool_call(function_name, function_args, f"[CACHED] {result}", idx + 1)
                    
                    # Update call_id to the cached one
                    tool_call_id = cache_entry['call_id']
                else:
                    # Execute the tool
                    if function_name in available_llm_functions:
                        try:
                            start_time = time.time()
                            tool_function = available_llm_functions[function_name]['function']
                            result = tool_function(**function_args)
                            elapsed_time = time.time() - start_time
                            
                            # Log to Logs channel
                            self.channel_logger.log_to_logs(f"🔧 {function_name} executed in {elapsed_time:.3f}s ({len(str(result))} chars)")
                            
                            # Log to Tool Calls channel with correct call number
                            self.channel_logger.log_tool_call(function_name, function_args, result, idx + 1)
                            
                            # Cache the result if it has llm_cache_duration > 0
                            # Check if result contains llm_cache_duration (default 0 if not present)
                            llm_cache_duration = 0
                            try:
                                result_json = json.loads(result) if isinstance(result, str) else result
                                if isinstance(result_json, dict):
                                    llm_cache_duration = result_json.get('llm_cache_duration', 0)
                            except:
                                pass
                            
                            if llm_cache_duration > 0:
                                self.memory_manager.add_tool_to_cache(
                                    self.session_data.get_memory(),
                                    function_name, function_args, result, llm_cache_duration
                                )
                            
                            tool_call_id = f"{function_name}_{idx}"
                            
                        except Exception as tool_error:
                            error_msg = f"Tool execution error: {str(tool_error)}"
                            self.channel_logger.log_to_logs(f"❌ {function_name}: {str(tool_error)}")
                            self.channel_logger.log_tool_call(function_name, function_args, error_msg, idx + 1)
                            result = error_msg
                            tool_call_id = f"{function_name}_{idx}"
                    else:
                        error_msg = f"Unknown tool: {function_name}"
                        self.channel_logger.log_to_logs(f"❌ Unknown tool: {function_name}")
                        self.channel_logger.log_tool_call(function_name, function_args, error_msg, idx + 1)
                        result = error_msg
                        tool_call_id = f"{function_name}_{idx}"
                
                # Create tool result
                tool_result = {
                    'tool_call_id': tool_call_id,
                    'function_name': function_name,
                    'function_args': function_args,
                    'result': result
                }
                
                # Check for tool error - be more specific about error detection
                # TODO This seems off. sometimes tools fails but should work fine.
                result_str = str(tool_result['result'])
                try:
                    # Try to parse as JSON to check for structured error
                    import json
                    result_json = json.loads(result_str)
                    if isinstance(result_json, dict) and result_json.get('status') == 'error':
                        raise Exception(f"Tool execution failed: {result_json.get('message', result_str)}")
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, check for obvious error patterns
                    if result_str.lower().startswith('error:') or result_str.lower().startswith('tool execution error:'):
                        raise Exception(f"Tool execution failed: {result_str}")
                
                # Add assistant message with function_call
                messages.append({
                    "role": "assistant",
                    "function_call": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments if isinstance(tool_call.function.arguments, str) else json.dumps(tool_call.function.arguments)
                    }
                })
                
                # Add function result immediately after
                messages.append({
                    "role": "function",
                    "name": tool_result['function_name'],
                    "content": str(tool_result['result'])
                })
                
            except Exception as e:
                self.channel_logger.log_to_logs(f"❌ Tool {tool_call.function.name} failed: {str(e)}")
                self.channel_logger.log_tool_call(tool_call.function.name, tool_call.function.arguments, f"Tool execution error: {str(e)}", idx + 1)
                raise Exception(f"Tool execution failed: {str(e)}")
        
        return True
    
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute T3rnAgent with internal tool loop"""
        
        self.channel_logger.log_to_logs("🚀 T3rnAgent starting with internal tool loop")
        
        # Get current user message
        current_user_message = context.original_user_message
        
        
        # Use memory manager from session
        if self.memory_manager is None:
            raise Exception("MemoryManager not set - should be passed from session")
        
        self.session_data = context.session_data
        # TODO Why context?
        memory_messages = self.memory_manager.prepare_messages_for_agent(context.session_data.get_memory(), current_user_message)
        
        # Prepare messages: system prompt + memory + current user message
        messages: List['ChatCompletionMessageParam'] = []
        
        # Add system prompt
        system_prompt = self.get_system_prompt(context)
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add memory context messages
        messages.extend(memory_messages)
        
        # Add screen context injection at session start
        try:
            from workload_game_cache import CURRENT_JSON_DATA
            
            # TODO session should be object
            if CURRENT_JSON_DATA:
                injection_messages = self.memory_manager.inject_screen_context(context.session_data.get_memory(), CURRENT_JSON_DATA)
                
                # TODO Try replace with developer.
                if injection_messages:
                    messages.extend(injection_messages)
                    self.channel_logger.log_to_logs(f"🎯 Screen injection: {len(injection_messages)} messages added")
                            
        except Exception as e:
            self.channel_logger.log_to_logs(f"⚠️ Screen injection error: {str(e)}")
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": current_user_message
        })
        
        self.channel_logger.log_to_logs(f"🧠 Memory: {len(memory_messages)} context messages loaded")
        
        # TODO Nie potrzebne z Chatem GPT.
        max_iterations = 10
        iteration = 0
        
        try:
            while iteration < max_iterations:
                iteration += 1
                self.channel_logger.log_to_logs(f"🔄 T3rnAgent iteration {iteration}")
                
                try:
                    # Check if this is the final iteration - no tools, force final answer
                    if iteration == max_iterations:
                        self.channel_logger.log_to_logs(f"⏰ T3RNAgent final iteration {iteration}/{max_iterations} - forcing final answer without tools")
                        
                        # Add strong instruction for final answer
                        from agents.agent_prompts import T3RN_FINAL_ITERATION_PROMPT
                        messages.append({
                            "role": "system",
                            "content": T3RN_FINAL_ITERATION_PROMPT
                        })
                        
                        # Call LLM WITHOUT tools
                        response = self.call_llm(messages, tools=None)
                    else:
                        # Normal iteration - call LLM with tools
                        response = self.call_llm(messages, tools=self.tools)
                    
                    # Check if tools were called (only possible in non-final iterations)
                    if iteration < max_iterations and hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                        tool_calls = response.choices[0].message.tool_calls
                        self.channel_logger.log_to_logs(f"🔧 T3RNAgent requested {len(tool_calls)} tools")
                        
                        # Process and execute tools using dedicated function
                        response_content = response.choices[0].message.content or ""
                        tools_executed = self.process_and_execute_tools(tool_calls, response_content, messages)
                        
                        if tools_executed:
                            # Continue loop - call LLM again with tool results
                            continue
                        else:
                            # No regular tools, treat as final response
                            pass
                    
                    # No tools called or final iteration - final answer
                    response_content = response.choices[0].message.content or ""
                    
                    # Add assistant's final response to messages for conversation history
                    messages.append({
                        "role": "assistant",
                        "content": response_content
                    })
                    
                    # Final answer - no tools, no clarification needed
                    if iteration == max_iterations:
                        self.channel_logger.log_to_logs(f"✅ T3RNAgent forced final answer after {iteration} iterations")
                    else:
                        self.channel_logger.log_to_logs(f"✅ T3RNAgent completed after {iteration} iterations")
                    self.channel_logger.log_to_logs(f"💭 T3RN AGENT PROCESSING: Completed in {iteration} iterations, final response generated")
                                        
                    result = AgentResult()
                    result.final_answer = response_content
                    
                    return result
                        
                except Exception as llm_error:
                    self.channel_logger.log_to_logs(f"❌ T3RNAgent error in iteration {iteration}: {str(llm_error)}")
                    raise llm_error
            
            # This should never be reached now
            raise Exception(f"T3RNAgent loop logic error")
            
        except Exception as main_error:
            # T3RNAgent failed - let workload_agent_system handle fallback
            self.channel_logger.log_to_logs(f"🚨 T3RNAgent failed: {str(main_error)}")            
            
            result = AgentResult()
            result.error_content = f"T3RN AGENT ERROR: Failed in iteration {iteration} - {str(main_error)}"
            
            result.final_answer = None
            
            return result
