import { useShallow } from 'zustand/react/shallow';
import useAuthStore from '../stores/authStore';

/**
 * Custom hook for authentication state and actions
 * Provides a clean interface to the Zustand auth store with optimized selectors
 */
export const useAuth = () => {
  // Use useShallow to prevent unnecessary re-renders
  const authState = useAuthStore(
    useShallow((state) => ({
      user: state.user,
      isAuthenticated: state.isAuthenticated,
      isLoading: state.isLoading,
      error: state.error,
      accessToken: state.accessToken,
    }))
  );

  // Get actions separately to prevent re-renders when they change
  const actions = useAuthStore(
    useShallow((state) => ({
      register: state.register,
      login: state.login,
      logout: state.logout,
      refreshTokens: state.refreshTokens,
      clearError: state.clearError,
      setLoading: state.setLoading,
    }))
  );

  return {
    // State
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    error: authState.error,
    accessToken: authState.accessToken,
    
    // Computed values
    userPseudo: authState.user?.pseudo,
    userRole: authState.user?.role,
    hasError: !!authState.error,
    
    // Actions
    register: actions.register,
    login: actions.login,
    logout: actions.logout,
    refreshTokens: actions.refreshTokens,
    clearError: actions.clearError,
    setLoading: actions.setLoading,
  };
};

/**
 * Hook to get only authentication status (optimized for header/nav components)
 */
export const useAuthStatus = () => {
  return useAuthStore(
    useShallow((state) => ({
      isAuthenticated: state.isAuthenticated,
      isLoading: state.isLoading,
    }))
  );
};

/**
 * Hook to get only user information (optimized for profile components)
 */
export const useAuthUser = () => {
  return useAuthStore((state) => state.user);
};

/**
 * Hook to get only authentication error (optimized for error display components)
 */
export const useAuthError = () => {
  const error = useAuthStore((state) => state.error);
  const clearError = useAuthStore((state) => state.clearError);
  
  return {
    error,
    clearError,
    hasError: !!error,
  };
};

/**
 * Hook to get authentication actions only (for forms and buttons)
 */
export const useAuthActions = () => {
  return useAuthStore(
    useShallow((state) => ({
      register: state.register,
      login: state.login,
      logout: state.logout,
      clearError: state.clearError,
    }))
  );
}; 