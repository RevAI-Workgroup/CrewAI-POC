# Graphs Component Architecture

**Date**: 2024-12-27  
**Task**: [2-19 Graph Store and Grid UI](mdc:../PBI-002-19.md)  
**Refactor**: Component Modularization

## Overview

The Graphs page has been refactored from a single monolithic component into a collection of smaller, focused components organized in `@/components/graphs/`.

## Component Structure

### `@/components/graphs/`

```
graphs/
├── index.ts                    # Export barrel
├── GraphsHeader.tsx           # Page header with title and create button
├── GraphCard.tsx              # Individual graph card with actions
├── GraphGrid.tsx              # Grid layout and state management
├── GraphLoadingSkeleton.tsx   # Loading state display
├── GraphEmptyState.tsx        # Empty state when no graphs exist
└── GraphErrorState.tsx        # Error state display
```

## Component Breakdown

### 1. **GraphsHeader**
- **Purpose**: Page title and main create action
- **Props**: `onCreateGraph`, `isCreating`
- **Responsibility**: Header layout and primary CTA

```typescript
interface GraphsHeaderProps {
  onCreateGraph: () => void;
  isCreating: boolean;
}
```

### 2. **GraphCard**
- **Purpose**: Display individual graph with metadata and actions
- **Props**: `graph`, `onEdit`, `onDelete`, `onDuplicate`, `isDeleting`
- **Features**: 
  - Graph metadata (nodes, connections, updated date)
  - Dropdown menu with actions (Edit, Duplicate, Delete)
  - Delete confirmation dialog
  - Loading states for delete action

```typescript
interface GraphCardProps {
  graph: Graph;
  onEdit: (graph: Graph) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
  isDeleting?: boolean;
}
```

### 3. **GraphGrid**
- **Purpose**: Layout management and state routing
- **Props**: `graphs`, `isLoading`, `isCreating`, `deletingId`, action handlers
- **Responsibility**: 
  - Determines which component to render (loading, empty, or grid)
  - Manages responsive grid layout
  - Passes props to child components

```typescript
interface GraphGridProps {
  graphs: Graph[];
  isLoading: boolean;
  isCreating: boolean;
  deletingId: string | null;
  onEdit: (graph: Graph) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
  onCreateGraph: () => void;
}
```

### 4. **GraphLoadingSkeleton**
- **Purpose**: Loading state with skeleton cards
- **Props**: None (pure UI component)
- **Features**: 8 animated skeleton cards in responsive grid

### 5. **GraphEmptyState**
- **Purpose**: Empty state when no graphs exist
- **Props**: `onCreateGraph`, `isCreating`
- **Features**: 
  - Encouraging messaging
  - Visual icon placeholder
  - Primary create action

```typescript
interface GraphEmptyStateProps {
  onCreateGraph: () => void;
  isCreating: boolean;
}
```

### 6. **GraphErrorState**
- **Purpose**: Error display with recovery options
- **Props**: `error`, `onCreateGraph`, `onRetry`, `isCreating`
- **Features**:
  - Error message display
  - Retry functionality
  - Maintains create capability during errors

```typescript
interface GraphErrorStateProps {
  error: string;
  onCreateGraph: () => void;
  onRetry: () => void;
  isCreating: boolean;
}
```

## Refactored GraphsPage

The main `GraphsPage` component is now simplified to:

1. **State Management**: Handles local state and store integration
2. **Event Handlers**: Defines action handlers for child components
3. **Composition**: Composes the appropriate components based on state

```typescript
// Before: 256 lines of mixed concerns
// After: 68 lines focused on orchestration

export function GraphsPage() {
  // State and handlers...
  
  if (error) {
    return <GraphErrorState {...errorProps} />;
  }

  return (
    <div className="space-y-6">
      <GraphsHeader {...headerProps} />
      <GraphGrid {...gridProps} />
    </div>
  );
}
```

## Benefits

### 1. **Maintainability**
- Each component has a single responsibility
- Easier to test individual components
- Clearer separation of concerns

### 2. **Reusability**
- Components can be reused in other contexts
- GraphCard could be used in dashboards or search results
- Loading and empty states are reusable patterns

### 3. **Developer Experience**
- Easier to locate and modify specific functionality
- Smaller, focused files are easier to understand
- Better code organization and discoverability

### 4. **Testing**
- Unit tests can focus on individual components
- Easier to mock dependencies and isolate functionality
- More granular testing capabilities

### 5. **Performance**
- Smaller bundle chunks for code splitting
- Better tree shaking opportunities
- Reduced re-render scope

## Usage Examples

### Import and Use Individual Components
```typescript
import { GraphCard, GraphLoadingSkeleton } from '@/components/graphs';

// Use in other contexts
<GraphCard 
  graph={selectedGraph} 
  onEdit={handleEdit}
  // ... other props
/>
```

### Compose Different Layouts
```typescript
// Alternative layout using the same components
<div className="flex flex-col lg:flex-row gap-6">
  <div className="lg:w-1/3">
    <GraphsHeader {...props} />
  </div>
  <div className="lg:w-2/3">
    <GraphGrid {...props} />
  </div>
</div>
```

## Future Enhancements

With this modular structure, future improvements become easier:

1. **Add graph filtering**: Extend GraphGrid with filter props
2. **Graph previews**: Enhance GraphCard with preview thumbnails  
3. **Bulk actions**: Add selection state to GraphCard
4. **Different view modes**: Create GraphList component alongside GraphGrid
5. **Advanced sorting**: Add sort controls to GraphsHeader

The component architecture provides a solid foundation for these and other enhancements while maintaining clean separation of concerns. 