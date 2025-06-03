import { createBrowserRouter } from 'react-router-dom';
import { RootLayout, AuthLayout, AppLayout } from '../layouts/RootLayout';
import { ProtectedRoute, PublicRoute } from '../components/ProtectedRoute';
import { ROUTES } from './routes';
import { RegisterPage } from '@/pages/Register';
import { LoginPage } from '@/pages/Login';
import { GraphsPage } from '@/pages/Graphs';
import { DashboardPage } from '@/pages/Dashboard';
import { GraphEditorPage } from '@/pages/GraphEditor';

// Error boundary component for routes
function RouteErrorBoundary() {
  return (
    <div className='min-h-screen flex items-center justify-center'>
      <div className='text-center space-y-4'>
        <h1 className='text-4xl font-bold text-red-500'>Oops!</h1>
        <p className='text-muted-foreground'>
          Something went wrong with this page.
        </p>
        <button
          onClick={() => (window.location.href = ROUTES.DASHBOARD)}
          className='px-4 py-2 bg-primary text-primary-foreground rounded-md'
        >
          Go Home
        </button>
      </div>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <RouteErrorBoundary />,
    children: [
      // Auth routes with AuthLayout
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
      // Protected app routes with AppLayout
      {
        path: '/',
        element: (
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        ),
        children: [
          {
            index: true, // Dashboard at root "/"
            element: <DashboardPage />,
          },
          {
            path: 'graphs',
            element: <GraphsPage />,
          },
          {
            path: 'graphs/:id',
            element: <GraphEditorPage />,
          },
        ],
      },
    ],
  },
]);

// Export updated route constants
export { ROUTES } from './routes';
