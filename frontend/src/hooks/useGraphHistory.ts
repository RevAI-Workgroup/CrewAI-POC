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
  
  // ✅ FIX: Zustand persist middleware handles reactivity automatically
  // No need for manual subscriptions or force updates
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
    console.log('🔄 Undo operation called, canUndo:', canUndo);
    console.log('🔍 Current store state before undo:', {
      historyLength: history.length,
      currentIndex,
      canUndo,
      canRedo
    });
    
    if (!canUndo) return false;
    
    const previousState = undo();
    if (previousState && onStateRestore) {
      console.log('✅ Undo successful, restoring state:', {
        nodeCount: previousState.nodes.length,
        edgeCount: previousState.edges.length,
        operation: previousState.operation
      });
      onStateRestore(previousState.nodes, previousState.edges);
      onHistoryChange?.('undo', previousState.operation);
      return true;
    }
    console.log('❌ Undo failed - no previous state or onStateRestore');
    return false;
  }, [canUndo, undo, onStateRestore, onHistoryChange, history.length, currentIndex, canRedo]);
  
  // Redo operation
  const redoOperation = useCallback(() => {
    console.log('🔄 Redo operation called, canRedo:', canRedo);
    console.log('🔍 Current store state before redo:', {
      historyLength: history.length,
      currentIndex,
      canUndo,
      canRedo
    });
    
    if (!canRedo) return false;
    
    const nextState = redo();
    if (nextState && onStateRestore) {
      console.log('✅ Redo successful, restoring state:', {
        nodeCount: nextState.nodes.length,
        edgeCount: nextState.edges.length,
        operation: nextState.operation
      });
      onStateRestore(nextState.nodes, nextState.edges);
      onHistoryChange?.('redo', nextState.operation);
      return true;
    }
    console.log('❌ Redo failed - no next state or onStateRestore');
    return false;
  }, [canRedo, redo, onStateRestore, onHistoryChange, history.length, currentIndex, canUndo]);
  
  // Clear all history
  const clearHistory = useCallback(() => {
    clear();
  }, [clear]);
  
  // ✅ SIMPLIFIED: Initialize history with automatic persistence
  const initializeHistory = useCallback((nodes: Node[], edges: Edge[], graphId?: string) => {
    console.log('🚀 Initializing history for graph:', graphId);
    
    if (graphId) {
      // ✅ Load history from persist middleware (automatic)
      const store = useHistoryStore.getState();
      store.loadHistory(graphId);
      
      // ✅ Check immediately after loading
      const freshState = useHistoryStore.getState();
      console.log('🔍 History after loading:', { 
        historyLength: freshState.history.length, 
        currentIndex: freshState.currentIndex,
        canUndo: freshState.canUndo,
        canRedo: freshState.canRedo,
        graphId 
      });
      
      // If no stored history was loaded, add current state as initial IMMEDIATELY
      if (freshState.history.length === 0) {
        console.log('📝 No stored history found, adding initial state IMMEDIATELY');
        pushState(nodes, edges, 'initial', 'Initial state');
      } else {
        console.log(`✅ Loaded ${freshState.history.length} history steps from persist store`);
      }
      
      // ✅ End initialization phase after 200ms to allow React to settle
      setTimeout(() => {
        useHistoryStore.getState().endInitialization();
      }, 200);
    } else {
      // No graphId, just clear and add initial state
      clear();
      pushState(nodes, edges, 'initial', 'Initial state');
    }
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