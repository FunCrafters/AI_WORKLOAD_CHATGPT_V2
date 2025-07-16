#!/usr/bin/env python3
"""
Simple Memory Manager
Follows user-defined simple rules for conversation memory management
"""

import os
import time
import json
import hashlib
import uuid
import textwrap
from typing import Dict, List, Any, Optional, TypedDict
from venv import logger
from openai.types.chat import ChatCompletionMessageParam
import markdown
from bs4 import BeautifulSoup
from agents.base_agent import chat_completion_to_content_str
from channel_logger import ChannelLogger
import openai

class ConversationMemory(TypedDict):
    summary: str|None
    running_messages: List['ChatCompletionMessageParam']
    all_messages: List['ChatCompletionMessageParam']

# TODO test diffrent summarization heuristics
# TODO split into MemoryMenger, CacheManager and MessageInjector 
class MemoryManager:
    def __init__(self, channel_logger: 'ChannelLogger'):
        self.max_exchanges = 20            # Max exchanges in list (including agent messages and tool calls)
        self.max_summary_size = 4000       # Max summary size before LLM compression
        self.summary_target_after_llm = 1000  # Target size after LLM summarization
        
        self.llm_summarization_count = 0 

        self.openai_client = None

        self.memory = self.initialize_session_memory()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=api_key)
            except Exception:
                self.openai_client = None
        else:
            logger.warning("Memory Menager will not use openAI for summarization (No API KEY)")

        self.channal_logger: ChannelLogger = channel_logger
    
    def initialize_session_memory(self,) -> ConversationMemory:
        """Initialize simple conversation memory structure"""
        return {
            'running_messages': [],
            'all_messages': [],
            'summary': '',
        }
    
    def prepare_messages_for_agent(self) -> List['ChatCompletionMessageParam']:
        # Build messages for LLM
        messages: List['ChatCompletionMessageParam'] = []

        # Add all exchanges from the list
        messages.extend(self.memory['running_messages'])
        
        return messages

    def last_exchange(self) -> List['ChatCompletionMessageParam']:
        if len(self.memory['running_messages']) < 2:
            return []
        
        last_assistant_idx = None
        for i in range(len(self.memory['running_messages']) - 1, -1, -1):
            if self.memory['running_messages'][i]['role'] == 'assistant':
                last_assistant_idx = i
                break
        
        if last_assistant_idx is None:
            return []
            
        for i in range(last_assistant_idx - 1, -1, -1):
            if self.memory['running_messages'][i]['role'] == 'user':
                return [self.memory['running_messages'][i], self.memory['running_messages'][last_assistant_idx]]
            
        return []
    
    # def _generate_tool_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
    #     """Generate unique cache key for tool call"""
    #     # Create a deterministic hash from tool name and parameters
    #     params_json = json.dumps(parameters, sort_keys=True)
    #     hash_input = f"{tool_name}:{params_json}"
    #     return hashlib.md5(hash_input.encode()).hexdigest()
    
    # def add_tool_to_cache(self, tool_name: str, parameters: Dict[str, Any], 
    #                      result: str, llm_cache_duration: int) -> None:
    #     """Add tool result to cache with specified duration"""
    #     if llm_cache_duration <= 0:
    #         return  # Don't cache if duration is 0
            
    #     cache_key = self._generate_tool_cache_key(tool_name, parameters)
        
    #     call_id = f"call_cached_{uuid.uuid4().hex[:8]}"
        
    #     cache_entry = {
    #         'tool_name': tool_name,
    #         'parameters': parameters,
    #         'result': result,
    #         'remaining_duration': llm_cache_duration,
    #         'original_duration': llm_cache_duration,
    #         'call_id': call_id,
    #         'cached_at': time.time()
    #     }
        
    #     self.memory['tool_cache'][cache_key] = cache_entry
        
    #     self.channal_logger.log_to_memory(f"🗄️ Cached tool {tool_name} for {llm_cache_duration} exchanges")
    
    # # TODO check what this function is doing and what is cache all about., Why it is with memory?
    # def lookup_tool_in_cache(self, tool_name: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    #     """Look up tool result in cache and refresh duration if found"""
    #     cache_key = self._generate_tool_cache_key(tool_name, parameters)
        
    #     if cache_key in self.memory['tool_cache']:
    #         cache_entry = self.memory['tool_cache'][cache_key]
            
    #         # Refresh the duration to original value
    #         cache_entry['remaining_duration'] = cache_entry['original_duration']
            
    #         self.channal_logger.log_to_memory(f"♻️ Cache hit for {tool_name}, refreshed duration to {cache_entry['original_duration']}")
    #         return cache_entry
            
    #     return None
    
    # # TODO seems like this is used at the end of exchange, but why?
    # def _get_cached_tool_messages(self) -> List[Dict[str, Any]]:
    #     """Get all cached tool results as OpenAI messages"""
    #     tool_messages = []
        
    #     for cache_entry in self.memory['tool_cache'].values():
    #         if cache_entry['remaining_duration'] > 0:
    #             # Add assistant message with tool call
    #             assistant_message = {
    #                 "role": "assistant",
    #                 "content": None,
    #                 "tool_calls": [
    #                     {
    #                         "id": cache_entry['call_id'],
    #                         "type": "function",
    #                         "function": {
    #                             "name": cache_entry['tool_name'],
    #                             "arguments": json.dumps(cache_entry['parameters'])
    #                         }
    #                     }
    #                 ]
    #             }
                
    #             # Add tool result message
    #             tool_message = {
    #                 "role": "tool",
    #                 "tool_call_id": cache_entry['call_id'],
    #                 "name": cache_entry['tool_name'],
    #                 "content": cache_entry['result']
    #             }
                
    #             tool_messages.extend([assistant_message, tool_message])
        
    #     return tool_messages
    
    # def _cleanup_expired_cache(self) -> None:
    #     """Remove expired tool cache entries and decrement remaining durations at end of exchange"""
    #     expired_keys = []
        
    #     for cache_key, cache_entry in self.memory['tool_cache'].items():
    #         # Decrement duration for all cached tools at end of exchange
    #         cache_entry['remaining_duration'] -= 1
            
    #         if cache_entry['remaining_duration'] <= 0:
    #             expired_keys.append(cache_key)
        
    #     # Remove expired entries
    #     for key in expired_keys:
    #         removed_entry = self.memory['tool_cache'].pop(key)

    #         self.channal_logger.log_to_memory(f"🗑️ Expired cache for {removed_entry['tool_name']}")
    
    # def is_tool_already_in_current_messages(self, messages: List['ChatCompletionMessageParam'], tool_name: str, parameters: Dict[str, Any]) -> bool:
    #     """Check if tool with same parameters is already in current message list"""
    #     target_args = json.dumps(parameters, sort_keys=True)
        
    #     for message in messages:
    #         if message['role'] == 'assistant' and 'tool_calls' in message:
    #             for tool_call in message['tool_calls']:
    #                 if (tool_call['function']['name'] == tool_name and 
    #                     tool_call['function']['arguments'] == target_args):
    #                     return True
    #     return False
    
    # def _cache_proactive_tool_results(self, proactive_messages: List[Dict[str, Any]]) -> None:
    #     try:            
    #         # Process pairs of assistant + tool messages
    #         for i in range(0, len(proactive_messages), 2):
    #             if i + 1 < len(proactive_messages):
    #                 assistant_msg = proactive_messages[i]
    #                 tool_msg = proactive_messages[i + 1]
                    
    #                 if (assistant_msg.get('role') == 'assistant' and 
    #                     tool_msg.get('role') == 'tool' and
    #                     assistant_msg.get('tool_calls')):
                        
    #                     tool_call = assistant_msg['tool_calls'][0]
    #                     tool_name = tool_call['function']['name']
    #                     parameters = json.loads(tool_call['function']['arguments'])
    #                     result = tool_msg['content']
                        
    #                     # Get cache duration from result JSON (default 0 if not present)
    #                     llm_cache_duration = 0
    #                     try:
    #                         result_json = json.loads(result) if isinstance(result, str) else result
    #                         if isinstance(result_json, dict):
    #                             llm_cache_duration = result_json.get('llm_cache_duration', 0)
    #                     except:
    #                         pass
                        
    #                     if llm_cache_duration > 0:
    #                         self.add_tool_to_cache(tool_name, parameters, result, llm_cache_duration)
                            
    #     except Exception as e:
    #         self.channal_logger.log_to_memory(f"❌ Failed to cache proactive tools: {str(e)}")
    
    
        # self._cleanup_expired_cache()
    def finalize_current_cycle(self, messages: List['ChatCompletionMessageParam']) -> None:
        self.memory['running_messages'] = messages

        total_size = sum(len(str(msg)) for msg in messages)

        # Sumarization logic
        while len(messages) > self.max_exchanges or total_size > self.max_summary_size:
            messages_to_summarize = messages[:self.max_exchanges // 2]
            remaining_messages = messages[self.max_exchanges // 2:]

            summary_text = ""
            for msg in messages_to_summarize:
                role = msg['role']
                summary_text += f"{role}: {self._clean_markdown(chat_completion_to_content_str(msg))}\n"

            if self.memory['summary']:
                summary_text = f"{self.memory['summary']}\n\n{summary_text}"

            compressed_summary = self._summarize_text(summary_text, self.summary_target_after_llm)
            self.memory['summary'] = compressed_summary

            self.memory['running_messages'] = remaining_messages
            messages = remaining_messages

            total_size = sum(len(str(msg)) for msg in messages)

            self.llm_summarization_count += 1    
        
        
    
    def _summarize_text(self, text: str, target_size: int) -> str:
        if self.openai_client is None:
            return textwrap.shorten(text, width=target_size)
        
        try:
            # Calculate approximate character count (rough estimate: 1 byte per char for English)
            target_chars = int(target_size * 0.8)  # Conservative estimate
            
            # Use OpenAI for intelligent summarization
            prompt = f"Summarize the following text to approximately {target_chars} characters while preserving key information. Be concise:\n\n{text}"
            
            response = self.openai_client.chat.completions.create( 
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates very concise summaries. Be extremely brief."},
                    {"role": "user", "content": prompt}
                ],
                # TODO, add param for TEMP of summary
                temperature=0.0,  
                max_completion_tokens=int(target_chars / 2),
            ) 

            if response.choices[0].message.content is None:
                logger.error("Empty response from OpenAI summarization")
                return textwrap.shorten(text, width=target_size)
                        
            summary = response.choices[0].message.content.strip()
            
            summary = textwrap.shorten(summary, width=target_size)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            return textwrap.shorten(text, width=target_size)
    
    def _clean_markdown(self, text: str) -> str:
        html = markdown.markdown(text)
        return BeautifulSoup(html, features='html.parser').get_text()
