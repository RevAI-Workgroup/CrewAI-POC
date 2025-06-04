# Error Boundary Testing Guide

**Date**: 2024-12-27  
**Task**: [2-19 Graph Store and Grid UI](mdc:../PBI-002-19.md)  
**Component**: ErrorBoundary for Router Error Handling

## Overview

The ErrorBoundary component provides user-friendly error pages for React Router errors, including 404 (not found) and general application errors.

## Features

### 1. Route Error Handling
- **404 Errors**: Custom "Page Not Found" message for non-existent routes
- **Graph Not Found**: Specific messaging when graph IDs don't exist
- **General Errors**: Fallback handling for unexpected server errors

### 2. User Experience
- **Navigation Options**: "Go Home" and "Try Again" buttons
- **Responsive Design**: Works on mobile and desktop
- **Contextual Messages**: Different messages for different error types

### 3. Developer Experience
- **Error Details**: Shows error stack traces in development mode
- **Debug Information**: Expandable error details for troubleshooting

## Testing the Error Boundary

### Test Case 1: Non-existent Graph
1. Navigate to: `http://localhost:5173/graphs/non-existent-id`
2. Expected: 404 error page with "Page Not Found" message
3. Actions available: "Go Home" and "Try Again" buttons

### Test Case 2: Network Error Simulation
1. Disconnect from network
2. Navigate to: `http://localhost:5173/graphs`
3. Expected: Error boundary catches network error
4. Actions available: Retry and navigation options

### Test Case 3: Invalid Graph ID Format
1. Navigate to: `http://localhost:5173/graphs/invalid-uuid-format`
2. Expected: Error boundary handles API validation error
3. User sees friendly error message instead of technical details

## Implementation Details

### Router Configuration
```typescript
{
  path: "graphs/:id",
  element: <GraphEditorPage />,
  loader: graphLoader,
  errorElement: <ErrorBoundary />  // Catches loader errors
}
```

### Error Types Handled
- **Route Errors**: `isRouteErrorResponse(error)` - HTTP status codes
- **JavaScript Errors**: General Error objects from failed API calls
- **Network Errors**: Axios/fetch failures

### Error Sources
1. **Router Loaders**: `graphLoader`, `graphsLoader`
2. **API Calls**: Graph store methods throwing errors
3. **Component Errors**: React component lifecycle errors

## Error Flow

1. **Loader Execution**: Router calls loader (e.g., `graphLoader`)
2. **API Call**: Loader calls store method (e.g., `fetchGraphById`)
3. **Error Thrown**: Store method throws error for failed API call
4. **Router Catches**: Router catches error from loader
5. **Error Boundary**: Router renders ErrorBoundary instead of page
6. **User Interface**: User sees friendly error page with options

## Benefits

- **User-Friendly**: No more blank pages or console errors
- **Accessible**: Proper error messaging for all user types
- **Debuggable**: Development mode shows technical details
- **Navigable**: Users can easily recover from errors
- **Consistent**: Same error handling pattern across all routes 