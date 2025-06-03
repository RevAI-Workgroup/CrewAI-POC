export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface CreateGraphRequest {
  name: string;
  description?: string;
}

export interface UpdateGraphRequest {
  name?: string;
  description?: string;
  nodes?: any[];
  edges?: any[];
}

export interface GraphListResponse {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  node_count: number;
}

export interface NodeDefinitionsResponse {
  crew: any;
  agent: any;
  task: any;
  llm: any;
}

export interface ApiRequestConfig {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  url: string;
  data?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
}
