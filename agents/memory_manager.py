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
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from venv import logger

from channel_logger import ChannelLogger
from session import Session
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# TODO test diffrent summarization heuristics
class MemoryManager:
    """Simple memory manager with straightforward rules"""
    
    def __init__(self):
        # Simple configuration
        self.max_exchanges = 10            # Max exchanges in list
        self.large_answer_threshold = 750  # Threshold for long answers (bytes)
        self.summary_target_size = 500     # Target size for answer summarization
        self.max_summary_size = 4000       # Max summary size before LLM compression
        self.summary_target_after_llm = 3000  # Target size after LLM summarization
        
        # Statistics tracking
        self.llm_summarization_count = 0  # Track how many times LLM was used for compression
        
        # OpenAI client for summaries
        self.openai_client = None
        self.openai_enabled = False
        
        # Initialize OpenAI client for summaries
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and api_key != 'your_openai_api_key_here':
                try:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    self.openai_enabled = True
                except Exception:
                    self.openai_enabled = False
        
        # TODO can be removed if phantom call to logger is removed.
        # For logging (set by agent system)
        self.client = None
        self.session_id = None
        self.action_id = None

    
    def initialize_session_memory(self,) -> Dict[str, Any]:
        """Initialize simple conversation memory structure"""
        # TODO REPLACE WITH MEMORY STATE / STH LIKE THIS.
        return {
            'exchanges': [],           # List of Q&A exchanges (max 10)
            'summary': '',            # Text summary of old conversations
            'current_cycle': {
                'user_question': "",
                'agent_messages': [],
                'final_answer': None
            },
            'tool_cache': {},         # Tool results cache {tool_key: cache_entry}
            'screen_injection_done': False  # Track if screen injection was done
        }
    
    def prepare_messages_for_agent(self, memory: Dict[str, Any], user_message: str) -> List[Dict[str, str]]:
        memory['current_cycle']['user_question'] = user_message
        
        # Build messages for LLM
        messages = []
        
        # Add summary if exists (as user message describing history)
        if memory.get('summary'):
            messages.append({
                "role": "user",
                "content": f"Previous conversation summary: {memory['summary']}"
            })
        
        # Add all exchanges from the list
        for exchange in memory.get('exchanges', []):
            messages.append({
                "role": "user",
                "content": exchange['question']
            })
            messages.append({
                "role": "assistant",
                "content": exchange['answer']
            })
        
        # Add cached tool messages (if any are still valid)
        cached_tool_messages = self._get_cached_tool_messages(memory)
        if cached_tool_messages:
            messages.extend(cached_tool_messages)
        
        return messages
    
    def _generate_tool_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate unique cache key for tool call"""
        # Create a deterministic hash from tool name and parameters
        params_json = json.dumps(parameters, sort_keys=True)
        hash_input = f"{tool_name}:{params_json}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def add_tool_to_cache(self, memory: Dict[str, Any], tool_name: str, parameters: Dict[str, Any], 
                         result: str, llm_cache_duration: int, channel_logger=None) -> None:
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
        
        memory['tool_cache'][cache_key] = cache_entry
        
        if channel_logger:
            self._add_to_session_log(memory, f"🗄️ Cached tool {tool_name} for {llm_cache_duration} exchanges")
    
    # TODO check what this function is doing and what is cache all about., Why it is with memory?
    def lookup_tool_in_cache(self, memory: Dict[str, Any], tool_name: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Look up tool result in cache and refresh duration if found"""
        cache_key = self._generate_tool_cache_key(tool_name, parameters)
        
        if cache_key in memory['tool_cache']:
            cache_entry = memory['tool_cache'][cache_key]
            
            # Refresh the duration to original value
            cache_entry['remaining_duration'] = cache_entry['original_duration']
            
            self._add_to_session_log(memory, f"♻️ Cache hit for {tool_name}, refreshed duration to {cache_entry['original_duration']}")
            return cache_entry
            
        return None
    
    # TODO seems like this is used at the end of exchange, but why?
    def _get_cached_tool_messages(self, memory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all cached tool results as OpenAI messages"""
        tool_messages = []
        
        for cache_entry in memory['tool_cache'].values():
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
    
    def _cleanup_expired_cache(self, memory: Dict[str, Any], channel_logger=None) -> None:
        """Remove expired tool cache entries and decrement remaining durations at end of exchange"""
        expired_keys = []
        
        for cache_key, cache_entry in memory['tool_cache'].items():
            # Decrement duration for all cached tools at end of exchange
            cache_entry['remaining_duration'] -= 1
            
            if cache_entry['remaining_duration'] <= 0:
                expired_keys.append(cache_key)
        
        # Remove expired entries
        for key in expired_keys:
            removed_entry = memory['tool_cache'].pop(key)
            if channel_logger:
                self._add_to_session_log(memory, f"🗑️ Expired cache for {removed_entry['tool_name']}")
    
    def is_tool_already_in_current_messages(self, messages: List[Dict[str, Any]], tool_name: str, parameters: Dict[str, Any]) -> bool:
        """Check if tool with same parameters is already in current message list"""
        target_args = json.dumps(parameters, sort_keys=True)
        
        for message in messages:
            if message.get('role') == 'assistant' and message.get('tool_calls'):
                for tool_call in message['tool_calls']:
                    if (tool_call['function']['name'] == tool_name and 
                        tool_call['function']['arguments'] == target_args):
                        return True
        return False
    
    def inject_screen_context(self, memory: Dict[str, Any], json_data: Dict[str, Any], channel_logger=None) -> List[Dict[str, Any]]:
        """Inject screen context and proactive tools at session start"""
        
        # Only inject once per session and only if we have json_data
        if memory.get('screen_injection_done') or not json_data:
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
                
                if channel_logger:
                    self._add_to_session_log(memory, f"🎯 Injected screen context: {len(prompt_injection)} chars")
            
            # Add proactive tool results and cache them
            if proactive_messages:
                injection_messages.extend(proactive_messages)
                
                # Cache the tool results
                self._cache_proactive_tool_results(memory, proactive_messages, channel_logger)
                
                if channel_logger:
                    self._add_to_session_log(memory, f"🔧 Injected {len(proactive_messages)} proactive tool messages")
            
            # Mark injection as done
            memory['screen_injection_done'] = True
            
            return injection_messages
            
        except Exception as e:
            if channel_logger:
                self._add_to_session_log(memory, f"❌ Screen injection failed: {str(e)}")
            return []
    
    def _cache_proactive_tool_results(self, memory: Dict[str, Any], proactive_messages: List[Dict[str, Any]], channel_logger=None) -> None:
        """Cache proactive tool results based on their llm_cache_duration"""
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
                            self.add_tool_to_cache(memory, tool_name, parameters, result, llm_cache_duration, channel_logger)
                            
        except Exception as e:
            if channel_logger:
                self._add_to_session_log(memory, f"❌ Failed to cache proactive tools: {str(e)}")
    
    def finalize_current_cycle(self, memory: Dict[str, Any], user_message: str, final_answer: str, channel_logger=None) -> None:
        """Update memory with final exchange results"""        
        # Prepare the current exchange
        current_exchange = {
            'question': user_message,
            'answer': final_answer
        }
        
        # Add to exchanges list, managing max_exchanges
        memory['exchanges'].insert(0, current_exchange)
        if len(memory['exchanges']) > self.max_exchanges:
            memory['exchanges'] = memory['exchanges'][:self.max_exchanges]
        
        # Reset current cycle
        memory['current_cycle'] = {
            'user_question': "",
            'agent_messages': [],
            'final_answer': None
        }
        
        self._cleanup_expired_cache(memory, channel_logger)
    
    def _summarize_text(self, text: str, target_size: int) -> str:
        """Summarize text to target size (in bytes) using LLM or simple truncation"""
        
        if not self.openai_enabled:
            # Fallback: simple truncation
            if len(text.encode('utf-8')) <= target_size:
                return text
            # Truncate safely without breaking unicode
            return textwrap.shorten(text, width=target_size)
        
        try:
            # Calculate approximate character count (rough estimate: 1 byte per char for English)
            target_chars = int(target_size * 0.8)  # Conservative estimate
            
            # Use OpenAI for intelligent summarization
            prompt = f"Summarize the following text to approximately {target_chars} characters (aiming for {target_size} bytes) while preserving key information. Be concise:\n\n{text}"
            
            response = self.openai_client.chat.completions.create( # type: ignore
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates very concise summaries. Be extremely brief."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=int(target_chars / 2)  # More conservative token limit
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
    
    # TODO this seems like channal logger, but it is written by hand instead 
    # TODO [ChannelLogger](https://github.com/FunCrafters/AI_WORKLOAD_CHATGPT_V2/blob/fb8e3b0162d06aee67f0893f4233fa8e5d85a5b2/channel_logger.py#L66) 
    def _log_to_memory_channel(self, content: str) -> None:
        """Log content to Memory channel (5) - only called by _log_final_memory_state"""
        try:
            if self.client and self.session_id:
                from workload_tools import create_response, send_response
                response = create_response(5, content, self.session_id, f"memory_{int(time.time())}")
                send_response(self.client, response, self.session_id, 5, f"memory_{int(time.time())}")
        except Exception:
            logger.info("Failed to log to memory channel")
            pass  # Silent fail - logging is not critical OwO?
    
    def _add_to_session_log(self, memory: Dict[str, Any], content: str) -> None:
        """Add log entry to session logs (collected until final state)"""
        if 'session_logs' not in memory:
            memory['session_logs'] = []
        memory['session_logs'].append(content)
    
    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text for cleaner display"""
        # TODO Strip with library instead
        import re
        
        # Handle None or non-string input
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove bold (**text** or __text__)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        
        # Remove italic (*text* or _text_)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # Remove headers (# Header)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # Remove code blocks (```code```)
        text = re.sub(r'```[^`]+```', '', text)
        
        # Remove inline code (`code`)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove bullet points
        text = re.sub(r'^[\*\-]\s+', '', text, flags=re.MULTILINE)
        
        # Remove numbered lists
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Clean up multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _log_final_memory_state(self, session: 'Session', channel_logger: 'ChannelLogger') -> None:
        """Log final memory state showing what agent would receive"""
        try:
            # Get the current user message
            memory = session.conversation_memory if session.conversation_memory else self.initialize_session_memory()
            current_user_message = memory['current_cycle'].get('user_question', 'No current message')
            
            # Get memory messages as agent would receive them
            memory_messages = self.prepare_messages_for_agent(session.get_memory(), current_user_message)
            
            # Calculate statistics
            exchanges = memory.get('exchanges', [])
            summary = memory.get('summary', '')
            llm_summarizations = getattr(self, 'llm_summarization_count', 0)  # Track LLM usage
            
            # Format memory state for display
            memory_log = "=== MEMORY STATE ===\n"
            memory_log += f"Session: {session.session_id} | "
            memory_log += f"Exchanges: {len(exchanges)} | "
            memory_log += f"Summary: {len(summary.encode('utf-8'))} bytes | "
            memory_log += f"LLM compressions: {llm_summarizations}\n\n"
            
            # Show function cache state
            tool_cache = memory.get('tool_cache', {})
            if tool_cache:
                memory_log += "=== FUNCTION CACHE STATE ===\n"
                memory_log += f"Cached functions: {len(tool_cache)}\n"
                for cache_key, cache_entry in tool_cache.items():
                    tool_name = cache_entry.get('tool_name', 'unknown')
                    remaining = cache_entry.get('remaining_duration', 0)
                    original = cache_entry.get('original_duration', 0)
                    params = cache_entry.get('parameters', {})
                    
                    params_str = str(params)
                    params_str = textwrap.shorten(params_str, width=50)
                    
                    memory_log += f"  • {tool_name}({params_str}): {remaining}/{original} exchanges remaining\n"
                memory_log += "\n"
            else:
                memory_log += "=== FUNCTION CACHE STATE ===\n"
                memory_log += "No cached functions\n\n"
            
            # Show full summary if exists
            if summary:
                memory_log += "=== FULL SUMMARY ===\n"
                memory_log += self._clean_markdown(summary) + "\n\n"
            
            # Add session logs to memory log
            session_logs = memory.get('session_logs', [])
            if session_logs:
                memory_log += "=== SESSION ACTIVITY ===\n"
                for log_entry in session_logs:
                    memory_log += f"{log_entry}\n"
                memory_log += "\n"
            
            # Show what agent receives
            if memory_messages:
                memory_log += f"=== AGENT RECEIVES ({len(memory_messages)} messages) ===\n"
                for idx, msg in enumerate(memory_messages, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content') or ''  # Handle None content
                    
                    content = self._clean_markdown(content)

                    content = textwrap.shorten(content, width=120)
                    
                    memory_log += f"[{idx}] {role.upper()}: {content}\n"
            else:
                memory_log += "=== NO MEMORY CONTEXT ===\n"
            
            # Clear session logs after sending to avoid accumulation
            memory['session_logs'] = []
            
            channel_logger.log_to_memory(memory_log)
            
        except Exception as e:
            channel_logger.log_to_memory(f"❌ Error logging final memory state: {str(e)}")