import { env } from './env';

// API Configuration
export const apiConfig = {
  baseURL: env.API_BASE_URL,
  timeout: env.API_TIMEOUT,
  wsBaseURL: env.WS_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
} as const;

// API Endpoints
export const API_ROUTES = {
  AUTH: {
    REGISTER: '/api/auth/register',
    LOGIN: '/api/auth/login',
    REFRESH: '/api/auth/refresh',
    LOGOUT: '/api/auth/logout',
  },
  GRAPHS: {
    LIST: '/api/graphs',
    CREATE: '/api/graphs',
    GET: (id: string) => `/api/graphs/${id}`,
    UPDATE: (id: string) => `/api/graphs/${id}`,
    DELETE: (id: string) => `/api/graphs/${id}`,
    DUPLICATE: (id: string) => `/api/graphs/${id}/duplicate`,
  },
  NODES: {
    DEFINITIONS: '/api/graph-nodes',
    VALIDATE: '/api/graph-nodes/validate',
  },
  WEBSOCKET: {
    GRAPHS: '/ws/graphs',
    NOTIFICATIONS: '/ws/notifications',
  },
} as const;

// Request timeout configurations for different operations
export const TIMEOUTS = {
  SHORT: 5000, // Quick operations (login, logout)
  MEDIUM: 15000, // Standard operations (CRUD)
  LONG: 60000, // Heavy operations (graph processing)
} as const;
