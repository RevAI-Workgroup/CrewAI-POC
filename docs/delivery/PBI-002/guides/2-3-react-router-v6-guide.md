# React Router v6 Guide for Task 2-3

**Date**: 2024-12-27  
**Task**: [2-3 React Router v6 Setup](mdc:../PBI-002-3.md)  
**Official Docs**: https://reactrouter.com/en/main

## Key Features for Our Implementation

### 1. Data Router Pattern (Recommended)
```typescript
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { path: "dashboard", element: <Dashboard /> },
      { path: "graphs", element: <GraphList /> },
    ],
  },
]);

// In main.tsx
<RouterProvider router={router} />
```

### 2. Protected Routes Implementation
```typescript
// ProtectedRoute wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

// In route config
{
  path: "/dashboard",
  element: <ProtectedRoute><Dashboard /></ProtectedRoute>
}
```

### 3. Navigation Hooks
```typescript
import { useNavigate, useLocation } from 'react-router-dom';

// Programmatic navigation
const navigate = useNavigate();
navigate('/dashboard');

// Current location access
const location = useLocation();
```

### 4. Route Definitions Structure
```typescript
// routes.ts - Centralized route constants
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register', 
  DASHBOARD: '/dashboard',
  GRAPHS: '/graphs',
  GRAPH_EDITOR: '/graphs/:id/edit',
} as const;
```

### 5. Error Boundaries
```typescript
// Route-level error boundary
{
  path: "/dashboard",
  element: <Dashboard />,
  errorElement: <ErrorBoundary />,
}
```

### 6. Nested Layouts
```typescript
// Layout with Outlet for child routes
function Layout() {
  return (
    <div>
      <Header />
      <Sidebar />
      <main>
        <Outlet /> {/* Child routes render here */}
      </main>
    </div>
  );
}
```

## Installation
```bash
bun add react-router-dom
bun add -D @types/react-router-dom  # If needed
```

## TypeScript Support
- React Router v6 has built-in TypeScript support
- Type-safe route parameters with generics
- Proper typing for navigation and location hooks

## Authentication Integration
- Use route loaders for authentication checks
- Implement redirect logic in protected route wrapper
- Store intended route for post-login navigation

## Best Practices
1. Use data router pattern (createBrowserRouter)
2. Centralize route definitions
3. Implement proper error boundaries
4. Use nested layouts for consistent UI
5. Type-safe route parameters and navigation

## Sources
- [React Router v6 Official Documentation](https://reactrouter.com/en/main)
- [Data Router Guide](https://reactrouter.com/en/main/routers/create-browser-router)
- [Authentication Examples](https://reactrouter.com/en/main/start/examples) 