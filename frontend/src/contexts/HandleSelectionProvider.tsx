import { createContext, useContext, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import { useReactFlow } from '@xyflow/react';
import { useGraphStore } from '@/stores';
import { v4 as uuidv4 } from 'uuid';

export interface HandleInfo {
  nodeId: string;
  nodeType: string;
  fieldName?: string; // undefined for output handles
  handleType: 'source' | 'target';
  handleId: string;
}

interface HandleSelectionContextType {
  selectedHandle: HandleInfo | null;
  draggedHandle: HandleInfo | null;
  selectHandle: (handle: HandleInfo) => void;
  clearSelection: () => void;
  startConnectionDrag: (handle: HandleInfo) => void;
  endConnectionDrag: () => void;
  isHandleCompatible: (handle: HandleInfo) => boolean;
  isHandleSelected: (handleId: string) => boolean;
  shouldDimHandle: (handle: HandleInfo) => boolean;
  tryCreateConnection: (targetHandle: HandleInfo) => boolean;
  getHandleCompatibleTypes: (handle: HandleInfo) => string[];
}

const HandleSelectionContext = createContext<HandleSelectionContextType | undefined>(undefined);

interface HandleSelectionProviderProps {
  children: ReactNode;
}

export const HandleSelectionProvider = ({ children }: HandleSelectionProviderProps) => {
  const [selectedHandle, setSelectedHandle] = useState<HandleInfo | null>(null);
  const [draggedHandle, setDraggedHandle] = useState<HandleInfo | null>(null);
  
  const { setEdges } = useReactFlow();
  const { nodeDef } = useGraphStore();

  // Get compatible types for a handle
  const getHandleCompatibleTypes = useCallback((handle: HandleInfo): string[] => {
    if (!nodeDef) return [];

    if (handle.handleType === 'source') {
      // For output handles, find what input field types can accept this node type
      const compatibleTypes: string[] = [];
      Object.entries(nodeDef.node_types).forEach(([nodeType, nodeTypeDef]) => {
        Object.entries(nodeTypeDef.fields).forEach(([fieldName, field]) => {
          if (field.filter) {
            if (field.filter.type) {
              const allowedTypes = Array.isArray(field.filter.type) 
                ? field.filter.type 
                : [field.filter.type];
              if (allowedTypes.includes(handle.nodeType)) {
                compatibleTypes.push(`${nodeType}.${fieldName}`);
              }
            }
            if (field.filter.category) {
              const allowedCategories = Array.isArray(field.filter.category)
                ? field.filter.category
                : [field.filter.category];
              const sourceNodeDef = nodeDef.node_types[handle.nodeType];
              if (allowedCategories.includes(sourceNodeDef?.category || '')) {
                compatibleTypes.push(`${nodeType}.${fieldName}`);
              }
            }
          }
        });
      });
      return compatibleTypes;
    } else {
      // For input handles, find what output node types can connect to this field
      if (!handle.fieldName) return [];
      
      const targetNodeDef = nodeDef.node_types[handle.nodeType];
      const targetField = targetNodeDef?.fields[handle.fieldName];
      
      if (!targetField?.filter) return [];

      const compatibleTypes: string[] = [];
      
      if (targetField.filter.type) {
        const allowedTypes = Array.isArray(targetField.filter.type) 
          ? targetField.filter.type 
          : [targetField.filter.type];
        compatibleTypes.push(...allowedTypes);
      }
      
      if (targetField.filter.category) {
        const allowedCategories = Array.isArray(targetField.filter.category)
          ? targetField.filter.category
          : [targetField.filter.category];
        
        Object.entries(nodeDef.node_types).forEach(([nodeType, nodeTypeDef]) => {
          if (allowedCategories.includes(nodeTypeDef.category)) {
            compatibleTypes.push(nodeType);
          }
        });
      }
      
      return compatibleTypes;
    }
  }, [nodeDef]);

  // Check if two handles are compatible for connection
  const areHandlesCompatible = useCallback((sourceHandle: HandleInfo, targetHandle: HandleInfo): boolean => {
    if (!nodeDef) return false;

    // Can't connect to same node
    if (sourceHandle.nodeId === targetHandle.nodeId) return false;

    // Must be opposite types
    if (sourceHandle.handleType === targetHandle.handleType) return false;

    // For output to input connections
    if (sourceHandle.handleType === 'source' && targetHandle.handleType === 'target') {
      const sourceNodeType = sourceHandle.nodeType;
      const targetFieldName = targetHandle.fieldName;
      
      if (!targetFieldName) return false;

      // Get the target field definition to check its filter
      const targetNodeDef = nodeDef.node_types[targetHandle.nodeType];
      const targetField = targetNodeDef?.fields[targetFieldName];
      
      if (!targetField?.filter) return false;

      // Check connection_constraints if they exist
      const fieldConstraintKey = `${targetHandle.nodeType}.${targetFieldName}`;
      const fieldConstraints = nodeDef.connection_constraints?.[fieldConstraintKey];
      
      if (fieldConstraints && fieldConstraints[targetFieldName]) {
        const constraints = fieldConstraints[targetFieldName];
        // Check if the source type matches the target_type constraint
        if (constraints.target_type && constraints.target_type !== sourceNodeType) {
          return false;
        }
      }

      // Check if source node type matches the target field's filter
      if (targetField.filter.type) {
        const allowedTypes = Array.isArray(targetField.filter.type) 
          ? targetField.filter.type 
          : [targetField.filter.type];
        return allowedTypes.includes(sourceNodeType);
      }

      if (targetField.filter.category) {
        const allowedCategories = Array.isArray(targetField.filter.category)
          ? targetField.filter.category
          : [targetField.filter.category];
        const sourceNodeDef = nodeDef.node_types[sourceNodeType];
        return allowedCategories.includes(sourceNodeDef?.category || '');
      }
    }

    return false;
  }, [nodeDef]);

  const selectHandle = useCallback((handle: HandleInfo) => {
    setSelectedHandle(handle);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedHandle(null);
    setDraggedHandle(null);
  }, []);

  const startConnectionDrag = useCallback((handle: HandleInfo) => {
    setDraggedHandle(handle);
    setSelectedHandle(null); // Clear selected when starting drag
  }, []);

  const endConnectionDrag = useCallback(() => {
    setDraggedHandle(null);
  }, []);

  const isHandleCompatible = useCallback((handle: HandleInfo): boolean => {
    const activeHandle = draggedHandle || selectedHandle;
    if (!activeHandle) return false;
    return areHandlesCompatible(activeHandle, handle) || areHandlesCompatible(handle, activeHandle);
  }, [selectedHandle, draggedHandle, areHandlesCompatible]);

  const isHandleSelected = useCallback((handleId: string): boolean => {
    return selectedHandle?.handleId === handleId || draggedHandle?.handleId === handleId;
  }, [selectedHandle, draggedHandle]);

  // Should dim handle (opposite of highlight - dim non-compatible handles when one is selected or dragged)
  const shouldDimHandle = useCallback((handle: HandleInfo): boolean => {
    const activeHandle = draggedHandle || selectedHandle;
    if (!activeHandle) return false;
    // Don't dim the active handle itself
    if (activeHandle.handleId === handle.handleId) return false;
    // Don't dim compatible handles
    return !isHandleCompatible(handle);
  }, [selectedHandle, draggedHandle, isHandleCompatible]);

  const tryCreateConnection = useCallback((targetHandle: HandleInfo): boolean => {
    const activeHandle = draggedHandle || selectedHandle;
    if (!activeHandle) return false;

    if (!isHandleCompatible(targetHandle)) return false;

    // Determine source and target
    const source = activeHandle.handleType === 'source' ? activeHandle : targetHandle;
    const target = activeHandle.handleType === 'target' ? activeHandle : targetHandle;

    // Create the edge
    const newEdge = {
      id: uuidv4(),
      source: source.nodeId,
      target: target.nodeId,
      sourceHandle: source.fieldName || 'output', // Use 'output' for output handles
      targetHandle: target.fieldName!,
      type: 'default',
    };

    setEdges((edges) => [...edges, newEdge]);
    clearSelection();
    return true;
  }, [selectedHandle, draggedHandle, isHandleCompatible, setEdges, clearSelection]);

  const value: HandleSelectionContextType = {
    selectedHandle,
    draggedHandle,
    selectHandle,
    clearSelection,
    startConnectionDrag,
    endConnectionDrag,
    isHandleCompatible,
    isHandleSelected,
    shouldDimHandle,
    tryCreateConnection,
    getHandleCompatibleTypes,
  };

  return (
    <HandleSelectionContext.Provider value={value}>
      {children}
    </HandleSelectionContext.Provider>
  );
};

export const useHandleSelection = (): HandleSelectionContextType => {
  const context = useContext(HandleSelectionContext);
  if (context === undefined) {
    throw new Error('useHandleSelection must be used within a HandleSelectionProvider');
  }
  return context;
}; 