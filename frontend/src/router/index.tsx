import { createBrowserRouter } from 'react-router-dom';
import { RootLayout, AuthLayout, AppLayout } from '../layouts/RootLayout';
import { ProtectedRoute, PublicRoute } from '../components/ProtectedRoute';
import { LoginPage, RegisterPage, DashboardPage, GraphsPage } from '../pages/Login';
import { ROUTES } from './routes';

// Error boundary component for routes
function RouteErrorBoundary() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-red-500">Oops!</h1>
        <p className="text-muted-foreground">
          Something went wrong with this page.
        </p>
        <button 
          onClick={() => window.location.href = ROUTES.HOME}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
        >
          Go Home
        </button>
      </div>
    </div>
  );
}

// Home page component (redirects to appropriate page)
function HomePage() {
  // TODO: Replace with actual auth check
  const isAuthenticated = false;
  
  if (isAuthenticated) {
    window.location.href = ROUTES.DASHBOARD;
  } else {
    window.location.href = ROUTES.LOGIN;
  }
  
  return null;
}

export const router = createBrowserRouter([
  {
    path: ROUTES.HOME,
    element: <RootLayout />,
    errorElement: <RouteErrorBoundary />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'auth',
        element: <AuthLayout />,
        children: [
          {
            path: 'login',
            element: (
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            ),
          },
          {
            path: 'register',
            element: (
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            ),
          },
        ],
      },
      {
        path: 'app',
        element: (
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        ),
        children: [
          {
            path: 'dashboard',
            element: <DashboardPage />,
          },
          {
            path: 'graphs',
            element: <GraphsPage />,
          },
          // TODO: Add graph editor route in later tasks
          // {
          //   path: 'graphs/:id/edit',
          //   element: <GraphEditorPage />,
          // },
        ],
      },
    ],
  },
]);

// Update route constants to match nested structure
export const APP_ROUTES = {
  ...ROUTES,
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  DASHBOARD: '/app/dashboard',
  GRAPHS: '/app/graphs',
} as const; 