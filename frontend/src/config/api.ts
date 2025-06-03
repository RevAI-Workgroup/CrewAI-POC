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
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
  },
  GRAPHS: {
    LIST: '/graphs',
    CREATE: '/graphs',
    GET: (id: string) => `/graphs/${id}`,
    UPDATE: (id: string) => `/graphs/${id}`,
    DELETE: (id: string) => `/graphs/${id}`,
    DUPLICATE: (id: string) => `/graphs/${id}/duplicate`,
  },
  NODES: {
    DEFINITIONS: '/graph-nodes',
    VALIDATE: '/graph-nodes/validate',
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
