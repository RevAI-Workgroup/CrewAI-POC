// Environment configuration and validation
export interface EnvConfig {
  API_BASE_URL: string;
  API_TIMEOUT: number;
  APP_ENV: 'development' | 'staging' | 'production';
  ENABLE_DEVTOOLS: boolean;
  ENABLE_DEBUG: boolean;
  WS_BASE_URL: string;
}

const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = import.meta.env[key] ?? defaultValue;
  if (!value) {
    throw new Error(`Environment variable ${key} is required but not set`);
  }
  return value;
};

const getBooleanEnvVar = (key: string, defaultValue = false): boolean => {
  const value = import.meta.env[key];
  if (value === undefined) return defaultValue;
  return value === 'true' || value === '1';
};

const getNumberEnvVar = (key: string, defaultValue?: number): number => {
  const value = import.meta.env[key];
  if (value === undefined && defaultValue !== undefined) return defaultValue;
  const parsed = Number(value);
  if (isNaN(parsed)) {
    throw new Error(`Environment variable ${key} must be a valid number`);
  }
  return parsed;
};

// Validate and export environment configuration
export const env: EnvConfig = {
  API_BASE_URL: getEnvVar('VITE_API_BASE_URL', 'http://localhost:8000'),
  API_TIMEOUT: getNumberEnvVar('VITE_API_TIMEOUT', 30000),
  APP_ENV: getEnvVar('VITE_APP_ENV', 'development') as EnvConfig['APP_ENV'],
  ENABLE_DEVTOOLS: getBooleanEnvVar('VITE_ENABLE_DEVTOOLS', true),
  ENABLE_DEBUG: getBooleanEnvVar('VITE_ENABLE_DEBUG', false),
  WS_BASE_URL: getEnvVar('VITE_WS_BASE_URL', 'ws://localhost:8000'),
};

// Environment checks
export const isDevelopment = env.APP_ENV === 'development';
export const isProduction = env.APP_ENV === 'production';
export const isStaging = env.APP_ENV === 'staging';

// Validate configuration on module load
if (!['development', 'staging', 'production'].includes(env.APP_ENV)) {
  throw new Error(
    `Invalid APP_ENV: ${env.APP_ENV}. Must be development, staging, or production.`
  );
}

console.info('Environment configuration loaded:', {
  APP_ENV: env.APP_ENV,
  API_BASE_URL: env.API_BASE_URL,
  ENABLE_DEBUG: env.ENABLE_DEBUG,
});
