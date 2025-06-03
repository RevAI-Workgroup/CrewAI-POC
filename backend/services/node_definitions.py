"""
Service for providing node definition structure metadata.
Generates structured information about node types for frontend consumption.
"""

from typing import Dict, List, Any, Optional, Union
from models.node_types import NodeTypeEnum, ProcessTypeEnum, OutputFormatEnum, LLMProviderEnum


class NodeDefinitionService:
    """Service for generating node definition structure metadata."""
    
    @staticmethod
    def get_node_definitions_structure() -> Dict[str, Any]:
        """
        Generate complete node definitions structure for frontend consumption.
        
        Returns:
            Dictionary containing all node type definitions with fields, constraints, etc.
        """
        node_types = {
            "crew": NodeDefinitionService._get_crew_definition(),
            "agent": NodeDefinitionService._get_agent_definition(),
            "task": NodeDefinitionService._get_task_definition(),
            "tool": NodeDefinitionService._get_tool_definition(),
            "flow": NodeDefinitionService._get_flow_definition()
        }
        
        # Add all LLM provider nodes
        llm_providers = NodeDefinitionService._get_llm_providers()
        for provider_id, provider_def in llm_providers.items():
            node_types[provider_id] = provider_def
        
        return {
            "categories": NodeDefinitionService._get_node_categories(),
            "node_types": node_types,
            "connection_constraints": NodeDefinitionService._get_connection_constraints(),
            "enums": NodeDefinitionService._get_enum_definitions()
        }
    
    @staticmethod
    def _get_node_categories() -> List[Dict[str, Any]]:
        """Get node categories for sidebar organization."""
        return [
            {
                "id": "core",
                "name": "Core Components",
                "description": "Essential CrewAI building blocks",
                "nodes": ["crew", "agent", "task"]
            },
            {
                "id": "llm",
                "name": "Language Models",
                "description": "AI model providers and configurations",
                "nodes": ["openai", "anthropic", "ollama", "google", "azure", "groq"]
            },
            {
                "id": "tools",
                "name": "Tools & Extensions",
                "description": "External tools and custom functions",
                "nodes": ["tool"]
            },
            {
                "id": "control",
                "name": "Flow Control",
                "description": "Workflow control and routing",
                "nodes": ["flow"]
            }
        ]
    
    @staticmethod
    def _get_crew_definition() -> Dict[str, Any]:
        """Get Crew node definition structure."""
        return {
            "name": "Crew",
            "description": "A collection of agents working together on tasks",
            "icon": "crew",
            "color": "#4F46E5",
            "category": "core",
            "fields": {
                "name": {
                    "type": "string",
                    "label": "Crew Name",
                    "required": True,
                    "default": "My Crew",
                    "placeholder": "Enter crew name",
                    "display_order": 1,
                    "show_by_default": True
                },
                "description": {
                    "type": "text",
                    "label": "Description",
                    "required": False,
                    "placeholder": "Describe what this crew does",
                    "display_order": 2,
                    "show_by_default": True
                },
                "tasks": {
                    "type": "multi_select",
                    "label": "Tasks",
                    "required": True,
                    "source": "nodes",
                    "filter": {"type": "task"},
                    "display_order": 3,
                    "show_by_default": True,
                    "validation": {"min_items": 1}
                },
                "agents": {
                    "type": "multi_select",
                    "label": "Agents",
                    "required": True,
                    "source": "nodes",
                    "filter": {"type": "agent"},
                    "display_order": 4,
                    "show_by_default": True,
                    "validation": {"min_items": 1}
                },
                "process": {
                    "type": "select",
                    "label": "Process Type",
                    "required": True,
                    "default": "sequential",
                    "options": [
                        {"value": "sequential", "label": "Sequential"},
                        {"value": "hierarchical", "label": "Hierarchical"}
                    ],
                    "display_order": 5,
                    "show_by_default": True
                },
                "verbose": {
                    "type": "boolean",
                    "label": "Verbose Logging",
                    "required": False,
                    "default": False,
                    "display_order": 6,
                    "show_by_default": True
                },
                "manager_agent": {
                    "type": "select",
                    "label": "Manager Agent",
                    "required": False,
                    "source": "nodes",
                    "filter": {"type": "agent"},
                    "display_order": 7,
                    "show_by_default": True
                },
                "max_rpm": {
                    "type": "number",
                    "label": "Max Requests/Minute",
                    "required": False,
                    "validation": {"min": 1},
                    "display_order": 8,
                    "show_by_default": False
                },
                "memory": {
                    "type": "select",
                    "label": "Memory",
                    "required": False,
                    "source": "nodes",
                    "filter": {"type": "memory"},
                    "display_order": 9,
                    "show_by_default": False,
                    "description": "Future memory node will be linked here"
                }
            }
        }
    
    @staticmethod
    def _get_agent_definition() -> Dict[str, Any]:
        """Get Agent node definition structure."""
        return {
            "name": "Agent",
            "description": "An AI agent with specific role and capabilities",
            "icon": "agent",
            "color": "#059669",
            "category": "core",
            "fields": {
                "name": {
                    "type": "string",
                    "label": "Agent Name",
                    "required": True,
                    "default": "My Agent",
                    "placeholder": "Enter agent name",
                    "display_order": 1,
                    "show_by_default": True
                },
                "role": {
                    "type": "text",
                    "label": "Role",
                    "required": True,
                    "placeholder": "What is this agent's function and expertise?",
                    "display_order": 2,
                    "show_by_default": True
                },
                "goal": {
                    "type": "text",
                    "label": "Goal",
                    "required": True,
                    "placeholder": "What is this agent trying to achieve?",
                    "display_order": 3,
                    "show_by_default": True
                },
                "backstory": {
                    "type": "text",
                    "label": "Backstory",
                    "required": False,
                    "placeholder": "What's the agent's context and personality?",
                    "display_order": 4,
                    "show_by_default": True
                },
                "llm": {
                    "type": "select",
                    "label": "Language Model",
                    "required": True,
                    "source": "nodes",
                    "filter": {"category": "llm"},
                    "display_order": 5,
                    "show_by_default": True
                },
                "tool": {
                    "type": "multi_select",
                    "label": "Tools",
                    "required": False,
                    "source": "nodes",
                    "filter": {"type": "tool"},
                    "display_order": 6,
                    "show_by_default": True
                },
                "verbose": {
                    "type": "boolean",
                    "label": "Verbose Logging",
                    "required": False,
                    "default": False,
                    "display_order": 7,
                    "show_by_default": False
                },
                "multimodal": {
                    "type": "boolean",
                    "label": "Multimodal",
                    "required": False,
                    "default": False,
                    "display_order": 8,
                    "show_by_default": False
                },
                "response_template": {
                    "type": "text",
                    "label": "Response Template",
                    "required": False,
                    "placeholder": "Define how the agent should format responses",
                    "display_order": 9,
                    "show_by_default": False
                },
                "reasoning": {
                    "type": "boolean",
                    "label": "Reasoning",
                    "required": False,
                    "default": False,
                    "display_order": 10,
                    "show_by_default": False
                }
            }
        }
    
    @staticmethod
    def _get_task_definition() -> Dict[str, Any]:
        """Get Task node definition structure."""
        return {
            "name": "Task",
            "description": "A specific task to be completed by an agent",
            "icon": "task",
            "color": "#DC2626",
            "category": "core",
            "fields": {
                "description": {
                    "type": "text",
                    "label": "Description",
                    "required": True,
                    "placeholder": "What needs to be done?",
                    "display_order": 1,
                    "show_by_default": True
                },
                "expected_output": {
                    "type": "text",
                    "label": "Expected Output",
                    "required": False,
                    "placeholder": "Describe the completion criteria",
                    "display_order": 2,
                    "show_by_default": True
                },
                "name": {
                    "type": "string",
                    "label": "Task Name",
                    "required": False,
                    "default": "My Task",
                    "placeholder": "Enter task name",
                    "display_order": 3,
                    "show_by_default": True
                },
                "markdown": {
                    "type": "boolean",
                    "label": "Markdown Output",
                    "required": False,
                    "default": False,
                    "display_order": 4,
                    "show_by_default": False
                }
            }
        }
    
    @staticmethod
    def _get_common_llm_fields() -> Dict[str, Any]:
        """Get common fields for all LLM providers."""
        return {
            "name": {
                "type": "string",
                "label": "Model Name",
                "required": True,
                "default": "My LLM",
                "placeholder": "Enter model name",
                "display_order": 1,
                "show_by_default": True
            },
            "model": {
                "type": "select",
                "label": "Model",
                "required": True,
                "display_order": 2,
                "show_by_default": True,
                "options": []  # Will be populated per provider
            },
            "temperature": {
                "type": "slider",
                "label": "Temperature",
                "required": False,
                "default": 0.7,
                "validation": {"min": 0.0, "max": 1.0, "step": 0.1},
                "display_order": 3,
                "show_by_default": True,
                "description": "Controls randomness (0.0-1.0)"
            },
            "max_tokens": {
                "type": "number",
                "label": "Max Tokens",
                "required": False,
                "default": 4096,
                "validation": {"min": 1, "max": 100000},
                "display_order": 4,
                "show_by_default": True,
                "description": "Limits response length"
            },
            "timeout": {
                "type": "number",
                "label": "Timeout (seconds)",
                "required": False,
                "default": 120,
                "validation": {"min": 1},
                "display_order": 5,
                "show_by_default": False,
                "description": "Maximum wait time for response"
            },
            "top_p": {
                "type": "slider",
                "label": "Top P",
                "required": False,
                "default": 0.9,
                "validation": {"min": 0.0, "max": 1.0, "step": 0.1},
                "display_order": 6,
                "show_by_default": False,
                "description": "Alternative to temperature for sampling"
            },
            "frequency_penalty": {
                "type": "slider",
                "label": "Frequency Penalty",
                "required": False,
                "default": 0.1,
                "validation": {"min": -2.0, "max": 2.0, "step": 0.1},
                "display_order": 7,
                "show_by_default": False,
                "description": "Reduces word repetition"
            },
            "presence_penalty": {
                "type": "slider",
                "label": "Presence Penalty",
                "required": False,
                "default": 0.1,
                "validation": {"min": -2.0, "max": 2.0, "step": 0.1},
                "display_order": 8,
                "show_by_default": False,
                "description": "Encourages new topics"
            },
            "seed": {
                "type": "number",
                "label": "Seed",
                "required": False,
                "validation": {"min": 0},
                "display_order": 9,
                "show_by_default": False,
                "description": "Ensures consistent outputs"
            }
        }
    
    @staticmethod
    def _get_llm_providers() -> Dict[str, Dict[str, Any]]:
        """Get all LLM provider node definitions."""
        providers = {}
        
        # OpenAI
        openai_fields = NodeDefinitionService._get_common_llm_fields()
        openai_fields["model"]["options"] = [
            {"value": "gpt-4", "label": "GPT-4"},
            {"value": "gpt-4-turbo", "label": "GPT-4 Turbo"},
            {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
            {"value": "gpt-4o", "label": "GPT-4o"},
            {"value": "gpt-4o-mini", "label": "GPT-4o Mini"}
        ]
        openai_fields["api_key"] = {
            "type": "password",
            "label": "API Key",
            "required": True,
            "placeholder": "Enter OpenAI API key",
            "display_order": 10,
            "show_by_default": True
        }
        
        providers["openai"] = {
            "name": "OpenAI",
            "description": "OpenAI GPT models",
            "icon": "openai",
            "color": "#00A67E",
            "category": "llm",
            "provider": "openai",
            "fields": openai_fields
        }
        
        # Anthropic
        anthropic_fields = NodeDefinitionService._get_common_llm_fields()
        anthropic_fields["model"]["options"] = [
            {"value": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet"},
            {"value": "claude-3-sonnet-20240229", "label": "Claude 3 Sonnet"},
            {"value": "claude-3-haiku-20240307", "label": "Claude 3 Haiku"},
            {"value": "claude-3-opus-20240229", "label": "Claude 3 Opus"}
        ]
        anthropic_fields["api_key"] = {
            "type": "password",
            "label": "API Key",
            "required": True,
            "placeholder": "Enter Anthropic API key",
            "display_order": 10,
            "show_by_default": True
        }
        
        providers["anthropic"] = {
            "name": "Anthropic",
            "description": "Anthropic Claude models",
            "icon": "anthropic",
            "color": "#D97706",
            "category": "llm",
            "provider": "anthropic",
            "fields": anthropic_fields
        }
        
        # Ollama
        ollama_fields = NodeDefinitionService._get_common_llm_fields()
        ollama_fields["model"]["options"] = [
            {"value": "llama3.2", "label": "Llama 3.2"},
            {"value": "llama3.1", "label": "Llama 3.1"},
            {"value": "llama3", "label": "Llama 3"},
            {"value": "mistral", "label": "Mistral"},
            {"value": "codellama", "label": "Code Llama"},
            {"value": "qwen2.5", "label": "Qwen 2.5"}
        ]
        ollama_fields["base_url"] = {
            "type": "string",
            "label": "Base URL",
            "required": True,
            "default": "http://localhost:11434",
            "placeholder": "Enter Ollama server URL",
            "display_order": 10,
            "show_by_default": True
        }
        
        providers["ollama"] = {
            "name": "Ollama",
            "description": "Local Ollama models",
            "icon": "ollama",
            "color": "#000000",
            "category": "llm",
            "provider": "ollama",
            "fields": ollama_fields
        }
        
        # Google
        google_fields = NodeDefinitionService._get_common_llm_fields()
        google_fields["model"]["options"] = [
            {"value": "gemini-1.5-pro", "label": "Gemini 1.5 Pro"},
            {"value": "gemini-1.5-flash", "label": "Gemini 1.5 Flash"},
            {"value": "gemini-pro", "label": "Gemini Pro"}
        ]
        google_fields["api_key"] = {
            "type": "password",
            "label": "API Key",
            "required": True,
            "placeholder": "Enter Google AI API key",
            "display_order": 10,
            "show_by_default": True
        }
        
        providers["google"] = {
            "name": "Google AI",
            "description": "Google Gemini models",
            "icon": "google",
            "color": "#4285F4",
            "category": "llm",
            "provider": "google",
            "fields": google_fields
        }
        
        # Azure OpenAI
        azure_fields = NodeDefinitionService._get_common_llm_fields()
        azure_fields["model"]["options"] = [
            {"value": "gpt-4", "label": "GPT-4"},
            {"value": "gpt-4-turbo", "label": "GPT-4 Turbo"},
            {"value": "gpt-35-turbo", "label": "GPT-3.5 Turbo"}
        ]
        azure_fields["api_key"] = {
            "type": "password",
            "label": "API Key",
            "required": True,
            "placeholder": "Enter Azure OpenAI API key",
            "display_order": 10,
            "show_by_default": True
        }
        azure_fields["base_url"] = {
            "type": "string",
            "label": "Endpoint URL",
            "required": True,
            "placeholder": "https://your-resource.openai.azure.com/",
            "display_order": 11,
            "show_by_default": True
        }
        
        providers["azure"] = {
            "name": "Azure OpenAI",
            "description": "Azure OpenAI Service",
            "icon": "azure",
            "color": "#0078D4",
            "category": "llm",
            "provider": "azure",
            "fields": azure_fields
        }
        
        # Groq
        groq_fields = NodeDefinitionService._get_common_llm_fields()
        groq_fields["model"]["options"] = [
            {"value": "llama3-70b-8192", "label": "Llama 3 70B"},
            {"value": "llama3-8b-8192", "label": "Llama 3 8B"},
            {"value": "mixtral-8x7b-32768", "label": "Mixtral 8x7B"},
            {"value": "gemma-7b-it", "label": "Gemma 7B"}
        ]
        groq_fields["api_key"] = {
            "type": "password",
            "label": "API Key",
            "required": True,
            "placeholder": "Enter Groq API key",
            "display_order": 10,
            "show_by_default": True
        }
        
        providers["groq"] = {
            "name": "Groq",
            "description": "Groq AI models",
            "icon": "groq",
            "color": "#F55036",
            "category": "llm",
            "provider": "groq",
            "fields": groq_fields
        }
        
        return providers
    
    @staticmethod
    def _get_tool_definition() -> Dict[str, Any]:
        """Get Tool node definition structure."""
        return {
            "name": "Tool",
            "description": "External tool or custom function",
            "icon": "tool",
            "color": "#EA580C",
            "category": "tools",
            "fields": {
                "name": {
                    "type": "string",
                    "label": "Tool Name",
                    "required": True,
                    "default": "My Tool",
                    "placeholder": "Enter tool name",
                    "display_order": 1,
                    "show_by_default": True
                },
                "tool_type": {
                    "type": "select",
                    "label": "Tool Type",
                    "required": True,
                    "options": [
                        {"value": "web_search", "label": "Web Search"},
                        {"value": "file_reader", "label": "File Reader"},
                        {"value": "calculator", "label": "Calculator"},
                        {"value": "custom", "label": "Custom Tool"}
                    ],
                    "display_order": 2,
                    "show_by_default": True
                },
                "description": {
                    "type": "text",
                    "label": "Description",
                    "required": False,
                    "placeholder": "What does this tool do?",
                    "display_order": 3,
                    "show_by_default": True
                },
                "parameters": {
                    "type": "json",
                    "label": "Parameters",
                    "required": False,
                    "placeholder": "{}",
                    "display_order": 4,
                    "show_by_default": False
                },
                "function_name": {
                    "type": "string",
                    "label": "Function Name",
                    "required": False,
                    "placeholder": "my_custom_function",
                    "display_order": 5,
                    "show_by_default": False,
                    "condition": {"field": "tool_type", "value": "custom"}
                },
                "api_endpoint": {
                    "type": "string",
                    "label": "API Endpoint",
                    "required": False,
                    "placeholder": "https://api.example.com/endpoint",
                    "display_order": 6,
                    "show_by_default": False
                }
            }
        }
    
    @staticmethod
    def _get_flow_definition() -> Dict[str, Any]:
        """Get Flow node definition structure."""
        return {
            "name": "Flow Control",
            "description": "Control workflow execution flow",
            "icon": "flow",
            "color": "#0891B2",
            "category": "control",
            "fields": {
                "name": {
                    "type": "string",
                    "label": "Flow Name",
                    "required": True,
                    "default": "Flow Control",
                    "placeholder": "Enter flow name",
                    "display_order": 1,
                    "show_by_default": True
                },
                "flow_type": {
                    "type": "select",
                    "label": "Flow Type",
                    "required": True,
                    "default": "sequential",
                    "options": [
                        {"value": "sequential", "label": "Sequential"},
                        {"value": "hierarchical", "label": "Hierarchical"}
                    ],
                    "display_order": 2,
                    "show_by_default": True
                },
                "entry_point": {
                    "type": "boolean",
                    "label": "Entry Point",
                    "required": False,
                    "default": False,
                    "display_order": 3,
                    "show_by_default": False
                },
                "exit_point": {
                    "type": "boolean",
                    "label": "Exit Point",
                    "required": False,
                    "default": False,
                    "display_order": 4,
                    "show_by_default": False
                }
            }
        }
    
    @staticmethod
    def _get_connection_constraints() -> Dict[str, Any]:
        """Get connection constraints between node types with field specifications."""
        return {
            "crew": {
                "agents": {
                    "target_type": "agent",
                    "required": True,
                    "min_connections": 1,
                    "max_connections": None,
                    "description": "Agents that are part of this crew"
                },
                "tasks": {
                    "target_type": "task",
                    "required": True,
                    "min_connections": 1,
                    "max_connections": None,
                    "description": "Tasks to be completed by the crew"
                },
                "manager_agent": {
                    "target_type": "agent",
                    "required": False,
                    "min_connections": 0,
                    "max_connections": 1,
                    "description": "Optional manager agent for hierarchical processes"
                },
                "memory": {
                    "target_type": "memory",
                    "required": False,
                    "min_connections": 0,
                    "max_connections": 1,
                    "description": "Optional memory system for the crew"
                }
            },
            "agent": {
                "llm": {
                    "target_type": "llm",
                    "required": True,
                    "min_connections": 1,
                    "max_connections": 1,
                    "description": "Language model used by this agent"
                },
                "tool": {
                    "target_type": "tool",
                    "required": False,
                    "min_connections": 0,
                    "max_connections": None,
                    "description": "Tools available to this agent"
                }
            },
            "task": {
                "agent": {
                    "target_type": "agent",
                    "required": False,
                    "min_connections": 0,
                    "max_connections": 1,
                    "description": "Agent assigned to execute this task"
                },
                "tools": {
                    "target_type": "tool",
                    "required": False,
                    "min_connections": 0,
                    "max_connections": None,
                    "description": "Tools available for this task"
                },
                "context_tasks": {
                    "target_type": "task",
                    "required": False,
                    "min_connections": 0,
                    "max_connections": None,
                    "description": "Tasks that provide context for this task"
                }
            },
            "tool": {},
            "flow": {
                "connected_nodes": {
                    "target_type": "core",
                    "required": False,
                    "min_connections": 0,
                    "max_connections": None,
                    "description": "Core nodes controlled by this flow"
                }
            },
            # LLM providers have no outgoing connections
            "openai": {},
            "anthropic": {},
            "ollama": {},
            "google": {},
            "azure": {},
            "groq": {}
        }
    
    @staticmethod
    def _get_enum_definitions() -> Dict[str, Any]:
        """Get enum definitions for select fields."""
        return {
            "process_types": [
                {"value": "sequential", "label": "Sequential", "description": "Tasks execute one after another"},
                {"value": "hierarchical", "label": "Hierarchical", "description": "Tasks execute in a hierarchy with delegation"}
            ],
            "output_formats": [
                {"value": "raw", "label": "Raw", "description": "Plain text output"},
                {"value": "json", "label": "JSON", "description": "Structured JSON output"},
                {"value": "pydantic", "label": "Pydantic", "description": "Pydantic model output"},
                {"value": "file", "label": "File", "description": "Output to file"}
            ],
            "llm_providers": [
                {"value": "openai", "label": "OpenAI", "description": "OpenAI GPT models"},
                {"value": "anthropic", "label": "Anthropic", "description": "Anthropic Claude models"},
                {"value": "ollama", "label": "Ollama", "description": "Local Ollama models"},
                {"value": "google", "label": "Google AI", "description": "Google Gemini models"},
                {"value": "azure", "label": "Azure OpenAI", "description": "Azure OpenAI Service"},
                {"value": "groq", "label": "Groq", "description": "Groq AI models"}
            ]
        } 