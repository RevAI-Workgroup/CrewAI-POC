import { useCallback } from 'react';
import type { Node, Edge } from '@xyflow/react';
import useHistoryStore from '@/stores/historyStore';
import type { HistoryOperation } from '@/types/history.types';

interface UseGraphHistoryOptions {
  onStateRestore?: (nodes: Node[], edges: Edge[]) => void;
  onHistoryChange?: (operation: 'undo' | 'redo', historyOperation: HistoryOperation) => void;
}

export function useGraphHistory({ 
  onStateRestore, 
  onHistoryChange 
}: UseGraphHistoryOptions = {}) {
  const { 
    history,
    currentIndex,
    canUndo, 
    canRedo, 
    pushState, 
    undo, 
    redo, 
    clear,
    getCurrentState,
    getPreviousOperation
  } = useHistoryStore();
  
  // Add new state to history
  const addHistoryState = useCallback((
    nodes: Node[], 
    edges: Edge[], 
    operation: HistoryOperation, 
    description?: string
  ) => {
    // Don't add duplicate states for move operations (too frequent)
    if (operation === 'move_node') {
      const currentState = getCurrentState();
      if (currentState && currentState.operation === 'move_node') {
        // Update the current move operation instead of adding new one
        const updatedHistory = [...history];
        if (updatedHistory[currentIndex]) {
          updatedHistory[currentIndex] = {
            nodes: JSON.parse(JSON.stringify(nodes)),
            edges: JSON.parse(JSON.stringify(edges)),
            timestamp: Date.now(),
            operation,
            description
          };
          // Update store directly
          useHistoryStore.setState({
            history: updatedHistory
          });
          return;
        }
      }
    }
    
    pushState(nodes, edges, operation, description);
  }, [pushState, getCurrentState, history, currentIndex]);
  
  // Undo operation
  const undoOperation = useCallback(() => {
    if (!canUndo) return false;
    
    const previousState = undo();
    if (previousState && onStateRestore) {
      onStateRestore(previousState.nodes, previousState.edges);
      onHistoryChange?.('undo', previousState.operation);
      return true;
    }
    return false;
  }, [canUndo, undo, onStateRestore, onHistoryChange]);
  
  // Redo operation
  const redoOperation = useCallback(() => {
    if (!canRedo) return false;
    
    const nextState = redo();
    if (nextState && onStateRestore) {
      onStateRestore(nextState.nodes, nextState.edges);
      onHistoryChange?.('redo', nextState.operation);
      return true;
    }
    return false;
  }, [canRedo, redo, onStateRestore, onHistoryChange]);
  
  // Clear all history
  const clearHistory = useCallback(() => {
    clear();
  }, [clear]);
  
  // Initialize history with current state
  const initializeHistory = useCallback((nodes: Node[], edges: Edge[]) => {
    clear();
    pushState(nodes, edges, 'initial', 'Initial state');
  }, [clear, pushState]);
  
  // Batch multiple operations
  const batchOperations = useCallback((
    operations: Array<{
      nodes: Node[];
      edges: Edge[];
      operation: HistoryOperation;
      description?: string;
    }>
  ) => {
    if (operations.length === 0) return;
    
    if (operations.length === 1) {
      const op = operations[0];
      addHistoryState(op.nodes, op.edges, op.operation, op.description);
      return;
    }
    
    // For multiple operations, save the final state as a batch
    const finalOp = operations[operations.length - 1];
    addHistoryState(
      finalOp.nodes, 
      finalOp.edges, 
      'batch', 
      `Batch: ${operations.map(op => op.operation).join(', ')}`
    );
  }, [addHistoryState]);
  
  // Get human-readable operation description
  const getOperationDescription = useCallback((operation: HistoryOperation): string => {
    switch (operation) {
      case 'create_node': return 'Create node';
      case 'delete_node': return 'Delete node';
      case 'move_node': return 'Move node';
      case 'update_node': return 'Update node';
      case 'create_edge': return 'Create connection';
      case 'delete_edge': return 'Delete connection';
      case 'batch': return 'Multiple changes';
      case 'initial': return 'Initial state';
      default: return 'Unknown operation';
    }
  }, []);
  
  // Get undo/redo button tooltips
  const getUndoTooltip = useCallback((): string => {
    if (!canUndo) return 'Nothing to undo';
    const previousOp = getPreviousOperation();
    return `Undo ${previousOp ? getOperationDescription(previousOp) : 'last action'}`;
  }, [canUndo, getPreviousOperation, getOperationDescription]);
  
  const getRedoTooltip = useCallback((): string => {
    if (!canRedo) return 'Nothing to redo';
    if (currentIndex + 1 < history.length) {
      const nextOp = history[currentIndex + 1].operation;
      return `Redo ${getOperationDescription(nextOp)}`;
    }
    return 'Redo next action';
  }, [canRedo, currentIndex, history, getOperationDescription]);
  
  // Combined history and sync operation
  const addHistoryStateWithSync = useCallback((
    nodes: Node[], 
    edges: Edge[], 
    operation: HistoryOperation, 
    description?: string,
    syncFn?: (nodes: Node[], edges: Edge[]) => void
  ) => {
    console.log('📚 addHistoryStateWithSync called:', { 
      operation, 
      nodeCount: nodes.length, 
      edgeCount: edges.length, 
      hasSyncFn: !!syncFn 
    });
    
    // Add to history first
    addHistoryState(nodes, edges, operation, description);
    
    // Then sync if provided
    if (syncFn) {
      console.log('🔄 Calling sync function from history');
      syncFn(nodes, edges);
    } else {
      console.log('⚠️ No sync function provided');
    }
  }, [addHistoryState]);

  return {
    // State
    canUndo,
    canRedo,
    historySize: history.length,
    currentIndex,
    
    // Actions
    addHistoryState,
    addHistoryStateWithSync,
    undoOperation,
    redoOperation,
    clearHistory,
    initializeHistory,
    batchOperations,
    
    // Utilities
    getOperationDescription,
    getUndoTooltip,
    getRedoTooltip,
    getCurrentState
  };
} 