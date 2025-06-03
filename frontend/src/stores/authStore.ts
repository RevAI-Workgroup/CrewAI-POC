import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import axios from 'axios';
import { env } from '../config/env';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  RefreshTokenRequest,
} from '../types/auth.types';

interface User {
  id: string;
  pseudo: string;
  role: 'user' | 'admin';
  created_at: string;
  updated_at: string;
  last_login?: string;
}

interface AuthStoreState {
  // State
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  register: (pseudo: string) => Promise<string>;
  login: (passphrase: string) => Promise<void>;
  logout: () => void;
  refreshTokens: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  
  // Internal utilities
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
}

// Get API base URL from centralized environment configuration
const API_BASE_URL = env.API_BASE_URL;

const useAuthStore = create<AuthStoreState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,

    // Actions
    register: async (pseudo: string): Promise<string> => {
      set({ isLoading: true, error: null });
      
      try {
        const requestData: RegisterRequest = { pseudo };
        const response = await axios.post<RegisterResponse>(
          `${API_BASE_URL}/api/auth/register`,
          requestData
        );

        const {
          id,
          pseudo: userPseudo,
          role,
          created_at,
          updated_at,
          access_token,
          refresh_token,
          passphrase,
        } = response.data;

        // Store tokens and user data
        set({
          user: {
            id,
            pseudo: userPseudo,
            role,
            created_at,
            updated_at,
          },
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });

        // Return passphrase for user to save
        return passphrase;
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || 
                           error.response?.data?.message || 
                           'Registration failed. Please try again.';
        
        set({
          error: errorMessage,
          isLoading: false,
          isAuthenticated: false,
        });
        
        throw new Error(errorMessage);
      }
    },

    login: async (passphrase: string): Promise<void> => {
      set({ isLoading: true, error: null });
      
      try {
        const requestData: LoginRequest = { passphrase };
        const response = await axios.post<LoginResponse>(
          `${API_BASE_URL}/api/auth/login`,
          requestData
        );

        const { user, access_token, refresh_token } = response.data;

        set({
          user,
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || 
                           error.response?.data?.message || 
                           'Invalid passphrase. Please check your passphrase and try again.';
        
        set({
          error: errorMessage,
          isLoading: false,
          isAuthenticated: false,
          user: null,
          accessToken: null,
          refreshToken: null,
        });
        
        throw new Error(errorMessage);
      }
    },

    logout: () => {
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        error: null,
      });
    },

    refreshTokens: async (): Promise<void> => {
      const { refreshToken } = get();
      
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      try {
        const requestData: RefreshTokenRequest = { 
          refresh_token: refreshToken 
        };
        
        const response = await axios.post<LoginResponse>(
          `${API_BASE_URL}/api/auth/refresh`,
          requestData
        );

        const { access_token, refresh_token } = response.data;

        set({
          accessToken: access_token,
          refreshToken: refresh_token,
          error: null,
        });
      } catch (error: any) {
        // Refresh failed, logout user
        console.error('Token refresh failed:', error);
        get().logout();
        throw new Error('Session expired. Please log in again.');
      }
    },

    clearError: () => set({ error: null }),

    setLoading: (isLoading: boolean) => set({ isLoading }),

    // Internal utilities
    setTokens: (accessToken: string, refreshToken: string) => {
      set({ accessToken, refreshToken });
    },

    setUser: (user: User) => {
      set({ user, isAuthenticated: true });
    },
  }))
);

// Set up automatic token refresh before expiration
useAuthStore.subscribe(
  (state) => state.accessToken,
  (accessToken) => {
    if (accessToken) {
      try {
        // Decode JWT to get expiration time
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        const expiresAt = payload.exp * 1000; // Convert to milliseconds
        const now = Date.now();
        const refreshBuffer = 60000; // Refresh 1 minute before expiration
        const timeUntilRefresh = expiresAt - now - refreshBuffer;

        if (timeUntilRefresh > 0) {
          setTimeout(() => {
            const currentState = useAuthStore.getState();
            if (currentState.isAuthenticated && currentState.refreshToken) {
              currentState.refreshTokens().catch((error) => {
                console.error('Automatic token refresh failed:', error);
              });
            }
          }, timeUntilRefresh);
        }
      } catch (error) {
        console.error('Failed to parse access token for auto-refresh:', error);
      }
    }
  }
);

export default useAuthStore;

// Export convenience functions for use outside React components
export const login = (passphrase: string) => 
  useAuthStore.getState().login(passphrase);

export const register = (pseudo: string) => 
  useAuthStore.getState().register(pseudo);

export const logout = () => 
  useAuthStore.getState().logout();

export const refreshTokens = () => 
  useAuthStore.getState().refreshTokens();

export const clearAuthError = () => 
  useAuthStore.getState().clearError(); 