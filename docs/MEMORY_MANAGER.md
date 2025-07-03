# Memory Manager Documentation

## Overview

The Memory Manager is a sophisticated component that handles conversation history, tool result caching, and context optimization for the LLM system.

## Architecture

```
MemoryManager
├── Conversation Memory
│   ├── Summary (compressed history)
│   ├── Exchanges (recent Q&A pairs)
│   └── Current Cycle (active conversation)
├── Tool Cache
│   ├── Cached Results
│   ├── Duration Management
│   └── Parameter Hashing
└── Context Injection
    ├── Screen Context
    └── Proactive Tools
```

## Key Features

### 1. Conversation Memory Structure

```python
conversation_memory = {
    'exchanges': [],           # List of Q&A exchanges (max 10)
    'summary': '',            # Text summary of old conversations
    'current_cycle': {
        'user_question': "",
        'agent_messages': [],
        'final_answer': None
    },
    'tool_cache': {},         # Tool results cache
    'screen_injection_done': False  # Track if injection was done
}
```

### 2. Memory Summarization Algorithm

The system implements a multi-tier summarization strategy:

1. **Large Answer Summarization**
   ```python
   if len(answer) > 750 bytes:
       summarized = summarize_to_500_bytes(answer)
   ```

2. **Exchange Management**
   ```python
   while len(exchanges) > 10:
       oldest = exchanges.pop(0)
       summary += format_exchange(oldest)
       if len(summary) > 4000:
           summary = llm_compress(summary, target=3000)
   ```

3. **LLM-Powered Compression**
   - Uses GPT-4o-mini for intelligent summarization
   - Preserves key information
   - Falls back to truncation on failure

### 3. Tool Result Caching

#### Cache Key Generation
```python
def _generate_tool_cache_key(tool_name: str, parameters: Dict) -> str:
    params_json = json.dumps(parameters, sort_keys=True)
    hash_input = f"{tool_name}:{params_json}"
    return hashlib.md5(hash_input.encode()).hexdigest()
```

#### Cache Entry Structure
```python
cache_entry = {
    'tool_name': str,
    'parameters': dict,
    'result': str,
    'remaining_duration': int,
    'original_duration': int,
    'call_id': str,
    'cached_at': float
}
```

#### Cache Lifecycle
1. **Addition**: Tool results with `llm_cache_duration > 0`
2. **Lookup**: Check cache before execution
3. **Refresh**: Reset duration on cache hit
4. **Cleanup**: Decrement duration after each exchange

### 4. Context Injection System

#### Screen Context Injection
```python
def inject_screen_context(session, json_data, channel_logger):
    # Only inject once per session
    if memory['screen_injection_done']:
        return []
    
    # Get proactive tool results
    proactive_messages, prompt_injection = get_proactive_tool_messages(json_data)
    
    # Create conversation history
    injection_messages = [{
        "role": "assistant",
        "content": f"I can see you're on a specific screen. {prompt_injection}"
    }]
    
    # Add and cache tool results
    injection_messages.extend(proactive_messages)
    _cache_proactive_tool_results(proactive_messages)
    
    memory['screen_injection_done'] = True
    return injection_messages
```

## Memory Management Rules

### Exchange Limits
- Maximum 10 exchanges in active list
- Older exchanges moved to summary
- Each exchange = 1 Q&A pair

### Size Limits
- Answer summarization: > 750 bytes → 500 bytes
- Summary compression: > 4KB → 3KB
- Maximum context: Optimized for LLM window

### Cache Duration Rules
- Duration in "exchanges" not time
- Decrements after each Q&A cycle
- Refreshes on cache hit
- Removes when duration ≤ 0

## API Reference

### Core Methods

#### `initialize_session_memory(session: Dict[str, Any]) -> None`
Initialize memory structure for new session.

#### `prepare_messages_for_agent(session: Dict[str, Any], user_message: str) -> List[Dict[str, str]]`
Prepare conversation history for LLM, including cached tools.

#### `finalize_current_cycle(session: Dict[str, Any], user_question: str, final_answer: str, channel_logger=None) -> None`
Finalize Q&A cycle, manage memory limits, and cleanup cache.

#### `add_tool_to_cache(session: Dict[str, Any], tool_name: str, parameters: Dict[str, Any], result: str, llm_cache_duration: int, channel_logger=None) -> None`
Add tool result to cache with specified duration.

#### `lookup_tool_in_cache(session: Dict[str, Any], tool_name: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]`
Look up tool result in cache and refresh duration if found.

#### `inject_screen_context(session: Dict[str, Any], json_data: Dict[str, Any], channel_logger=None) -> List[Dict[str, Any]]`
Inject screen context and proactive tools at session start.

## Performance Considerations

1. **Memory Efficiency**
   - Automatic summarization prevents memory bloat
   - Cache prevents redundant tool executions

2. **Context Optimization**
   - Keeps context within LLM limits
   - Prioritizes recent and relevant information

3. **Cache Benefits**
   - Reduces API/DB calls
   - Improves response time
   - Maintains consistency across exchanges

## Logging and Observability

The Memory Manager provides detailed logging through Channel 5:

```
=== MEMORY STATE ===
Session: ABC123 | Exchanges: 3 | Summary: 1250 bytes | LLM compressions: 1

=== FUNCTION CACHE STATE ===
Cached functions: 2
  • gcs_get_champion_details({'champion_name': 'droideka'}): 2/3 exchanges remaining
  • db_get_ux_details({'query': 'screen help'}): 1/2 exchanges remaining

=== AGENT RECEIVES (8 messages) ===
[1] USER: Question
[2] ASSISTANT: Answer
...
```