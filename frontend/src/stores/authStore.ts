import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import apiClient from '@/services/api';
import { setAuthCookie, getAuthCookie, clearAuthCookie } from '@/utils/cookies';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  User,
} from '../types/auth.types';
import { API_ROUTES } from '@/config/api';

interface AuthData {
  user: User;
  accessToken: string;
  refreshToken: string;
  tokenExpiresAt: Date;
}

interface AuthStoreState {
  // State
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  tokenExpiresAt: Date | null;
  
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitializing: boolean;
  error: string | null;

  // Actions
  register: (pseudo: string) => Promise<{ passphrase: string; authData: AuthData }>;
  login: (passphrase: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  completeRegistration: (authData: AuthData) => void;
  
  // Internal utilities
  setUser: (user: User) => void;
  isTokenValid: () => boolean;
  initializeAuth: () => void;
}

const useAuthStore = create<AuthStoreState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    user: null,
    accessToken: null,
    refreshToken: null,
    tokenExpiresAt: null,
    isAuthenticated: false,
    isLoading: false,
    isInitializing: true,
    error: null,

    // Actions
    register: async (pseudo: string): Promise<{ passphrase: string; authData: AuthData }> => {
      set({ isLoading: true, error: null });
      
      try {
        const requestData: RegisterRequest = { pseudo };
        const response = await apiClient.post<RegisterResponse>(
          API_ROUTES.AUTH.REGISTER,
          requestData
        );

        const {
          id,
          pseudo: userPseudo,
          role,
          created_at,
          updated_at,
          passphrase,
          access_token,
          refresh_token,
          expires_in,
        } = response.data;

        // Calculate token expiration time
        const expiresAt = new Date(Date.now() + expires_in * 1000);
        
        // Prepare auth data but don't store it yet
        const authData: AuthData = {
          user: {
            id,
            pseudo: userPseudo,
            role,
            created_at,
            updated_at,
          },
          accessToken: access_token,
          refreshToken: refresh_token,
          tokenExpiresAt: expiresAt,
        };

        set({
          isLoading: false,
          error: null,
        });

        // Return passphrase and auth data (don't auto-login)
        return { passphrase, authData };
      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.detail || 
                           axiosError.response?.data?.message || 
                           'Registration failed. Please try again.';
        
        set({
          error: errorMessage,
          isLoading: false,
          isAuthenticated: false,
        });
        
        throw new Error(errorMessage);
      }
    },

    completeRegistration: (authData: AuthData) => {
      // Store auth data in encrypted cookie and update state
      setAuthCookie(
        authData.accessToken,
        authData.refreshToken,
        authData.tokenExpiresAt,
        authData.user
      );

      set({
        user: authData.user,
        accessToken: authData.accessToken,
        refreshToken: authData.refreshToken,
        tokenExpiresAt: authData.tokenExpiresAt,
        isAuthenticated: true,
        isInitializing: false,
        error: null,
      });
    },

    login: async (passphrase: string): Promise<void> => {
      set({ isLoading: true, error: null });
      
      try {
        const requestData: LoginRequest = { passphrase };
        const response = await apiClient.post<LoginResponse>(
          API_ROUTES.AUTH.LOGIN,
          requestData
        );

        // Store user data and tokens from the response
        const { user, access_token, refresh_token, expires_in } = response.data;
        
        // Calculate token expiration time
        const expiresAt = new Date(Date.now() + expires_in * 1000);
        
        // Store in encrypted cookie for persistence
        setAuthCookie(access_token, refresh_token, expiresAt, user);
        
        set({
          user: {
            id: user.id,
            pseudo: user.pseudo,
            role: user.role,
            created_at: user.created_at,
            updated_at: user.updated_at,
            last_login: user.last_login,
          },
          accessToken: access_token,
          refreshToken: refresh_token,
          tokenExpiresAt: expiresAt,
          isAuthenticated: true,
          isLoading: false,
          isInitializing: false,
          error: null,
        });
      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.detail ||
                           axiosError.response?.data?.message ||
                           'Invalid passphrase. Please check your passphrase and try again.';
        
        set({
          error: errorMessage,
          isLoading: false,
          isAuthenticated: false,
          isInitializing: false,
          user: null,
          accessToken: null,
          refreshToken: null,
          tokenExpiresAt: null,
        });
        
        throw new Error(errorMessage);
      }
    },

    logout: async (): Promise<void> => {
      try {
        // Call logout endpoint to clear server-side session
        clearAuthCookie();
      } catch (error) {
        console.error('Logout failed:', error);
      } finally {
        
        // Clear local state regardless of API call success
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          tokenExpiresAt: null,
          isAuthenticated: false,
          isInitializing: false,
          error: null,
        });
      }
    },

    refreshTokens: async (): Promise<void> => {
      try {
        const response = await apiClient.post<LoginResponse>(
          API_ROUTES.AUTH.REFRESH, {
            refresh_token: get().refreshToken,
          }
        );

        // Store updated user data and tokens from the refresh response
        const { user, access_token, refresh_token, expires_in } = response.data;
        
        // Calculate token expiration time
        const expiresAt = new Date(Date.now() + expires_in * 1000);
        
        // Update encrypted cookie
        setAuthCookie(access_token, refresh_token, expiresAt, user);

        set({
          user: {
            id: user.id,
            pseudo: user.pseudo,
            role: user.role,
            created_at: user.created_at,
            updated_at: user.updated_at,
            last_login: user.last_login,
          },
          accessToken: access_token,
          refreshToken: refresh_token,
          tokenExpiresAt: expiresAt,
          isAuthenticated: true,
          error: null,
        });
      } catch (error: unknown) {
        // Refresh failed, logout user
        console.error('Token refresh failed:', error);
        await get().logout();
        throw new Error('Session expired. Please log in again.');
      }
    },

    clearError: () => set({ error: null }),

    setLoading: (isLoading: boolean) => set({ isLoading }),

    // Internal utilities
    setUser: (user: User) => {
      set({ user, isAuthenticated: true });
    },

    isTokenValid: (): boolean => {
      const { tokenExpiresAt } = get();
      if (!tokenExpiresAt) return false;
      return new Date() < tokenExpiresAt;
    },

    initializeAuth: () => {
      try {
        const { user, accessToken, refreshToken, tokenExpiresAt } = getAuthCookie();

        if (user && accessToken && refreshToken && tokenExpiresAt) {
          // Check if token is still valid
          if (new Date() < tokenExpiresAt) {
            set({
              user: user as User,
              accessToken,
              refreshToken,
              tokenExpiresAt,
              isAuthenticated: true,
              isInitializing: false,
              error: null,
            });
          } else {
            // Token expired, try to refresh
            get().refreshTokens().catch(() => {
              // If refresh fails, clear stored data and complete initialization
              get().logout();
            }).finally(() => {
              set({ isInitializing: false });
            });
          }
        } else {
          // No auth data found, complete initialization
          set({ isInitializing: false });
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error);
        // Clear potentially corrupted data and complete initialization
        get().logout();
      }
    },

  }))
);

// Export convenience functions for use outside React components
export const login = (passphrase: string) => 
  useAuthStore.getState().login(passphrase);

export const register = (pseudo: string) => 
  useAuthStore.getState().register(pseudo);

export const logout = () => 
  useAuthStore.getState().logout();

export const refreshTokens = () => 
  useAuthStore.getState().refreshTokens();

export default useAuthStore; 