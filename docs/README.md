# Workload ChatGPT Documentation

## Overview

This directory contains comprehensive documentation for the Workload ChatGPT system architecture and components.

## Documentation Structure

### Core Architecture
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - Main architecture document covering all innovative features
  - LLM Flow Architecture
  - Agent Workflow System
  - Intelligent Fallback Mechanism
  - Context Injection System
  - Memory Summarization
  - Tool Result Caching

### Component Documentation

#### 1. [Memory Manager](MEMORY_MANAGER.md)
Sophisticated memory management system featuring:
- Conversation history management
- Intelligent summarization with LLM compression
- Tool result caching with duration control
- Context injection capabilities

#### 2. [Agent System](AGENT_SYSTEM.md)
Multi-agent architecture documentation:
- T3RN Agent (primary game assistant)
- Fallback Agent (error recovery)
- Agent stack and context management
- Tool execution loop

#### 3. [Tool System](TOOL_SYSTEM.md)
Comprehensive tool framework:
- Three categories: Cache, RAG, and GCS tools
- Tool result caching mechanism
- Proactive tool execution
- Tool development guidelines

#### 4. [Context Injection](CONTEXT_INJECTION.md)
Innovative context awareness system:
- Screen-based context detection
- Conversation history injection method
- Proactive tool configuration
- Rule-based tool selection

## Quick Start Guide

### For Developers

1. **Understanding the System**
   - Start with [ARCHITECTURE.md](../ARCHITECTURE.md) for overview
   - Read component docs based on your focus area

2. **Adding New Features**
   - New agents: See [AGENT_SYSTEM.md](AGENT_SYSTEM.md)
   - New tools: See [TOOL_SYSTEM.md](TOOL_SYSTEM.md)
   - Screen rules: See [CONTEXT_INJECTION.md](CONTEXT_INJECTION.md)

3. **Debugging**
   - Check multi-channel logs (Channels 0-8)
   - Memory state in Channel 5
   - Tool calls in Channel 3

### For System Administrators

1. **Performance Monitoring**
   - Memory usage via Memory Manager logs
   - Cache hit rates in Function Cache State
   - Tool execution times in Performance channel

2. **Configuration**
   - Tool cache durations in tool responses
   - Screen rules in `screen_tool_config.py`
   - Memory limits in `MemoryManager.__init__`

## Key Innovations

### 1. Hybrid Memory Architecture
Combines intelligent summarization with tool result caching for optimal context usage.

### 2. Conversation History Injection
Context injected as conversation history rather than system prompts, preserving LLM behavior.

### 3. Proactive Intelligence
Tools executed based on screen context before users ask questions.

### 4. Multi-Level Fallback
Graceful degradation from primary agent → fallback agent → emergency response.

### 5. Observable System
Nine-channel logging system provides comprehensive visibility into system operation.

## Architecture Diagrams

### System Flow
```
User Input → Session Manager → Memory Manager → Agent System → Tool Execution → Response
                                     ↓                              ↓
                               Context Injection              Result Caching
```

### Memory Structure
```
Conversation Memory
├── Summary (compressed history)
├── Exchanges (last 10 Q&As)
├── Current Cycle (active)
└── Tool Cache (with durations)
```

### Agent Stack
```
T3RN Agent (primary)
    ↓ (on failure)
Fallback Agent (recovery)
    ↓ (on critical failure)
Emergency Response
```

## Contributing

When contributing to the system:

1. **Documentation First**
   - Update relevant .md files
   - Add examples for new features
   - Include performance considerations

2. **Follow Patterns**
   - Use existing agent/tool patterns
   - Maintain channel discipline
   - Preserve error handling chains

3. **Test Thoroughly**
   - Unit tests for new components
   - Integration tests for workflows
   - Performance benchmarks

## Support

For questions or issues:
- Check existing documentation
- Review code comments
- Examine log outputs
- Contact development team

## Version History

- **v2.0** - Current version with advanced features
  - Tool result caching
  - Context injection system
  - Memory summarization
  - Multi-agent architecture

- **v1.0** - Initial release
  - Basic agent system
  - Simple memory management
  - Standard tool execution