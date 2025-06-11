# CrewAI 0.121.1 Integration Guide

**Date**: 2024-12-28  
**Task**: 1-19 CrewAI Integration  
**Source**: CrewAI Official Documentation & PyPI  
**Version**: 0.121.1

## Installation

```bash
pip install crewai==0.121.1
```

**Python Requirements**: >=3.10 <3.14

## Core Classes and Components

### 1. Agent Class
The foundation of CrewAI - autonomous units with specific roles and capabilities.

**Required Properties**:
- `role`: String defining the agent's function
- `goal`: Individual objective guiding decisions  
- `backstory`: Context and personality

**Optional Properties**:
- `llm`: Language model (defaults to OpenAI GPT-4)
- `tools`: List of available capabilities
- `memory`: Boolean for maintaining history
- `allow_delegation`: Boolean for task delegation
- `max_iter`: Maximum iterations (default: 20)
- `verbose`: Boolean for detailed logging

**Example**:
```python
from crewai import Agent

agent = Agent(
    role="Senior Data Analyst",
    goal="Analyze complex datasets to extract actionable insights",
    backstory="You are an expert data analyst with 10+ years experience",
    verbose=True,
    memory=True,
    allow_delegation=False,
    max_iter=25
)
```

### 2. Task Class
Individual assignments with clear objectives and completion criteria.

**Required Properties**:
- `description`: Clear statement of what the task entails
- `expected_output`: Detailed completion criteria

**Optional Properties**:
- `agent`: Assigned agent (can be auto-assigned in hierarchical)
- `tools`: Task-specific tools (overrides agent tools)
- `context`: List of other tasks whose outputs provide context
- `async_execution`: Boolean for asynchronous execution
- `output_file`: File path for storing output
- `output_pydantic`: Pydantic model for structured output

**Example**:
```python
from crewai import Task

task = Task(
    description="Analyze user engagement metrics for Q4 2024",
    expected_output="Detailed report with key insights and recommendations",
    agent=agent,
    output_file="q4_analysis.md",
    async_execution=False
)
```

### 3. Crew Class
Orchestrates multiple agents and tasks with defined processes.

**Key Properties**:
- `agents`: List of Agent objects
- `tasks`: List of Task objects  
- `process`: Process type (sequential, hierarchical)
- `verbose`: Boolean for detailed execution logging
- `manager_llm`: LLM for manager in hierarchical process

**Example**:
```python
from crewai import Crew, Process

crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2, task3],
    process=Process.sequential,
    verbose=True
)

result = crew.kickoff()
```

### 4. Tools Integration
CrewAI supports various tools for enhanced agent capabilities.

**Basic Tool Example**:
```python
from crewai_tools import SerperDevTool, FileReadTool

search_tool = SerperDevTool()
file_tool = FileReadTool()

agent = Agent(
    role="Researcher",
    goal="Gather comprehensive data",
    backstory="Expert researcher",
    tools=[search_tool, file_tool]
)
```

## Process Types

### Sequential Process
Tasks executed one after another, outputs passed as context.

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential
)
```

### Hierarchical Process  
Manager agent coordinates task delegation and execution.

```python
crew = Crew(
    agents=[analyst, researcher, writer],
    tasks=[analysis_task, research_task, report_task],
    process=Process.hierarchical,
    manager_llm=ChatOpenAI(model="gpt-4")
)
```

## Backend Integration Patterns

### 1. Async Execution with FastAPI
```python
from fastapi import FastAPI, BackgroundTasks
from crewai import Crew, Agent, Task, Process
import asyncio

app = FastAPI()

async def execute_crew_async(crew_config: dict):
    """Execute CrewAI crew asynchronously"""
    agents = [create_agent(config) for config in crew_config['agents']]
    tasks = [create_task(config) for config in crew_config['tasks']]
    
    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    # Execute in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, crew.kickoff)
    return result

@app.post("/execute-crew")
async def execute_crew(crew_config: dict, background_tasks: BackgroundTasks):
    """API endpoint to execute crew"""
    background_tasks.add_task(execute_crew_async, crew_config)
    return {"status": "execution_started"}
```

### 2. Database Integration
```python
from sqlalchemy.orm import Session
from backend.models.execution import ExecutionLog

def save_crew_execution(crew_result, db: Session):
    """Save crew execution results to database"""
    execution = ExecutionLog(
        crew_id="crew_001",
        status="completed",
        result=crew_result.raw,
        token_usage=crew_result.token_usage,
        created_at=datetime.utcnow()
    )
    db.add(execution)
    db.commit()
```

### 3. Graph Translation Service Foundation
```python
class GraphToCrewTranslator:
    """Service to translate graph objects to CrewAI components"""
    
    def translate_graph(self, graph_data: dict) -> Crew:
        """Convert graph representation to CrewAI Crew"""
        agents = self._create_agents_from_nodes(graph_data['nodes'])
        tasks = self._create_tasks_from_edges(graph_data['edges'])
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=self._determine_process(graph_data),
            verbose=True
        )
    
    def _create_agents_from_nodes(self, nodes: list) -> list[Agent]:
        """Convert graph nodes to CrewAI agents"""
        agents = []
        for node in nodes:
            if node['type'] == 'agent':
                agent = Agent(
                    role=node['data']['role'],
                    goal=node['data']['goal'],
                    backstory=node['data']['backstory'],
                    tools=self._load_tools(node['data'].get('tools', []))
                )
                agents.append(agent)
        return agents
```

## Error Handling Patterns

### 1. Execution Errors
```python
try:
    result = crew.kickoff()
except Exception as e:
    # Log error and handle gracefully
    logger.error(f"Crew execution failed: {str(e)}")
    # Save error to database
    save_execution_error(crew_id, str(e))
    raise HTTPException(status_code=500, detail="Crew execution failed")
```

### 2. Validation Errors
```python
def validate_crew_config(config: dict):
    """Validate crew configuration before execution"""
    required_fields = ['agents', 'tasks']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate agents have required properties
    for agent_config in config['agents']:
        if not all(key in agent_config for key in ['role', 'goal', 'backstory']):
            raise ValueError("Agent missing required properties")
```

## Memory and State Management

### 1. Agent Memory
```python
agent = Agent(
    role="Research Assistant",
    goal="Maintain context across conversations",
    backstory="Expert at remembering previous interactions",
    memory=True  # Enables memory
)
```

### 2. State Persistence
```python
class CrewStateManager:
    """Manage crew execution state"""
    
    def save_state(self, crew_id: str, state: dict):
        """Save crew state to database"""
        # Implementation for state persistence
        pass
    
    def restore_state(self, crew_id: str) -> dict:
        """Restore crew state from database"""
        # Implementation for state restoration
        pass
```

## Testing Patterns

### 1. Unit Tests
```python
import pytest
from crewai import Agent, Task, Crew, Process

def test_agent_creation():
    """Test basic agent creation"""
    agent = Agent(
        role="Tester",
        goal="Test functionality",
        backstory="QA expert"
    )
    assert agent.role == "Tester"

def test_crew_execution():
    """Test crew execution"""
    agent = Agent(role="Analyst", goal="Analyze", backstory="Expert")
    task = Task(description="Simple task", expected_output="Result")
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
    
    result = crew.kickoff()
    assert result is not None
```

### 2. Integration Tests
```python
def test_backend_integration():
    """Test CrewAI integration with backend"""
    # Test API endpoint
    # Test database operations
    # Test async execution
    pass
```

## Performance Considerations

### 1. Resource Management
- Set appropriate `max_iter` limits
- Use `verbose=False` in production
- Implement proper timeout handling
- Monitor token usage and costs

### 2. Scalability
- Use async execution for long-running tasks
- Implement proper queue management
- Consider rate limiting for API calls
- Monitor memory usage with agent memory

## Security Considerations

### 1. API Key Management
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Secure API key handling
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

### 2. Input Validation
- Validate all user inputs before crew execution
- Sanitize file paths and outputs
- Implement proper authentication for crew execution APIs

## Next Steps for Backend Integration

1. **Task 1-20**: Graph to CrewAI Translation Service
2. **Task 1-21**: Async Execution with Celery
3. **Task 1-22**: Execution Status Management
4. **Task 1-23**: Error Handling Implementation
5. **Task 1-25**: SSE Streaming Integration

## References

- CrewAI Documentation: https://docs.crewai.com/
- PyPI Package: https://pypi.org/project/crewai/0.121.1/
- GitHub Repository: https://github.com/crewAIInc/crewAI
- Installation Guide: https://docs.crewai.com/installation 