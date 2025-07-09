#!/usr/bin/env python3
"""
Base Agent Class
Foundation for all agents in the agent-based architecture
"""

import time
import logging
import ollama
import json
import textwrap
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from openai.types.chat import ChatCompletionMessageParam
from channel_logger import ChannelLogger
from session import Session

# Logger
logger = logging.getLogger("Base Agent")

class AgentContext:
    """Context object passed between agents containing all necessary information"""
    
    def __init__(self, session: 'Session', logger: 'ChannelLogger'):
        # Basic data
        self.original_user_message = ""    
        # Session data
        self.session_data: 'Session' = session
        self.channel_logger: 'ChannelLogger' = logger
        # Action ID for tracking across channels
        self.action_id = None        
        # Simple conversation tracking
        self.conversation_topics = []
    

class AgentResult:
    """Result object returned by agent execution"""
    
    def __init__(self):
        self.final_answer: Optional[str] = None
        self.spawn_agents: List[Tuple[Agent, AgentContext]] = []
        self.user_message: str = ""
        self.error_content: str = ""
        self.missing_information: Optional[List[str]] = None

class Agent(ABC):
    """Base class for all agents"""
    
    def __init__(self, session: 'Session', channel_logger: 'ChannelLogger'):
        self.tools = []
        self.session_data: 'Session' = session
        self.channel_logger: 'ChannelLogger' = channel_logger
        # TODO is this correct? Trace back to session_data if it can be guaranteed to have memory manager
        if self.session_data.memory_manager is None: 
            raise ValueError("Session must have a memory manager initialized")
        
        self.memory_manager = self.session_data.memory_manager

   
    
    @abstractmethod
    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt for this agent"""
        pass
    
    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent with given context"""
        pass
    
    def prepare_messages(self, context: AgentContext) -> List[Dict[str, str]]:
        """Prepare messages for LLM call"""        
        # Get base prompt
        base_prompt = self.get_system_prompt(context)
        
        # Get current user message (simplified - just use original_user_message)
        current_user_message = context.original_user_message
        
        # Simple message preparation - just system prompt + user message
        return [
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": current_user_message}
        ]
    
    def call_llm(self, 
                 messages: List['ChatCompletionMessageParam'], 
                 tools: Optional[List] = None, 
                 use_json: bool = False) -> Any:
        """Make LLM call with error handling"""
        
        # Log LLM call to Prompts channel BEFORE making the call
        self._log_llm_call_to_prompts_channel(messages, tools, use_json)
            
        try:
            start_time = time.time()
            
            call_params = {
                'model': 'llama3.1:8b',  # Default model for base agent
                'messages': messages
            }
            
            if tools:
                call_params['tools'] = tools
            
            if use_json:
                call_params['format'] = 'json'
            
            # Add keep_alive to maintain models in memory
            call_params['keep_alive'] = '60m'
            
            response = ollama.chat(**call_params)
            
            elapsed_time = time.time() - start_time
            
            # Log consolidated model call info
            prompt_tokens = getattr(response, 'prompt_eval_count', 0)
            completion_tokens = getattr(response, 'eval_count', 0)
            
            if prompt_tokens and completion_tokens:
                total_tokens = prompt_tokens + completion_tokens
                self.channel_logger.log_to_logs(f"⚡ Base agent completed in {elapsed_time:.3f}s ({prompt_tokens}+{completion_tokens}={total_tokens} tokens)")
            else:
                self.channel_logger.log_to_logs(f"⚡ Base agent completed in {elapsed_time:.3f}s")
        
            return response
            
        except Exception as e:
            error_msg = f"LLM call failed for base agent: {str(e)}"
            self.channel_logger.log_to_logs(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def execute_tools(self, tool_calls: List) -> List[Dict[str, Any]]:
        """Execute tools and return results - available to all agents"""
        if not tool_calls:
            return []
        
        # Import here to avoid circular imports
        from tools_functions import available_llm_functions
        import time
        
        tool_results = []
        
        # Add complementary tools first
        enhanced_tool_calls = self._add_complementary_tools(tool_calls)
        
        for idx, tool_call in enumerate(enhanced_tool_calls):
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments
            
            # === PARAMETER VALIDATION AND NORMALIZATION ===
            try:
                # Log original tool call details for debugging
                self.channel_logger.log_to_logs(f"🔍 Tool call debug: function_name='{function_name}', args_type={type(function_args).__name__}")
                
                # Check if function_args is a string (JSON) - if so, parse it
                if isinstance(function_args, str):
                    self.channel_logger.log_to_logs(f"⚠️ {function_name}: arguments are JSON string, parsing...")
                    
                    # Parse JSON string to dictionary
                    function_args = json.loads(function_args)
                
                # Validate that function_args is now a dictionary
                if not isinstance(function_args, dict):
                    raise ValueError(f"Arguments must be dict after parsing, got {type(function_args).__name__}")
                
                # Log successful validation with key=value pairs
                if function_args:
                    # Format as key=value pairs, truncate long values
                    arg_pairs = []
                    for key, value in function_args.items():
                        value_str = textwrap.shorten(str(value), width=50)
                        arg_pairs.append(f"{key}={value_str}")
                    args_display = ", ".join(arg_pairs)
                    self.channel_logger.log_to_logs(f"✅ {function_name}: arguments validated - {args_display}")
                else:
                    self.channel_logger.log_to_logs(f"✅ {function_name}: arguments validated - no arguments")
                    
            except json.JSONDecodeError as json_error:
                error_msg = f"Invalid JSON in arguments: {str(json_error)}"
                self.channel_logger.log_to_logs(f"❌ {function_name}: {error_msg}")
                
                # Log validation error to Tool Calls channel
                validation_error = f"Parameter validation error: {error_msg}"
                self.channel_logger.log_tool_call(function_name, tool_call.function.arguments, validation_error, idx + 1)
                
                tool_results.append({
                    'tool_call_id': f"{function_name}_{idx}",
                    'function_name': function_name,
                    'function_args': tool_call.function.arguments,  # Original args for debugging
                    'result': validation_error
                })
                continue
                
            except Exception as validation_error:
                error_msg = f"Argument validation failed: {str(validation_error)}"
                self.channel_logger.log_to_logs(f"❌ {function_name}: {error_msg}")
                
                # Log validation error to Tool Calls channel
                validation_error_msg = f"Parameter validation error: {error_msg}"
                self.channel_logger.log_tool_call(function_name, tool_call.function.arguments, validation_error_msg, idx + 1)
                
                tool_results.append({
                    'tool_call_id': f"{function_name}_{idx}",
                    'function_name': function_name,
                    'function_args': tool_call.function.arguments,  # Original args for debugging
                    'result': validation_error_msg
                })
                continue
            
            # === SAFE TOOL EXECUTION ===
            if function_name in available_llm_functions:
                try:
                    start_time = time.time()
                    tool_function = available_llm_functions[function_name]['function']
                    result = tool_function(**function_args)
                    elapsed_time = time.time() - start_time
                    
                    self.channel_logger.log_to_logs(f"🔧 {function_name} executed in {elapsed_time:.3f}s ({len(str(result))} chars)")
                    
                    # Log detailed tool call info to Tool Calls channel
                    self.channel_logger.log_tool_call(function_name, function_args, result, idx + 1)
                    
                    tool_results.append({
                        'tool_call_id': f"{function_name}_{idx}",
                        'function_name': function_name,
                        'function_args': function_args,
                        'result': result
                    })
                    
                except Exception as e:
                    error_msg = f"Tool execution error: {str(e)}"
                    self.channel_logger.log_to_logs(f"❌ {function_name}: {str(e)}")
                    
                    # Log failed tool call to Tool Calls channel
                    self.channel_logger.log_tool_call(function_name, function_args, error_msg, idx + 1)
                    
                    tool_results.append({
                        'tool_call_id': f"{function_name}_{idx}",
                        'function_name': function_name,
                        'function_args': function_args,
                        'result': error_msg
                    })
            else:
                error_msg = f"Unknown tool: {function_name}"
                self.channel_logger.log_to_logs(f"❌ Unknown tool: {function_name}")
                
                # Log unknown tool call to Tool Calls channel
                self.channel_logger.log_tool_call(function_name, function_args, error_msg, idx + 1)
                
                tool_results.append({
                    'tool_call_id': f"{function_name}_{idx}",
                    'function_name': function_name,
                    'function_args': function_args,
                    'result': error_msg
                })
        
        return tool_results
    
    def _add_complementary_tools(self, tool_calls: List) -> List:
        """Add complementary tools to the tool calls list based on existing calls"""
        complementary_mapping = {
            'db_rag_get_champion_details': 'db_get_champion_details',
            'db_get_champion_details': 'db_rag_get_champion_details',
            # Add more mappings here as needed
        }
        
        # Create a new list with original + complementary tools
        enhanced_tool_calls = list(tool_calls)  # Copy original list
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = tool_call.function.arguments
            
            # Check if this function has a complementary tool
            if function_name in complementary_mapping:
                complementary_function = complementary_mapping[function_name]
                
                # Check if complementary function is already called with these specific parameters
                # Check both original tool_calls AND enhanced_tool_calls to avoid duplicates
                complementary_already_exists = False
                for existing_call in enhanced_tool_calls:
                    if (existing_call.function.name == complementary_function and 
                        existing_call.function.arguments == function_args):
                        complementary_already_exists = True
                        break
                
                # Only add if complementary function with these specific parameters doesn't exist
                if not complementary_already_exists:
                    # Create a new tool call object with same arguments
                    class ComplementaryToolCall:
                        def __init__(self, function_name, function_args):
                            self.function = type('function', (), {
                                'name': function_name,
                                'arguments': function_args
                            })()
                    
                    complementary_call = ComplementaryToolCall(
                        complementary_function, 
                        function_args
                    )
                    enhanced_tool_calls.append(complementary_call)
                    
                    self.channel_logger.log_to_logs(f"🔗 Added complementary tool: {complementary_function} for {function_name}")
                else:
                    self.channel_logger.log_to_logs(f"⚠️ Complementary tool {complementary_function} already exists with same parameters, skipping")
        
        return enhanced_tool_calls

    def _log_llm_call_to_prompts_channel(self, messages: List['ChatCompletionMessageParam'], tools: Optional[List] = None, 
                                       use_json: bool = False):
        """Log complete LLM call information to Prompts channel"""
        try:            
            action_id = self.channel_logger.action_id or 'Unknown'
            agent_name = self.__class__.__name__
            
            # Extract system prompt (first message)
            system_prompt = ""
            if messages and messages[0].get('role') == 'system':
                system_prompt = messages[0]['content']
                # No truncation - show complete system prompt
            
            # Format messages (with intelligent length limits for readability)
            formatted_messages = []
            for msg in messages:
                content = msg.get('content', '')
                
                # Handle None content
                if content is None:
                    content = '[None]'
                
                # Special handling for different message types
                if msg.get('role') == 'function':
                    # Tool results - show basic info only
                    content = f"[Tool result: {len(str(content))} chars]"
                elif content and content.startswith("Tool execution results:"):
                    content = textwrap.shorten(content, width=200, placeholder="[...]\n[truncated - tool results]")
                elif len(content) > 300:
                    content = textwrap.shorten(content, width=300)
                
                formatted_msg = {
                    "role": msg['role'],
                    "content": content
                }

                if 'tool_calls' in msg:
                    formatted_msg['tool_calls'] = "[tool_calls_present]"
                if 'function_call' in msg:
                    formatted_msg['function_call'] = {       
                        "name": msg['function_call']['name'], 
                        "arguments": "[arguments_present]"
                    }
                if 'name' in msg:
                    formatted_msg['name'] = msg['name']
                formatted_messages.append(formatted_msg)
            
            # Create complete log (action_id will be added by channel_logger)
            prompt_log = f"""{agent_name} | Base Agent
                === CALL PARAMETERS ===
                Model: llama3.1:8b
                Format: {'json' if use_json else 'standard'}
                Keep-alive: 60m

                === MESSAGES TO LLM ===
                {json.dumps(formatted_messages, indent=2, ensure_ascii=False)}

                === SYSTEM PROMPT ===
                {system_prompt}
                ---
                """.strip()
            self.channel_logger.log_to_prompts(prompt_log)
            
        except Exception as e:
            self.channel_logger.log_to_logs(f"❌ Failed to log to Prompts channel: {str(e)}")



    def build_prompt(self, *fragments) -> str:
        """Build system prompt from prompt fragments"""
        from agents.agent_prompts import (
            CHARACTER_BASE_T3RN, CHARACTER_BASE_T4RN, GAME_CONTEXT, CONTENT_RESTRICTIONS, T3RN_INTRODUCTION,
            JSON_FORMAT,MOBILE_FORMAT,
            QUESTION_ANALYZER_INITIAL_TASK, 
            QUESTION_ANALYZER_RULES, QUESTION_ANALYZER_TOOLS, CHAMPIONS_AND_BOSSES,
            TOOL_RESULTS_ANALYSIS
        )
        
        # Map fragment names to actual fragments
        fragment_map = {
            'CHARACTER_BASE_T3RN': CHARACTER_BASE_T3RN,
            'CHARACTER_BASE_T4RN': CHARACTER_BASE_T4RN,
            'GAME_CONTEXT': GAME_CONTEXT,
            'CONTENT_RESTRICTIONS': CONTENT_RESTRICTIONS,
            'T3RN_INTRODUCTION': T3RN_INTRODUCTION,
            'JSON_FORMAT': JSON_FORMAT,
            'MOBILE_FORMAT': MOBILE_FORMAT,
            'QUESTION_ANALYZER_INITIAL_TASK': QUESTION_ANALYZER_INITIAL_TASK,
            'CHAMPIONS_AND_BOSSES': CHAMPIONS_AND_BOSSES,
            'QUESTION_ANALYZER_RULES': QUESTION_ANALYZER_RULES,
            'QUESTION_ANALYZER_TOOLS': QUESTION_ANALYZER_TOOLS,
            'TOOL_RESULTS_ANALYSIS': TOOL_RESULTS_ANALYSIS
        }
        
        # Build prompt from fragments
        prompt_parts = []
        for fragment in fragments:
            if isinstance(fragment, str):
                if fragment in fragment_map:
                    prompt_parts.append(fragment_map[fragment])
                else:
                    # Treat as custom text
                    prompt_parts.append(fragment)
            else:
                # Convert to string
                prompt_parts.append(str(fragment))
        
        return '\n\n'.join(prompt_parts)

    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration for serialization"""
        return {
            'class_name': self.__class__.__name__
        }
    
