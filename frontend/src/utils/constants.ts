// Authentication constants
export const AUTH_STORAGE_KEY = 'crewai_auth_tokens';
export const USER_STORAGE_KEY = 'crewai_user_data';

// API constants
export const API_ENDPOINTS = {
  AUTH: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
  },
  GRAPHS: {
    LIST: '/graphs',
    CREATE: '/graphs',
    GET: (id: string) => `/graphs/${id}`,
    UPDATE: (id: string) => `/graphs/${id}`,
    DELETE: (id: string) => `/graphs/${id}`,
  },
  NODES: {
    DEFINITIONS: '/graph-nodes',
  },
} as const;

// Validation constants
export const VALIDATION_RULES = {
  PSEUDO: {
    MIN_LENGTH: 1,
    MAX_LENGTH: 100,
  },
  PASSPHRASE: {
    WORD_COUNT: 6,
    SEPARATOR: '-',
  },
  GRAPH_NAME: {
    MIN_LENGTH: 1,
    MAX_LENGTH: 100,
  },
} as const;

// UI constants
export const BREAKPOINTS = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

export const Z_INDEX = {
  MODAL: 1000,
  DROPDOWN: 100,
  TOOLTIP: 50,
  DEFAULT: 1,
} as const;
