# Tool System Documentation

## Overview

The Tool System provides a comprehensive set of functions for accessing game data through different backends: static cache, RAG (Retrieval-Augmented Generation), and GCS (Game Content System) database.

## Tool Architecture

```
Tools System
├── Cache Tools (Static)
│   ├── cache_get_champions_list
│   └── cache_get_bosses_list
├── RAG Tools (Semantic Search)
│   ├── rag_get_champion_details
│   ├── rag_get_boss_details
│   ├── db_get_ux_details
│   └── [6 more specialized tools]
└── GCS Tools (Database)
    ├── gcs_get_champion_details
    ├── gcs_find_champions
    ├── gcs_compare_characters
    └── [10 more database tools]
```

## Tool Categories

### 1. Cache Tools
Fast, static lookups for frequently accessed data.

**Characteristics:**
- Instant response (< 5ms)
- No parameters or simple filtering
- Updated periodically
- No cache duration (always fresh)

**Example:**
```python
def cache_get_champions_list() -> str:
    """Returns complete list of all champions"""
    return json.dumps({
        "champions": [...],
        "total": 150,
        "last_updated": "2024-01-15"
    })
```

### 2. RAG Tools
Semantic search through knowledge base using vector embeddings.

**Characteristics:**
- Natural language queries
- Context-aware results
- ~100-500ms response time
- Returns relevant chunks

**Example:**
```python
def rag_get_champion_details(champion_name: str) -> str:
    """Search champion information using semantic search"""
    search_config = {
        "base_filters": {"category": "champions"},
        "required_sections": ["abilities", "stats"],
        "similarity_chunks": 7
    }
    return rag_search(champion_name, search_config)
```

### 3. GCS Tools
Structured database queries for precise data retrieval.

**Characteristics:**
- Exact matching
- Complex filtering
- Relational data
- ~50-200ms response time

**Example:**
```python
def gcs_get_champion_details(champion_name: str) -> str:
    """Get detailed champion data from database"""
    result = execute_query(
        "SELECT * FROM champions WHERE name LIKE ?",
        (f"%{champion_name}%",)
    )
    return json.dumps({
        "status": "success",
        "champion_data": result,
        "llm_cache_duration": 3  # Cache for 3 exchanges
    })
```

## Tool Result Caching

### Cache Duration Configuration

Tools can specify how long their results should be cached:

```python
return json.dumps({
    "status": "success",
    "data": "...",
    "llm_cache_duration": 3,  # Cache for 3 exchanges
    "internal_info": {...}
})
```

### Current Cache Durations

| Tool | Duration | Rationale |
|------|----------|-----------|
| `gcs_get_champion_details` | 3 exchanges | Large detailed data |
| `gcs_get_character_details_by_id` | 3 exchanges | Comprehensive character info |
| `db_get_lore_details` | 3 exchanges | Lore-heavy content |
| `db_get_ux_details` | 2 exchanges | UI context info |
| Others | 0 (no cache) | Dynamic or small data |

### Cache Key Generation

```python
def _generate_tool_cache_key(tool_name: str, parameters: Dict) -> str:
    # Ensures same tool+params = same cache key
    params_json = json.dumps(parameters, sort_keys=True)
    hash_input = f"{tool_name}:{params_json}"
    return hashlib.md5(hash_input.encode()).hexdigest()
```

## Tool Execution Flow

### 1. Cache Check
```python
# Before execution, check cache
cache_entry = memory_manager.lookup_tool_in_cache(
    session, tool_name, parameters
)
if cache_entry:
    return cache_entry['result']  # Cache hit!
```

### 2. Duplicate Prevention
```python
# Check if already in current conversation
if memory_manager.is_tool_already_in_current_messages(
    messages, tool_name, parameters
):
    skip_execution()  # Prevent duplicate
```

### 3. Execution & Caching
```python
# Execute tool
result = tool_function(**parameters)

# Cache if duration > 0
llm_cache_duration = extract_duration(result)
if llm_cache_duration > 0:
    memory_manager.add_tool_to_cache(
        session, tool_name, parameters, 
        result, llm_cache_duration
    )
```

## Proactive Tool System

### Screen-Based Tool Execution

The system can proactively execute tools based on current screen:

```python
SCREEN_TOOL_RULES = {
    "ChampionFeatureModelsPresenter": {
        "context_tool": {
            "tool": "db_get_ux_details",
            "parameters": {"query": "ChampionFeatureModelsPresenter"}
        },
        "data_tools": [{
            "tool": "gcs_get_character_details_by_id",
            "json_field": "ChampionConfigId",
            "parameter_name": "character_id"
        }],
        "prompt_injection": {
            "template": "You are on Champion Details screen viewing '{ChampionConfigId_translated}'",
            "required_fields": ["ChampionConfigId"]
        }
    }
}
```

### Proactive Execution Benefits
1. **Reduced Latency** - Data ready before user asks
2. **Context Awareness** - Tools match current screen
3. **Automatic Caching** - Results cached for reuse

## Tool Response Format

### Standard Response Structure
```json
{
    "status": "success|error",
    "message": "Human readable message",
    "data": {
        // Tool-specific data
    },
    "llm_cache_duration": 0,  // Optional cache duration
    "llm_instruction": "Instructions for LLM on how to use this data",
    "internal_info": {
        "function_name": "tool_name",
        "parameters": {...}
    }
}
```

### Error Response Format
```json
{
    "status": "error",
    "message": "Error description",
    "error_details": "Technical details",
    "guidance": "Suggested next steps",
    "internal_info": {...}
}
```

## Tool Development Guidelines

### 1. Naming Convention
- Prefix with category: `cache_`, `rag_`, `gcs_`
- Descriptive action: `get_`, `find_`, `compare_`
- Clear subject: `champion`, `abilities`, `battles`

### 2. Parameter Design
- Use consistent parameter names
- Validate input thoroughly
- Provide helpful error messages

### 3. Response Design
- Always return JSON (even for errors)
- Include `llm_cache_duration` when appropriate
- Add `llm_instruction` for complex data

### 4. Performance Considerations
- Set appropriate cache durations
- Minimize database queries
- Use batch operations when possible

## Tool Registration

### Adding a New Tool

1. **Create Tool Function**
```python
# tools_gcs/gcs_new_tool.py
def gcs_new_tool(param: str) -> str:
    result = execute_query(...)
    return json.dumps({
        "status": "success",
        "data": result,
        "llm_cache_duration": 2
    })
```

2. **Register in tools_functions.py**
```python
from tools_gcs.gcs_new_tool import gcs_new_tool

available_llm_functions = {
    'gcs_new_tool': {
        'function': gcs_new_tool,
        'is_rag': False,
        'is_gcs': True,
        'category': 'gcs_database',
        'description': 'Clear description of what tool does'
    }
}
```

3. **Add OpenAI Schema**
```python
# tools_schemas.py
schemas = {
    "gcs_new_tool": {
        "type": "function",
        "function": {
            "name": "gcs_new_tool",
            "description": "Detailed description for LLM",
            "parameters": {
                "type": "object",
                "properties": {
                    "param": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param"]
            }
        }
    }
}
```

## Performance Metrics

### Tool Execution Statistics
- Average execution time by category
- Cache hit rates
- Most frequently called tools
- Error rates by tool

### Optimization Opportunities
1. **Batch Similar Queries** - Combine multiple lookups
2. **Precompute Common Queries** - Move to cache tools
3. **Index Optimization** - Improve database queries
4. **Embedding Caching** - Cache vector computations

## Future Enhancements

1. **Tool Chaining**
   - Define tool dependencies
   - Automatic sequence execution
   - Result aggregation

2. **Dynamic Tool Selection**
   - Context-based tool recommendations
   - Performance-based routing
   - Cost optimization

3. **Tool Versioning**
   - A/B testing capabilities
   - Gradual rollouts
   - Backward compatibility