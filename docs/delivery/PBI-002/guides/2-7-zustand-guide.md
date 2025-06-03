# Zustand Package Guide - Task 2-7

**Date Created**: 2024-12-19  
**Task**: PBI-002-7 - Authentication Store with Zustand  
**Package Version**: zustand@^4.5.0  

## Package Overview

Zustand is a lightweight, unopinionated state management library for React applications. It provides a simple API based on hooks without the boilerplate typically associated with Redux. Zustand embraces immutability by default and offers fine-grained reactivity with proxy-based dependency tracking.

**Key Benefits**:
- Minimal boilerplate code
- TypeScript-first design
- No providers needed
- Works outside React components
- Built-in shallow comparison utilities
- Middleware support (persist, devtools)

## Installation

```bash
bun add zustand
```

## Core API Reference

### Basic Store Creation

```typescript
import { create } from 'zustand'

interface CounterState {
  count: number
  increment: () => void
  decrement: () => void
}

const useCounterStore = create<CounterState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
}))
```

### State Selection and Usage

```typescript
// Get whole state
const state = useCounterStore()

// Select specific values (recommended)
const count = useCounterStore((state) => state.count)
const increment = useCounterStore((state) => state.increment)

// Select multiple values
const { count, increment } = useCounterStore((state) => ({
  count: state.count,
  increment: state.increment,
}))
```

### Performance Optimization with Shallow Comparison

```typescript
import { shallow } from 'zustand/shallow'

// Prevent unnecessary re-renders
const { count, increment } = useCounterStore(
  (state) => ({ count: state.count, increment: state.increment }),
  shallow
)
```

## Authentication Store Patterns

### Basic Auth Store Structure

```typescript
interface User {
  id: string
  pseudo: string
  role: 'user' | 'admin'
  created_at: string
  updated_at: string
  last_login?: string
}

interface AuthState {
  // State
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  register: (pseudo: string) => Promise<void>
  login: (passphrase: string) => Promise<void>
  logout: () => void
  refreshTokens: () => Promise<void>
  clearError: () => void
  setLoading: (loading: boolean) => void
}
```

### Authentication Implementation Pattern

```typescript
import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import axios from 'axios'

const useAuthStore = create<AuthState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,

    // Actions
    register: async (pseudo: string) => {
      set({ isLoading: true, error: null })
      try {
        const response = await axios.post('/auth/register', { pseudo })
        const { user, access_token, refresh_token, passphrase } = response.data
        
        set({
          user,
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
          isLoading: false,
        })
        
        // Return passphrase for user to save
        return passphrase
      } catch (error) {
        set({
          error: error.response?.data?.message || 'Registration failed',
          isLoading: false,
        })
        throw error
      }
    },

    login: async (passphrase: string) => {
      set({ isLoading: true, error: null })
      try {
        const response = await axios.post('/auth/login', { passphrase })
        const { user, access_token, refresh_token } = response.data
        
        set({
          user,
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
          isLoading: false,
        })
      } catch (error) {
        set({
          error: error.response?.data?.message || 'Login failed',
          isLoading: false,
        })
        throw error
      }
    },

    logout: () => {
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        error: null,
      })
    },

    refreshTokens: async () => {
      const { refreshToken } = get()
      if (!refreshToken) throw new Error('No refresh token available')
      
      try {
        const response = await axios.post('/auth/refresh', {
          refresh_token: refreshToken,
        })
        const { access_token, refresh_token } = response.data
        
        set({
          accessToken: access_token,
          refreshToken: refresh_token,
        })
      } catch (error) {
        // Refresh failed, logout user
        get().logout()
        throw error
      }
    },

    clearError: () => set({ error: null }),
    setLoading: (isLoading: boolean) => set({ isLoading }),
  }))
)
```

## Advanced Patterns

### Store Subscriptions (for token refresh)

```typescript
// Auto-refresh tokens before expiration
useAuthStore.subscribe(
  (state) => state.accessToken,
  (accessToken) => {
    if (accessToken) {
      // Set up token refresh timer
      const payload = JSON.parse(atob(accessToken.split('.')[1]))
      const expiresIn = payload.exp * 1000 - Date.now() - 60000 // 1 min buffer
      
      setTimeout(() => {
        useAuthStore.getState().refreshTokens()
      }, expiresIn)
    }
  }
)
```

### Custom Hooks Pattern

```typescript
// Custom hook for easier usage
export const useAuth = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const isLoading = useAuthStore((state) => state.isLoading)
  const error = useAuthStore((state) => state.error)
  
  const login = useAuthStore((state) => state.login)
  const register = useAuthStore((state) => state.register)
  const logout = useAuthStore((state) => state.logout)
  const clearError = useAuthStore((state) => state.clearError)
  
  return {
    // State
    isAuthenticated,
    user,
    isLoading,
    error,
    
    // Actions
    login,
    register,
    logout,
    clearError,
  }
}
```

### Store Persistence (Token Storage)

```typescript
import { persist, createJSONStorage } from 'zustand/middleware'

const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // ... store implementation
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
)
```

## TypeScript Best Practices

### Strict Type Safety

```typescript
// Use strict interfaces
interface RegisterRequest {
  pseudo: string
}

interface RegisterResponse {
  id: string
  pseudo: string
  role: 'user' | 'admin'
  passphrase: string
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
  created_at: string
  updated_at: string
}

// Type API calls
const register = async (pseudo: string): Promise<string> => {
  const response = await axios.post<RegisterResponse>('/auth/register', {
    pseudo,
  } as RegisterRequest)
  return response.data.passphrase
}
```

### Store Type Utilities

```typescript
// Extract state and actions types
type AuthActions = Pick<AuthState, 'login' | 'register' | 'logout' | 'refreshTokens'>
type AuthData = Omit<AuthState, keyof AuthActions>
```

## Testing Strategies

### Store Testing

```typescript
import { renderHook, act } from '@testing-library/react'
import { useAuthStore } from './authStore'

beforeEach(() => {
  useAuthStore.setState({
    user: null,
    accessToken: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  })
})

test('should handle login success', async () => {
  const { result } = renderHook(() => useAuthStore())
  
  await act(async () => {
    await result.current.login('test-passphrase')
  })
  
  expect(result.current.isAuthenticated).toBe(true)
  expect(result.current.user).toBeDefined()
})
```

## Common Gotchas

1. **Avoid Object References**: Don't select objects directly, use shallow comparison
2. **State Updates**: Always return new objects from set functions
3. **Async Actions**: Handle loading and error states properly
4. **Token Expiration**: Implement automatic token refresh
5. **Memory Leaks**: Unsubscribe from store subscriptions when components unmount

## Performance Tips

1. Use selectors to prevent unnecessary re-renders
2. Implement shallow comparison for object selections
3. Split large stores into smaller, focused stores
4. Use computed values for derived state
5. Leverage Zustand's subscribe API for side effects

## Official Documentation

- **Zustand GitHub**: https://github.com/pmndrs/zustand
- **Documentation**: https://docs.pmnd.rs/zustand/getting-started/introduction
- **TypeScript Guide**: https://docs.pmnd.rs/zustand/guides/typescript

## Source Links

- [Zustand TypeScript Guide 2024](https://tillitsdone.com/blogs/zustand-typescript-guide-2024/)
- [Authentication with Zustand](https://blog.stackademic.com/zustand-for-authentication-in-react-apps-156b6294129c)
- [Session Management with Zustand](https://medium.com/@jkc5186/managing-user-sessions-with-zustand-in-react-5bf30f6bc536)
- [React State Management with Zustand](https://refine.dev/blog/zustand-react-state/) 