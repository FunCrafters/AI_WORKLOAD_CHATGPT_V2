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
from typing import Dict, List, Any, Optional, Tuple

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class MemoryManager:
    """Simple memory manager with straightforward rules"""
    
    def __init__(self):
        # Simple configuration
        self.max_exchanges = 10          # Max exchanges in list
        self.large_answer_threshold = 750  # Threshold for long answers (bytes)
        self.summary_target_size = 500    # Target size for answer summarization
        self.max_summary_size = 4000      # Max summary size before LLM compression
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
        
        # For logging (set by agent system)
        self.client = None
        self.session_id = None
        self.action_id = None
    
    def initialize_session_memory(self, session: Dict[str, Any]) -> None:
        """Initialize simple conversation memory structure"""
        if 'conversation_memory' not in session:
            session['conversation_memory'] = {
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
    
    def prepare_messages_for_agent(self, session: Dict[str, Any], user_message: str) -> List[Dict[str, str]]:
        """Prepare conversation history messages for agent"""
        
        # Initialize memory if needed
        self.initialize_session_memory(session)
        
        # Store current user message
        memory = session['conversation_memory']
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
        
        # Note: Cache cleanup moved to finalize_current_cycle to ensure
        # tools are available for their full exchange duration
        
        # Add cached tool messages (if any are still valid)
        cached_tool_messages = self.get_cached_tool_messages(session)
        if cached_tool_messages:
            messages.extend(cached_tool_messages)
        
        return messages
    
    def _generate_tool_cache_key(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate unique cache key for tool call"""
        # Create a deterministic hash from tool name and parameters
        params_json = json.dumps(parameters, sort_keys=True)
        hash_input = f"{tool_name}:{params_json}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def add_tool_to_cache(self, session: Dict[str, Any], tool_name: str, parameters: Dict[str, Any], 
                         result: str, llm_cache_duration: int, channel_logger=None) -> None:
        """Add tool result to cache with specified duration"""
        if llm_cache_duration <= 0:
            return  # Don't cache if duration is 0
            
        memory = session['conversation_memory']
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
            self._add_to_session_log(session, f"🗄️ Cached tool {tool_name} for {llm_cache_duration} exchanges")
    
    def lookup_tool_in_cache(self, session: Dict[str, Any], tool_name: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Look up tool result in cache and refresh duration if found"""
        memory = session['conversation_memory']
        cache_key = self._generate_tool_cache_key(tool_name, parameters)
        
        if cache_key in memory['tool_cache']:
            cache_entry = memory['tool_cache'][cache_key]
            
            # Refresh the duration to original value
            cache_entry['remaining_duration'] = cache_entry['original_duration']
            
            self._add_to_session_log(session, f"♻️ Cache hit for {tool_name}, refreshed duration to {cache_entry['original_duration']}")
            return cache_entry
            
        return None
    
    def get_cached_tool_messages(self, session: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all cached tool results as OpenAI messages"""
        memory = session['conversation_memory']
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
    
    def cleanup_expired_cache(self, session: Dict[str, Any], channel_logger=None) -> None:
        """Remove expired tool cache entries and decrement remaining durations at end of exchange"""
        memory = session['conversation_memory']
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
                self._add_to_session_log(session, f"🗑️ Expired cache for {removed_entry['tool_name']}")
    
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
    
    def inject_screen_context(self, session: Dict[str, Any], json_data: Dict[str, Any], channel_logger=None) -> List[Dict[str, Any]]:
        """Inject screen context and proactive tools at session start"""
        memory = session['conversation_memory']
        
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
                    self._add_to_session_log(session, f"🎯 Injected screen context: {len(prompt_injection)} chars")
            
            # Add proactive tool results and cache them
            if proactive_messages:
                injection_messages.extend(proactive_messages)
                
                # Cache the tool results
                self._cache_proactive_tool_results(session, proactive_messages, channel_logger)
                
                if channel_logger:
                    self._add_to_session_log(session, f"🔧 Injected {len(proactive_messages)} proactive tool messages")
            
            # Mark injection as done
            memory['screen_injection_done'] = True
            
            return injection_messages
            
        except Exception as e:
            if channel_logger:
                self._add_to_session_log(session, f"❌ Screen injection failed: {str(e)}")
            return []
    
    def _cache_proactive_tool_results(self, session: Dict[str, Any], proactive_messages: List[Dict[str, Any]], channel_logger=None) -> None:
        """Cache proactive tool results based on their llm_cache_duration"""
        try:
            from tools_functions import available_all_tools
            
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
                            self.add_tool_to_cache(session, tool_name, parameters, result, llm_cache_duration, channel_logger)
                            
        except Exception as e:
            if channel_logger:
                self._add_to_session_log(session, f"❌ Failed to cache proactive tools: {str(e)}")
    
    def finalize_current_cycle(self, session: Dict[str, Any], user_question: str, final_answer: str, channel_logger=None) -> None:
        """Finalize current cycle with simple memory management"""
        
        memory = session['conversation_memory']
        
        # STEP 1: Check if last exchange has long answer that needs summarization
        if memory['exchanges']:
            last_exchange = memory['exchanges'][-1]
            if len(last_exchange['answer'].encode('utf-8')) > self.large_answer_threshold:
                # Summarize the last answer to target size
                old_size = len(last_exchange['answer'].encode('utf-8'))
                summarized_answer = self._summarize_text(last_exchange['answer'], self.summary_target_size)
                last_exchange['answer'] = summarized_answer
                new_size = len(summarized_answer.encode('utf-8'))
                if channel_logger:
                    self._add_to_session_log(session, f"📝 Summarized last answer from {old_size} to {new_size} bytes")
        
        # STEP 2: Create new exchange and add to list
        new_exchange = {
            'question': user_question,
            'answer': final_answer,
            'timestamp': time.time()
        }
        memory['exchanges'].append(new_exchange)
        if channel_logger:
            self._add_to_session_log(session, f"➕ Added new exchange to list (now {len(memory['exchanges'])} exchanges)")
        
        # STEP 3: Check if we have too many exchanges (> 10)
        while len(memory['exchanges']) > self.max_exchanges:
            # Move oldest exchange to summary
            oldest = memory['exchanges'].pop(0)
            summary_entry = f"Question: {oldest['question']}. Answer: {oldest['answer']}"
            
            # Add to summary
            if memory['summary']:
                memory['summary'] += f"\n\n{summary_entry}"
            else:
                memory['summary'] = summary_entry
            
            if channel_logger:
                self._add_to_session_log(session, f"📚 Moved oldest exchange to summary (exchanges: {len(memory['exchanges'])})")
            
            # Check summary size after EACH addition
            if len(memory['summary'].encode('utf-8')) > self.max_summary_size:
                # Compress immediately
                old_size = len(memory['summary'].encode('utf-8'))
                compressed_summary = self._summarize_text(memory['summary'], self.summary_target_after_llm)
                memory['summary'] = compressed_summary
                new_size = len(compressed_summary.encode('utf-8'))
                self.llm_summarization_count += 1
                if channel_logger:
                    self._add_to_session_log(session, f"🗜️ Compressed summary from {old_size} to {new_size} bytes using LLM (#{self.llm_summarization_count})")
        
        # STEP 4: Final check if summary is still too long (> 4000 bytes)
        if len(memory['summary'].encode('utf-8')) > self.max_summary_size:
            # Use LLM to compress summary
            old_size = len(memory['summary'].encode('utf-8'))
            compressed_summary = self._summarize_text(memory['summary'], self.summary_target_after_llm)
            memory['summary'] = compressed_summary
            new_size = len(compressed_summary.encode('utf-8'))
            self.llm_summarization_count += 1  # Track LLM usage
            if channel_logger:
                self._add_to_session_log(session, f"🗜️ Compressed summary from {old_size} to {new_size} bytes using LLM (#{self.llm_summarization_count})")
        
        # Log final memory state to Memory channel if channel_logger is provided
        if channel_logger:
            self._log_final_memory_state(session, channel_logger)
        
        # Clean up expired tool cache entries at end of exchange
        self.cleanup_expired_cache(session, channel_logger)
        
        # Clear current cycle
        session['conversation_memory']['current_cycle'] = {
            'user_question': "",
            'agent_messages': [],
            'final_answer': None
        }
    
    def _summarize_text(self, text: str, target_size: int) -> str:
        """Summarize text to target size (in bytes) using LLM or simple truncation"""
        
        if not self.openai_enabled:
            # Fallback: simple truncation
            text_bytes = text.encode('utf-8')
            if len(text_bytes) <= target_size:
                return text
            # Truncate safely without breaking unicode
            truncated = text_bytes[:target_size].decode('utf-8', errors='ignore')
            return truncated + "..."
        
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
                temperature=0.3,
                max_tokens=int(target_chars / 2)  # More conservative token limit
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Verify the result is not too large
            if len(summary.encode('utf-8')) > target_size:
                # If still too large, truncate
                summary_bytes = summary.encode('utf-8')[:target_size]
                summary = summary_bytes.decode('utf-8', errors='ignore') + "..."
            
            # Note: summarization logs handled in finalize_current_cycle
            return summary
            
        except Exception as e:
            # Note: summarization logs handled in finalize_current_cycle
            # Fallback to truncation
            text_bytes = text.encode('utf-8')
            if len(text_bytes) <= target_size:
                return text
            truncated = text_bytes[:target_size].decode('utf-8', errors='ignore')
            return truncated + "..."
    
    def _log_to_memory_channel(self, content: str) -> None:
        """Log content to Memory channel (5) - only called by _log_final_memory_state"""
        try:
            if self.client and self.session_id:
                from workload_tools import create_response, send_response
                response = create_response(5, content, self.session_id, f"memory_{int(time.time())}")
                send_response(self.client, response, self.session_id, 5, f"memory_{int(time.time())}")
        except Exception:
            pass  # Silent fail - logging is not critical
    
    def _add_to_session_log(self, session: Dict[str, Any], content: str) -> None:
        """Add log entry to session logs (collected until final state)"""
        memory = session['conversation_memory']
        if 'session_logs' not in memory:
            memory['session_logs'] = []
        memory['session_logs'].append(content)
    
    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text for cleaner display"""
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
    
    def _log_final_memory_state(self, session: Dict[str, Any], channel_logger):
        """Log final memory state showing what agent would receive"""
        try:
            # Get the current user message
            memory = session['conversation_memory']
            current_user_message = memory['current_cycle'].get('user_question', 'No current message')
            
            # Get memory messages as agent would receive them
            memory_messages = self.prepare_messages_for_agent(session, current_user_message)
            
            # Calculate statistics
            exchanges = memory.get('exchanges', [])
            summary = memory.get('summary', '')
            llm_summarizations = getattr(self, 'llm_summarization_count', 0)  # Track LLM usage
            
            # Format memory state for display
            memory_log = "=== MEMORY STATE ===\n"
            memory_log += f"Session: {session.get('session_id', 'unknown')} | "
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
                    
                    # Format parameters for display (truncate if too long)
                    params_str = str(params)
                    if len(params_str) > 50:
                        params_str = params_str[:47] + "..."
                    
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
                    
                    # Clean markdown from content
                    content = self._clean_markdown(content)
                    
                    # Truncate for readability
                    if len(content) > 120:
                        content = content[:120] + "..."
                    
                    memory_log += f"[{idx}] {role.upper()}: {content}\n"
            else:
                memory_log += "=== NO MEMORY CONTEXT ===\n"
            
            # Clear session logs after sending to avoid accumulation
            memory['session_logs'] = []
            
            channel_logger.log_to_memory(memory_log)
            
        except Exception as e:
            channel_logger.log_to_memory(f"❌ Error logging final memory state: {str(e)}")