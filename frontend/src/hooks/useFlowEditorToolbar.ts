import { useMemo } from 'react';
import { useGraphHistory } from './useGraphHistory';
import { useAutoSync } from './useAutoSync';
import type { Node, Edge } from '@xyflow/react';

interface UseFlowEditorToolbarOptions {
  nodes: Node[];
  edges: Edge[];
  graphId: string;
  enableSync: boolean;
  nodeDef?: any;
  onStateRestore: (nodes: Node[], edges: Edge[]) => void;
}

/**
 * Custom hook that consolidates all toolbar-related state and functionality
 * Reduces prop drilling and simplifies FlowEditor component
 */
export function useFlowEditorToolbar({
  nodes,
  edges,
  graphId,
  enableSync,
  nodeDef,
  onStateRestore
}: UseFlowEditorToolbarOptions) {
  
  // History management with state restoration
  const {
    canUndo,
    canRedo,
    undoOperation,
    redoOperation,
    getUndoTooltip,
    getRedoTooltip,
    initializeHistory,
    addHistoryState
  } = useGraphHistory({
    onStateRestore,
    onHistoryChange: (operation, historyOperation) => {
      console.debug(`${operation}: ${historyOperation}`);
    }
  });

  // Auto-sync with smart debouncing
  const { syncStatus, forceSyncGraph, manualSync } = useAutoSync(nodes, edges, {
    graphId,
    enableSync,
    nodeDef
  });

  // Consolidated toolbar props
  const toolbarProps = useMemo(() => ({
    // Undo/Redo props
    canUndo,
    canRedo,
    onUndo: undoOperation,
    onRedo: redoOperation,
    undoTooltip: getUndoTooltip(),
    redoTooltip: getRedoTooltip(),
    
    // Sync status props
    isSyncing: syncStatus.isSyncing,
    lastSyncedAt: syncStatus.lastSyncedAt,
    syncError: syncStatus.error,
    pendingChanges: syncStatus.pendingChanges,
    
    // Manual save function
    onSave: () => manualSync(nodes, edges)
  }), [
    canUndo,
    canRedo,
    undoOperation,
    redoOperation,
    getUndoTooltip,
    getRedoTooltip,
    syncStatus.isSyncing,
    syncStatus.lastSyncedAt,
    syncStatus.error,
    syncStatus.pendingChanges,
    manualSync,
    nodes,
    edges
  ]);

  return {
    // Consolidated toolbar props for SyncToolbar component
    toolbarProps,
    
    // History functions for FlowEditor internal use
    initializeHistory,
    addHistoryState,
    
    // Sync functions for special cases
    forceSyncGraph
  };
} 