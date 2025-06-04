import React, { useEffect } from 'react';
import type { ReactNode } from 'react';
import useAuthStore from '@/stores/authStore';
import { useTokenRefresh } from '@/hooks/useTokenRefresh';

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const { initializeAuth, isAuthenticated } = useAuthStore();
  
  // Initialize authentication on app startup
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);
  
  // Enable automatic token refresh when authenticated
  useTokenRefresh({
    enabled: isAuthenticated,
    refreshBuffer: 5 * 60 * 1000, // Refresh 5 minutes before expiration
    checkInterval: 60 * 1000, // Check every minute
  });

  return <>{children}</>;
}; 