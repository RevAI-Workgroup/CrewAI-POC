import { Navigate, useLocation } from 'react-router-dom';
import { ROUTES } from '../router/routes';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();

  // TODO: Replace with actual auth hook when implemented
  const isAuthenticated = false; // Placeholder for useAuth hook

  if (!isAuthenticated) {
    // Redirect to login while preserving intended destination
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Helper component for redirecting authenticated users away from auth pages
export function PublicRoute({ children }: ProtectedRouteProps) {
  // TODO: Replace with actual auth hook when implemented
  const isAuthenticated = false; // Placeholder for useAuth hook

  if (isAuthenticated) {
    // Redirect authenticated users to dashboard
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  return <>{children}</>;
}
