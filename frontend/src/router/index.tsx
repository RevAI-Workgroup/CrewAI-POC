import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { AuthLayout } from '../layouts/RootLayout';
import { ProtectedRoute, PublicRoute } from '../components/ProtectedRoute';
import { RegisterPage } from '@/pages/Register';
import { LoginPage } from '@/pages/Login';
import { GraphsPage } from '@/pages/Graphs';
import { DashboardPage } from '@/pages/Dashboard';
import { GraphEditorPage } from '@/pages/GraphEditor';
import { AppLayout } from '@/layouts/AppLayout';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { graphsLoader, graphLoader } from './loaders';

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    errorElement: <ErrorBoundary />,
    children: [
      {
        index: true,
        element: <DashboardPage />
      },
      {
        path: "graphs",
        element: <GraphsPage />,
        loader: graphsLoader,
        errorElement: <ErrorBoundary />
      },
      {
        path: "graphs/:id",
        element: <GraphEditorPage />,
        loader: graphLoader,
        errorElement: <ErrorBoundary />
      }
    ]
  },
  {
    path: "/auth",
    element: <AuthLayout />,
    errorElement: <ErrorBoundary />,
    children: [
      {
        path: "login",
        element: (
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        )
      },
      {
        path: "register",
        element: (
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        )
      }
    ]
  },
  {
    path: "*",
    element: <Navigate to="/" replace />
  }
]);

const Router = () => {
  return <RouterProvider router={router} />;
};

export default Router;

// Export route constants
export { ROUTES } from './routes';
