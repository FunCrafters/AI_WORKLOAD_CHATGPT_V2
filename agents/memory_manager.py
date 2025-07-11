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
from typing import Dict, List, Any, Optional
from venv import logger
from openai.types.chat import ChatCompletionMessageParam
import markdown
from bs4 import BeautifulSoup
from channel_logger import ChannelLogger
import openai

# TODO test diffrent summarization heuristics
# TODO split into MemoryMenger, CacheManager and MessageInjector 
class MemoryManager:
    def __init__(self, channel_logger: 'ChannelLogger'):
        self.max_exchanges = 10            # Max exchanges in list
        self.large_answer_threshold = 750  # Threshold for long answers (bytes)
        self.summary_target_size = 500     # Target size for answer summarization
        self.max_summary_size = 4000       # Max summary size before LLM compression
        self.summary_target_after_llm = 3000  # Target size after LLM summarization
        
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
    
    def initialize_session_memory(self,) -> Dict[str, Any]:
        """Initialize simple conversation memory structure"""
        # TODO REPLACE WITH MEMORY STATE / STH LIKE THIS.
        return {
            'exchanges': [],
            'summary': '', 
            'current_cycle': {
                'user_question': "",
                'agent_messages': [],
                'final_answer': None
            },
            'tool_cache': {},
            'screen_injection_done': False  # Track if screen injection was done
        }
    
    def prepare_messages_for_agent(self, user_message: str) -> List['ChatCompletionMessageParam']:
        self.memory['current_cycle']['user_question'] = user_message
        
        # Build messages for LLM
        messages = []
        
        # Add summary if exists (as user message describing history)
        if self.memory.get('summary'):
            messages.append({
                "role": "user",
                "content": f"Previous conversation summary: {self.memory['summary']}"
            })
        
        # Add all exchanges from the list
        for exchange in self.memory.get('exchanges', []):
            messages.append({
                "role": "user",
                "content": exchange['question']
            })
            messages.append({
                "role": "assistant",
                "content": exchange['answer']
            })
        
        # Add cached tool messages (if any are still valid)
        cached_tool_messages = self._get_cached_tool_messages()
        if cached_tool_messages:
            messages.extend(cached_tool_messages)
        
        return messages
    
    def _generate_tool_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate unique cache key for tool call"""
        # Create a deterministic hash from tool name and parameters
        params_json = json.dumps(parameters, sort_keys=True)
        hash_input = f"{tool_name}:{params_json}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def add_tool_to_cache(self, tool_name: str, parameters: Dict[str, Any], 
                         result: str, llm_cache_duration: int) -> None:
        """Add tool result to cache with specified duration"""
        if llm_cache_duration <= 0:
            return  # Don't cache if duration is 0
            
        cache_key = self._generate_tool_cache_key(tool_name, parameters)
        
        call_id = f"call_cached_{uuid.uuid4().hex[:8]}"
        
        cache_entry = {
            'tool_name': tool_name,
            'parameters': parameters,
            'result': result,
            'remaining_duration': llm_cache_duration,
            'original_duration': llm_cache_duration,
            'call_id': call_id,
            'cached_at': time.time()
        }
        
        self.memory['tool_cache'][cache_key] = cache_entry
        
        self.channal_logger.log_to_memory(f"🗄️ Cached tool {tool_name} for {llm_cache_duration} exchanges")
    
    # TODO check what this function is doing and what is cache all about., Why it is with memory?
    def lookup_tool_in_cache(self, tool_name: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Look up tool result in cache and refresh duration if found"""
        cache_key = self._generate_tool_cache_key(tool_name, parameters)
        
        if cache_key in self.memory['tool_cache']:
            cache_entry = self.memory['tool_cache'][cache_key]
            
            # Refresh the duration to original value
            cache_entry['remaining_duration'] = cache_entry['original_duration']
            
            self.channal_logger.log_to_memory(f"♻️ Cache hit for {tool_name}, refreshed duration to {cache_entry['original_duration']}")
            return cache_entry
            
        return None
    
    # TODO seems like this is used at the end of exchange, but why?
    def _get_cached_tool_messages(self) -> List[Dict[str, Any]]:
        """Get all cached tool results as OpenAI messages"""
        tool_messages = []
        
        for cache_entry in self.memory['tool_cache'].values():
            if cache_entry['remaining_duration'] > 0:
                # Add assistant message with tool call
                assistant_message = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": cache_entry['call_id'],
                            "type": "function",
                            "function": {
                                "name": cache_entry['tool_name'],
                                "arguments": json.dumps(cache_entry['parameters'])
                            }
                        }
                    ]
                }
                
                # Add tool result message
                tool_message = {
                    "role": "tool",
                    "tool_call_id": cache_entry['call_id'],
                    "name": cache_entry['tool_name'],
                    "content": cache_entry['result']
                }
                
                tool_messages.extend([assistant_message, tool_message])
        
        return tool_messages
    
    def _cleanup_expired_cache(self, channel_logger=None) -> None:
        """Remove expired tool cache entries and decrement remaining durations at end of exchange"""
        expired_keys = []
        
        for cache_key, cache_entry in self.memory['tool_cache'].items():
            # Decrement duration for all cached tools at end of exchange
            cache_entry['remaining_duration'] -= 1
            
            if cache_entry['remaining_duration'] <= 0:
                expired_keys.append(cache_key)
        
        # Remove expired entries
        for key in expired_keys:
            removed_entry = self.memory['tool_cache'].pop(key)
            if channel_logger:
                self.channal_logger.log_to_memory(f"🗑️ Expired cache for {removed_entry['tool_name']}")
    
    def is_tool_already_in_current_messages(self, messages: List['ChatCompletionMessageParam'], tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Check if tool with same parameters is already in current message list"""
        target_args = json.dumps(parameters, sort_keys=True)
        
        for message in messages:
            if message['role'] == 'assistant' and 'tool_calls' in message:
                for tool_call in message['tool_calls']:
                    if (tool_call['function']['name'] == tool_name and 
                        tool_call['function']['arguments'] == target_args):
                        return True
        return False
    
    def inject_screen_context(self, json_data: Dict[str, Any]) -> List['ChatCompletionMessageParam']:
        """Inject screen context and proactive tools at session start"""
        
        # Only inject once per session and only if we have json_data
        if self.memory.get('screen_injection_done') or not json_data:
            return []
        
        try:
            from proactive_tool_executor import get_proactive_tool_messages
            proactive_messages, prompt_injection = get_proactive_tool_messages(json_data)
            
            injection_messages = []
            
            # Add screen context as assistant message if we have prompt injection
            if prompt_injection:
                injection_messages.append({
                    "role": "assistant", 
                    "content": f"I can see you're currently on a specific screen. Let me provide context: {prompt_injection}"
                })
                
                self.channal_logger.log_to_memory(f"🎯 Injected screen context: {len(prompt_injection)} chars")
            
            # Add proactive tool results and cache them
            if proactive_messages:
                injection_messages.extend(proactive_messages)
                
                # Cache the tool results
                self._cache_proactive_tool_results(proactive_messages)
                
                self.channal_logger.log_to_memory(f"🔧 Injected {len(proactive_messages)} proactive tool messages")
            
            # Mark injection as done
            self.memory['screen_injection_done'] = True
            
            return injection_messages
            
        except Exception as e:
            self.channal_logger.log_to_memory(f"❌ Screen injection failed: {str(e)}")
            return []
    
    def _cache_proactive_tool_results(self, proactive_messages: List[Dict[str, Any]]) -> None:
        try:            
            # Process pairs of assistant + tool messages
            for i in range(0, len(proactive_messages), 2):
                if i + 1 < len(proactive_messages):
                    assistant_msg = proactive_messages[i]
                    tool_msg = proactive_messages[i + 1]
                    
                    if (assistant_msg.get('role') == 'assistant' and 
                        tool_msg.get('role') == 'tool' and
                        assistant_msg.get('tool_calls')):
                        
                        tool_call = assistant_msg['tool_calls'][0]
                        tool_name = tool_call['function']['name']
                        parameters = json.loads(tool_call['function']['arguments'])
                        result = tool_msg['content']
                        
                        # Get cache duration from result JSON (default 0 if not present)
                        llm_cache_duration = 0
                        try:
                            result_json = json.loads(result) if isinstance(result, str) else result
                            if isinstance(result_json, dict):
                                llm_cache_duration = result_json.get('llm_cache_duration', 0)
                        except:
                            pass
                        
                        if llm_cache_duration > 0:
                            self.add_tool_to_cache(tool_name, parameters, result, llm_cache_duration)
                            
        except Exception as e:
            self.channal_logger.log_to_memory(f"❌ Failed to cache proactive tools: {str(e)}")
    
    def finalize_current_cycle(self, user_message: str, final_answer: str, channel_logger=None) -> None:
        """Update memory with final exchange results"""        
        # Prepare the current exchange
        current_exchange = {
            'question': user_message,
            'answer': final_answer
        }
        
        # Add to exchanges list, managing max_exchanges
        self.memory['exchanges'].insert(0, current_exchange)
        if len(self.memory['exchanges']) > self.max_exchanges:
            self.memory['exchanges'] = self.memory['exchanges'][:self.max_exchanges]
        
        # Reset current cycle
        self.memory['current_cycle'] = {
            'user_question': "",
            'agent_messages': [],
            'final_answer': None
        }
        
        self._cleanup_expired_cache(channel_logger)


        while len(self.memory['exchanges']) > self.max_exchanges:
            # Move oldest exchange to summary
            oldest = self.memory['exchanges'].pop(0)
            summary_entry = f"Question: {oldest['question']}. Answer: {oldest['answer']}"
            
            # Add to summary
            if self.memory['summary']:
                self.memory['summary'] += f"\n\n{summary_entry}"
            else:
                self.memory['summary'] = summary_entry
             
            # Check summary size after EACH addition
            if len(self.memory['summary'].encode('utf-8')) > self.max_summary_size:
                # Compress immediately
                old_size = len(self.memory['summary'].encode('utf-8'))
                compressed_summary = self._summarize_text(self.memory['summary'], self.summary_target_after_llm)
                self.memory['summary'] = compressed_summary
                new_size = len(compressed_summary.encode('utf-8'))
                self.llm_summarization_count += 1
 
        # STEP 4: Final check if summary is still too long (> 4000 bytes)
        if len(self.memory['summary'].encode('utf-8')) > self.max_summary_size:
            # Use LLM to compress summary
            old_size = len(self.memory['summary'].encode('utf-8'))
            compressed_summary = self._summarize_text(self.memory['summary'], self.summary_target_after_llm)
            self.memory['summary'] = compressed_summary
            new_size = len(compressed_summary.encode('utf-8'))
            self.llm_summarization_count += 1  # Track LLM usage

        # Clear current cycle
        self.memory['current_cycle'] = {
            'user_question': "",
            'agent_messages': [],
            'final_answer': None
        }
    
    def _summarize_text(self, text: str, target_size: int) -> str:
        """Summarize text to target size (in bytes) using LLM or simple truncation"""
        
        if self.openai_client is None:
            return textwrap.shorten(text, width=target_size)
        
        try:
            # Calculate approximate character count (rough estimate: 1 byte per char for English)
            target_chars = int(target_size * 0.8)  # Conservative estimate
            
            # Use OpenAI for intelligent summarization
            prompt = f"Summarize the following text to approximately {target_chars} characters (aiming for {target_size} bytes) while preserving key information. Be concise:\n\n{text}"
            
            response = self.openai_client.chat.completions.create( 
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates very concise summaries. Be extremely brief."},
                    {"role": "user", "content": prompt}
                ],
                # TODO, for summarization we want more deterministic output - 0 will result in most probable output.
                temperature=0.3,  
                max_tokens=int(target_chars / 2),
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
