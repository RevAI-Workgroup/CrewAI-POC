"""
Dynamic Task Creation Service for Chat Messages
Creates CrewAI Task objects dynamically from user chat messages.
"""
import logging
from typing import Optional, Dict, Any, List, Union
from crewai import Task, Crew
from crewai.agent import BaseAgent
from datetime import datetime

logger = logging.getLogger(__name__)

class DynamicTaskService:
    """Service for creating dynamic CrewAI tasks from chat messages."""
    
    @staticmethod
    def create_task_from_message(
        message: str,
        output_specification: Optional[str] = None,
        agent: Optional[BaseAgent] = None,
        task_metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Create a CrewAI Task from a chat message.
        
        Args:
            message: The user's chat message content
            output_specification: Optional output format specification
            agent: Agent to assign the task to (optional)
            task_metadata: Additional metadata for the task
            
        Returns:
            CrewAI Task object ready for execution
            
        Raises:
            ValueError: If message is empty or invalid
        """
        if not message or not message.strip():
            raise ValueError("Message content cannot be empty")
        
        # Clean and validate message
        cleaned_message = message.strip()
        
        # Default output specification
        default_output = "A helpful and detailed response addressing the user's request"
        expected_output = output_specification or default_output
        
        # Create task metadata
        metadata = task_metadata or {}
        metadata.update({
            "created_from_chat": True,
            "created_at": datetime.utcnow().isoformat(),
            "original_message": message
        })
        
        try:
            # Create the dynamic task
            task = Task(
                description=cleaned_message,
                expected_output=expected_output,
                agent=agent,
                async_execution=False,  # Synchronous execution for chat
                context=None,  # No context dependencies for dynamic tasks
                tools=None,    # Tools will be inherited from agent
                output_file=None,  # No file output for chat tasks
                callback=None  # No callback for chat tasks
            )
            
            logger.info(f"Created dynamic task from message: '{cleaned_message[:50]}...'")
            return task
            
        except Exception as e:
            logger.error(f"Failed to create dynamic task from message: {e}")
            raise ValueError(f"Failed to create task: {str(e)}")
    
    @staticmethod
    def add_dynamic_task_to_crew(
        crew: Crew,
        dynamic_task: Task,
        replace_existing: bool = False
    ) -> Crew:
        """
        Add a dynamic task to an existing crew.
        
        Args:
            crew: The CrewAI Crew object
            dynamic_task: The dynamic task to add
            replace_existing: Whether to replace existing tasks or append
            
        Returns:
            Modified Crew object with the dynamic task added
            
        Raises:
            ValueError: If crew or task is invalid
        """
        if not crew:
            raise ValueError("Crew cannot be None")
        
        if not dynamic_task:
            raise ValueError("Dynamic task cannot be None")
        
        try:
            # Ensure the task has an agent assigned
            if not dynamic_task.agent and crew.agents:
                # Assign to the first available agent if no agent specified
                dynamic_task.agent = crew.agents[0]
                logger.info(f"Assigned dynamic task to agent: {crew.agents[0].role}")
            
            if replace_existing:
                # Replace all existing tasks with the dynamic task
                crew.tasks = [dynamic_task]
                logger.info("Replaced existing tasks with dynamic task")
            else:
                # Append to existing tasks
                if not hasattr(crew, 'tasks') or crew.tasks is None:
                    crew.tasks = []
                crew.tasks.append(dynamic_task)
                logger.info(f"Added dynamic task to crew (total tasks: {len(crew.tasks)})")
            
            return crew
            
        except Exception as e:
            logger.error(f"Failed to add dynamic task to crew: {e}")
            raise ValueError(f"Failed to add task to crew: {str(e)}")
    
    @staticmethod
    def create_chat_task_for_crew(
        crew: Crew,
        message: str,
        output_specification: Optional[str] = None,
        preferred_agent_role: Optional[str] = None
    ) -> Crew:
        """
        Create a dynamic task from a chat message and add it to the crew.
        
        Args:
            crew: The CrewAI Crew object
            message: User's chat message
            output_specification: Optional output format
            preferred_agent_role: Preferred agent role for task assignment
            
        Returns:
            Crew with the dynamic task added
            
        Raises:
            ValueError: If crew or message is invalid
        """
        if not crew or not crew.agents:
            raise ValueError("Crew must have at least one agent")
        
        # Select agent for the task
        selected_agent = None
        if preferred_agent_role:
            # Find agent by role
            for agent in crew.agents:
                if hasattr(agent, 'role') and agent.role.lower() == preferred_agent_role.lower():
                    selected_agent = agent
                    break
        
        # Default to first agent if no specific agent found
        if not selected_agent:
            selected_agent = crew.agents[0]
        
        # Create the dynamic task
        dynamic_task = DynamicTaskService.create_task_from_message(
            message=message,
            output_specification=output_specification,
            agent=selected_agent,
            task_metadata={
                "assigned_agent_role": selected_agent.role if hasattr(selected_agent, 'role') else 'unknown'
            }
        )
        
        # Add task to crew (replace existing tasks for chat)
        return DynamicTaskService.add_dynamic_task_to_crew(
            crew=crew,
            dynamic_task=dynamic_task,
            replace_existing=True  # Replace existing tasks for chat interaction
        )
    
    @staticmethod
    def validate_task_requirements(message: str, output_specification: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate task creation requirements.
        
        Args:
            message: User's chat message
            output_specification: Optional output specification
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Validate message content
        if not message or not message.strip():
            validation_result["is_valid"] = False
            validation_result["errors"].append("Message content cannot be empty")
            return validation_result
        
        message_length = len(message.strip())
        
        # Check message length
        if message_length < 10:
            validation_result["warnings"].append("Message is very short - consider providing more detail")
        elif message_length > 2000:
            validation_result["warnings"].append("Message is very long - consider breaking into smaller requests")
        
        # Validate output specification if provided
        if output_specification:
            if len(output_specification.strip()) < 5:
                validation_result["warnings"].append("Output specification is very brief")
            elif len(output_specification.strip()) > 500:
                validation_result["warnings"].append("Output specification is very detailed - consider simplifying")
        
        # Provide suggestions for better task creation
        if not output_specification:
            validation_result["suggestions"].append("Consider providing an output specification for more targeted results")
        
        return validation_result 