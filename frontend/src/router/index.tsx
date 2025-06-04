import { Routes, Route } from 'react-router-dom';
import { AuthLayout } from '../layouts/RootLayout';
import { ProtectedRoute, PublicRoute } from '../components/ProtectedRoute';
import { RegisterPage } from '@/pages/Register';
import { LoginPage } from '@/pages/Login';
import { GraphsPage } from '@/pages/Graphs';
import { DashboardPage } from '@/pages/Dashboard';
import { GraphEditorPage } from '@/pages/GraphEditor';
import { AppLayout } from '@/layouts/AppLayout';

// Router component using Routes instead of createBrowserRouter
const Router = () => {
  return (
    <Routes>
        {/* Auth routes with AuthLayout */}
        <Route path="auth" element={<AuthLayout />}>
          <Route 
            path="login" 
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            } 
          />
          <Route 
            path="register" 
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            } 
          />
        </Route>

        {/* Protected app routes with AppLayout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="graphs" element={<GraphsPage />} />
        <Route
          path="graphs/:id"
          element={<GraphEditorPage />}
        />
      </Route>
    </Routes>
  );
};

export default Router;

// Export route constants
export { ROUTES } from './routes';
