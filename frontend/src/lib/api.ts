import axios from 'axios';
import { env } from '../config/env';

// Create axios instance with base configuration
const api = axios.create({
  // In development, use relative URLs (handled by Vite proxy)
  // In production, use the full API URL
  baseURL: env.APP_ENV === 'development' ? '' : env.API_BASE_URL,
  timeout: env.API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': location.origin,
  },
});

// Request interceptor for adding auth tokens
api.interceptors.request.use(
  (config) => {
    // Get token from auth store if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('[API] Response error:', error);
    
    // Handle 401 Unauthorized - token expired
    if (error.response?.status === 401) {
      // Clear auth state and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

export default api;

// Export configured instance as named export too
export { api }; 