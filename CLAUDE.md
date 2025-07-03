# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent LLM system implementing T-3RN (Tactical-3 Reconnaissance Navigator), a Star Wars-themed game assistant. The system uses a sophisticated agent architecture with multiple specialized tools to help players with game mechanics, strategies, and tactical advice.

## Key Commands

### Development Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the main application
python3 workload_main.py
```

### Running the Application
```bash
# Direct execution (for development/testing)
python3 workload_main.py

# Using PM2 (production)
pm2 start ecosystem.config.js --name "Workload_ChatGPT"
pm2 stop Workload_ChatGPT
pm2 restart Workload_ChatGPT
pm2 logs Workload_ChatGPT
```

### Testing and Linting
Currently, no testing framework or linting tools are configured. When implementing:
- Consider using pytest for testing
- Consider using ruff or pylint for linting
- Test files should go in the `/tests` directory

## Architecture Overview

### Agent System
The codebase uses a sophisticated agent-based architecture:

1. **Base Agent Framework** (`agents/base_agent.py`)
   - Abstract base class defining the agent interface
   - Handles conversation state and tool execution
   - Implements agent stack for execution management

2. **T3RN Agent** (`agents/t3rn_agent.py`)
   - Main agent implementing the T3RN droid personality
   - Handles all game-related queries
   - Manages tool selection and execution

3. **Memory Management** (`agents/memory_manager.py`)
   - Memory management combining different memory strategies
   - Handles context window management
   - Optimizes conversation history for LLM consumption

4. **Message Management** (`agents/agent_message_manager.py`)
   - Prepares and optimizes messages for LLM
   - Handles tool results formatting
   - Manages conversation flow

### Tool System
The application has 15+ specialized tools organized in three categories:

1. **Cache Tools** (`tools_cache/`)
   - Fast static lookups for champion/boss lists
   - Pre-computed data access

2. **RAG Tools** (`tools_rag/`)
   - Semantic search through knowledge base
   - Uses ChromaDB vector database
   - Handles unstructured queries

3. **GCS Tools** (`tools_gcs/`)
   - Structured database queries
   - Game Content System access
   - Precise data retrieval

### Data Layer
- **ChromaDB**: Vector database for semantic search
- **SQLite**: Structured game data (GCS.db, Lore.db)
- **Embeddings**: Uses sentence-transformers for vector generation

### Communication
- TCP socket server on port 5009
- 9-channel output system for organized information display
- Real-time streaming responses

## Key Files to Understand

1. **workload_agent_system.py**: Main agent orchestration logic
2. **workload_config.py**: Configuration and channel definitions
3. **tools_schemas.py**: OpenAI function calling schemas
4. **agents/agent_prompts.py**: System prompts and templates

## Important Considerations

1. **Model Configuration**: The system uses Ollama with models like "hermes3:latest" and "magistral:latest"
2. **Environment Variables**: Check `.env` for model configurations and API keys
3. **Refactoring in Progress**: Multiple files show active refactoring (e.g., fallback_agent_new.py replacing fallback_agent.py)
4. **Dead Code**: The clarification agent system appears to be unused and can be ignored

## Common Development Tasks

When modifying the agent system:
1. Start with `base_agent.py` to understand the agent interface
2. Tool additions require updates to both `tools_functions.py` and `tools_schemas.py`
3. New agents should inherit from `BaseAgent` and implement required methods
4. Memory management changes should be made in `memory_manager.py`

When adding new tools:
1. Create the tool function in the appropriate directory
2. Register it in `tools_functions.py`
3. Add the OpenAI function schema in `tools_schemas.py`
4. Update complementary tools mapping if needed