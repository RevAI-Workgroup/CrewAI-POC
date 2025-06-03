// Route constants for type-safe navigation
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  GRAPHS: '/graphs',
  GRAPH_EDITOR: '/graphs/:id/edit',
  GRAPH_NEW: '/graphs/new',
} as const;

// Type for route paths
export type RoutePath = typeof ROUTES[keyof typeof ROUTES];

// Route parameter types
export interface GraphParams {
  id: string;
}

// Route configuration types
export interface RouteConfig {
  path: string;
  title: string;
  requiresAuth: boolean;
  element?: React.ComponentType;
} 