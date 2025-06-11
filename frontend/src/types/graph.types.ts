export interface Graph {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  // Backend stores graph structure in graph_data JSON field
  graph_data?: {
    nodes: GraphNode[];
    edges: GraphEdge[];
    metadata?: Record<string, any>;
  };
  // Legacy direct properties for backward compatibility
  nodes?: GraphNode[];
  edges?: GraphEdge[];
  metadata?: Record<string, any>;
}

export interface GraphNode {
  id: string;
  type: 'crew' | 'agent' | 'task' | 'tool' | 'flow' | 'openai' | 'anthropic' | 'ollama' | 'google' | 'azure' | 'groq';
  position: { x: number; y: number };
  data: Record<string, any>;
  label?: string;
  // Enhanced storage fields for better relationship tracking
  category?: string; // Node category from definition
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  data?: Record<string, any>;
}

// API Response Types
export interface NodeDefinitions {
  categories: NodeCategory[];
  node_types: Record<string, NodeTypeDefinition>;
  connection_constraints: Record<string, ConnectionConstraint>;
  enums: EnumDefinitions;
}

export interface NodeCategory {
  id: string;
  name: string;
  description: string;
  nodes: string[];
}

export interface NodeTypeDefinition {
  name: string;
  description: string;
  icon: string;
  color: string;
  category: string;
  provider?: string;
  fields: Record<string, FieldDefinition>;
}

export interface FieldDefinition {
  type: 'string' | 'text' | 'select' | 'multi_select' | 'number' | 'boolean' | 'slider' | 'password' | 'json';
  label: string;
  required: boolean;
  default?: any;
  placeholder?: string;
  display_order: number;
  show_by_default: boolean;
  options?: SelectOption[];
  source?: string;
  filter?: Record<"type" | "category", string | string[]>;
  validation?: FieldValidation;
  description?: string;
  condition?: FieldCondition;
}

export interface SelectOption {
  value: string;
  label: string;
}

export interface FieldValidation {
  min?: number;
  max?: number;
  step?: number;
  min_items?: number;
  max_items?: number;
}

export interface FieldCondition {
  field: string;
  value: any;
}

export interface ConnectionConstraint {
  [fieldName: string]: {
    target_type: string;
    required: boolean;
    min_connections: number;
    max_connections: number | null;
    description: string;
  };
}

export interface EnumDefinitions {
  process_types: EnumOption[];
  output_formats: EnumOption[];
  llm_providers: EnumOption[];
}

export interface EnumOption {
  value: string;
  label: string;
  description: string;
}

// Legacy types (deprecated - use NodeTypeDefinition instead)
export interface NodeDefinition {
  type: string;
  label: string;
  description: string;
  fields: LegacyFieldDefinition[];
  validation?: ValidationRule[];
}

export interface LegacyFieldDefinition {
  name: string;
  type: 'text' | 'textarea' | 'select' | 'number' | 'boolean' | 'array';
  label: string;
  required: boolean;
  options?: SelectOption[];
  default?: any;
  placeholder?: string;
  validation?: ValidationRule[];
  visibility?: VisibilityCondition[];
}

export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value?: any;
  message: string;
}

export interface VisibilityCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'not_contains';
  value: any;
}
