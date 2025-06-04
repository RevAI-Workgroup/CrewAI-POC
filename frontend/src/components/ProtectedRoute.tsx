import { Navigate, useLocation } from 'react-router-dom';
import { ROUTES } from '../router/routes';
import useAuthStore from '../stores/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

// Loading component for auth initialization
function AuthLoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center space-y-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, isTokenValid, isInitializing } = useAuthStore();

  // Show loading spinner while auth is initializing
  if (isInitializing) {
    return <AuthLoadingSpinner />;
  }

  // Check if user is authenticated and token is valid
  if (!isAuthenticated || !isTokenValid()) {
    // Redirect to login while preserving intended destination
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Helper component for redirecting authenticated users away from auth pages
export function PublicRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isTokenValid, isInitializing } = useAuthStore();

  // Show loading spinner while auth is initializing
  if (isInitializing) {
    return <AuthLoadingSpinner />;
  }

  // Check if user is authenticated and token is valid
  if (isAuthenticated && isTokenValid()) {
    // Redirect authenticated users to dashboard
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  return <>{children}</>;
}
