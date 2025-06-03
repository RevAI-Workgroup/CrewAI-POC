// Common types for the application
export interface User {
  id: string;
  pseudo: string;
  role: 'user' | 'admin';
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: Record<string, any>;
}

// Re-export specific type modules
export * from './auth.types';
export * from './graph.types';
export * from './api.types';
