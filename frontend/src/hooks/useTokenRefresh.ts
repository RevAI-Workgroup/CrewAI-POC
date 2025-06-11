import { useEffect, useRef, useCallback } from 'react';
import useAuthStore from '@/stores/authStore';

interface UseTokenRefreshOptions {
  // Time in milliseconds before token expiration to trigger refresh
  refreshBuffer?: number;
  // Interval to check token expiration (in milliseconds)
  checkInterval?: number;
  // Whether to enable automatic refresh
  enabled?: boolean;
}

const DEFAULT_OPTIONS: Required<UseTokenRefreshOptions> = {
  refreshBuffer: 5 * 60 * 1000, // 5 minutes before expiration
  checkInterval: 60 * 1000, // Check every minute
  enabled: true,
};

export const useTokenRefresh = (options: UseTokenRefreshOptions = {}) => {
  const config = { ...DEFAULT_OPTIONS, ...options };
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const refreshingRef = useRef<boolean>(false);
  
  const {
    isAuthenticated,
    tokenExpiresAt,
    refreshTokens,
    logout,
  } = useAuthStore();

  const checkAndRefreshToken = useCallback(async () => {
    // Skip if not authenticated, already refreshing, or disabled
    if (!config.enabled || !isAuthenticated || refreshingRef.current) {
      return;
    }

    // Skip if no expiration time is set
    if (!tokenExpiresAt) {
      return;
    }

    const now = new Date();
    const expirationTime = new Date(tokenExpiresAt);
    const timeUntilExpiration = expirationTime.getTime() - now.getTime();

    // Check if token needs refresh (within buffer time)
    if (timeUntilExpiration <= config.refreshBuffer && timeUntilExpiration > 0) {
      try {
        refreshingRef.current = true;
        await refreshTokens();
        console.debug('Token refreshed automatically');
      } catch (error) {
        console.error('Automatic token refresh failed:', error);
        // Logout user if refresh fails
        await logout();
      } finally {
        refreshingRef.current = false;
      }
    } else if (timeUntilExpiration <= 0) {
      // Token has already expired
      console.warn('Token has expired, logging out user');
      await logout();
    }
  }, [
    config.enabled,
    config.refreshBuffer,
    isAuthenticated,
    tokenExpiresAt,
    refreshTokens,
    logout,
  ]);

  // Setup automatic token refresh interval
  useEffect(() => {
    if (!config.enabled || !isAuthenticated) {
      // Clear existing interval if disabled or not authenticated
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // Initial check
    checkAndRefreshToken();

    // Setup periodic checks
    intervalRef.current = setInterval(checkAndRefreshToken, config.checkInterval);

    // Cleanup on unmount or dependency change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [config.enabled, config.checkInterval, isAuthenticated, checkAndRefreshToken]);

  // Manual refresh function
  const manualRefresh = useCallback(async () => {
    if (!isAuthenticated || refreshingRef.current) {
      return false;
    }

    try {
      refreshingRef.current = true;
      await refreshTokens();
      return true;
    } catch (error) {
      console.error('Manual token refresh failed:', error);
      await logout();
      return false;
    } finally {
      refreshingRef.current = false;
    }
  }, [isAuthenticated, refreshTokens, logout]);

  // Return useful information and utilities
  return {
    isRefreshing: refreshingRef.current,
    manualRefresh,
    tokenExpiresAt,
    timeUntilExpiration: tokenExpiresAt 
      ? Math.max(0, new Date(tokenExpiresAt).getTime() - Date.now())
      : 0,
  };
}; 