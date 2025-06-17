// Route constants for type-safe navigation
export const ROUTES = {
  DASHBOARD: '/',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  GRAPHS: '/graphs', // graphs creation will be from this page and result in redirect to editor page
  GRAPH_EDITOR: '/graphs/:id',
  GRAPH_CHAT: '/graphs/:id/chat',
  GRAPH_CHAT_THREAD: '/graphs/:id/chat/:threadId',
} as const;

// Type for route paths
export type RoutePath = (typeof ROUTES)[keyof typeof ROUTES];

// Route parameter types
export interface GraphParams {
  id: string;
}

export interface GraphChatParams extends Record<string, string | undefined> {
  id: string;
  threadId?: string;
}

// Route configuration types
export interface RouteConfig {
  path: string;
  title: string;
  requiresAuth: boolean;
  element?: React.ComponentType;
}
