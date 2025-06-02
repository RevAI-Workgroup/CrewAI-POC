# CrewAI 0.121.1 Node Types Research Guide

**Date**: 2024-12-28  
**Task**: 1-13 Node Type Definitions  
**Source**: CrewAI Official Documentation

## Core Components

### Agents
- **role**: String defining the agent's function and expertise
- **goal**: Individual objective guiding decision-making  
- **backstory**: Context and personality for the agent
- **llm**: Language model (optional, defaults to GPT-4)
- **tools**: List of capabilities/functions available
- **memory**: Boolean for maintaining interaction history
- **allow_delegation**: Boolean for task delegation capability
- **max_iter**: Maximum iterations (default: 20)
- **verbose**: Boolean for detailed logging

### Tasks  
- **description**: Clear statement of what the task entails
- **expected_output**: Detailed description of completion criteria
- **agent**: Responsible agent (optional for hierarchical)
- **tools**: Task-specific tools (overrides agent tools)
- **context**: Other tasks whose outputs provide context
- **async_execution**: Boolean for asynchronous execution
- **output_file**: File path for storing output
- **output_pydantic**: Pydantic model for structured output

### Tools
- **name**: Tool identifier
- **description**: What the tool does
- **parameters**: Tool configuration parameters
- **function**: The actual tool implementation

### Flow Control
- **Sequential Process**: Tasks executed in order
- **Hierarchical Process**: Manager coordinates task delegation
- **Context Dependencies**: Tasks can wait for other task outputs

## Validation Rules

### Agent Constraints
- role, goal, backstory are required
- tools must be valid BaseTool instances
- max_iter must be positive integer
- llm must be valid language model reference

### Task Constraints  
- description and expected_output are required
- agent must exist if specified
- context tasks must be completed before execution
- output_pydantic and output_json are mutually exclusive

### Relationship Rules
- Agents can be assigned to multiple tasks
- Tasks can only have one primary agent
- Tools can be shared across agents and tasks
- Context dependencies must form valid DAG (no cycles)

## Node Categories

1. **Agent Nodes**: Autonomous units with roles and capabilities
2. **Task Nodes**: Specific assignments with clear objectives  
3. **Tool Nodes**: Functional capabilities for agents
4. **Flow Nodes**: Process control and execution patterns

## References
- CrewAI Documentation: https://docs.crewai.com/
- GitHub Repository: https://github.com/crewAIInc/crewAI
- Version: 0.121.1 