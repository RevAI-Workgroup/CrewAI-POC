export interface Graph {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  metadata?: Record<string, any>;
}

export interface GraphNode {
  id: string;
  type: 'crew' | 'agent' | 'task' | 'llm';
  position: { x: number; y: number };
  data: Record<string, any>;
  label?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  data?: Record<string, any>;
}

export interface NodeDefinition {
  type: string;
  label: string;
  description: string;
  fields: FieldDefinition[];
  validation?: ValidationRule[];
}

export interface FieldDefinition {
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

export interface SelectOption {
  value: string;
  label: string;
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
