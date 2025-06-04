import axios from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { apiConfig, TIMEOUTS } from '@/config/api';
import { getAuthCookie } from '@/utils/cookies';

// Create axios instance with base configuration
export const apiClient: AxiosInstance = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: apiConfig.timeout,
  headers: apiConfig.headers,
  withCredentials: true, // Enable cookies for auth
});

// Request interceptor to add tokens to all requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from encrypted cookie
    const { accessToken } = getAuthCookie();
    
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh on 401
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Check if error is 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh tokens
        const { refreshToken } = getAuthCookie();
        
        if (refreshToken) {
          // Import here to avoid circular dependency
          const { refreshTokens } = await import('@/stores/authStore');
          await refreshTokens();
          
          // Retry original request with new token
          const { accessToken: newAccessToken } = getAuthCookie();
          if (newAccessToken) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return apiClient(originalRequest);
          }
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        const { logout } = await import('@/stores/authStore');
        await logout();
        
        // Redirect to login page
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// Export configured axios instance
export default apiClient;

// Utility function to set custom timeout for specific requests
export const withTimeout = (timeout: number) => {
  return axios.create({
    ...apiClient.defaults,
    timeout,
  });
};

// Pre-configured instances for different operation types
export const shortTimeoutApi = withTimeout(TIMEOUTS.SHORT);
export const mediumTimeoutApi = withTimeout(TIMEOUTS.MEDIUM);
export const longTimeoutApi = withTimeout(TIMEOUTS.LONG); 