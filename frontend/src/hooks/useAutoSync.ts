import { useEffect, useRef, useCallback } from 'react';
import { useGraphSync } from './useGraphSync';
import type { Node, Edge } from '@xyflow/react';
import type { GraphState } from './useGraphState';

interface UseAutoSyncOptions {
  graphId: string;
  enableSync?: boolean;
  nodeDef?: any;
  debounceMs?: number;
  moveDebounceMs?: number; // Specific debounce for node movements
  immediateSync?: string[]; // Operations that should sync immediately
}

/**
 * React-Native Auto Sync Hook (Enhanced with Smart Debouncing)
 * 
 * This hook automatically syncs graph state changes using React's built-in reactivity.
 * Enhanced version supports both direct nodes/edges and GraphState with changeCount tracking.
 * 
 * Smart Debouncing Features:
 * - Different debounce times for different operations (movement vs creation/deletion)
 * - Detects operation types and applies appropriate debouncing
 * - Prevents sync loops during continuous node movements
 * - Immediate sync for critical operations (creation, deletion, connections)
 * 
 * Benefits:
 * - Eliminates race conditions from manual sync calls
 * - Prevents sync loops during node dragging
 * - Uses React's dependency tracking to prevent missed sync events
 * - More efficient change detection with changeCount
 * - Cleaner separation of concerns (state management vs sync logic)
 * - Smart debouncing based on operation type
 */

// Overloaded function signatures for Phase 1 (nodes/edges) and Phase 2 (GraphState)
export function useAutoSync(
  nodes: Node[], 
  edges: Edge[], 
  options: UseAutoSyncOptions
): {
  syncStatus: any;
  forceSyncGraph: (nodes: Node[], edges: Edge[]) => Promise<void>;
  manualSync: (nodes: Node[], edges: Edge[]) => void;
};

export function useAutoSync(
  graphState: GraphState,
  options: UseAutoSyncOptions
): {
  syncStatus: any;
  forceSyncGraph: (nodes: Node[], edges: Edge[]) => Promise<void>;
  manualSync: (nodes: Node[], edges: Edge[]) => void;
};

export function useAutoSync(
  nodesOrState: Node[] | GraphState,
  edgesOrOptions: Edge[] | UseAutoSyncOptions,
  optionsOrUndefined?: UseAutoSyncOptions
) {
  // Determine which overload is being used
  const isGraphState = Array.isArray(nodesOrState) === false;
  
  let nodes: Node[];
  let edges: Edge[];
  let options: UseAutoSyncOptions;
  let changeCount: number | undefined;

  if (isGraphState) {
    // Phase 2: GraphState usage
    const graphState = nodesOrState as GraphState;
    nodes = graphState.nodes;
    edges = graphState.edges;
    options = edgesOrOptions as UseAutoSyncOptions;
    changeCount = graphState.changeCount;
  } else {
    // Phase 1: Direct nodes/edges usage
    nodes = nodesOrState as Node[];
    edges = edgesOrOptions as Edge[];
    options = optionsOrUndefined as UseAutoSyncOptions;
    changeCount = undefined;
  }

  const { 
    graphId, 
    enableSync = true, 
    nodeDef, 
    debounceMs = 1000,
    moveDebounceMs = 2000, // Longer debounce for movements to prevent sync loops
    immediateSync = ['create', 'delete', 'connect'] // Operations that sync immediately
  } = options;

  const { syncGraph, forceSyncGraph, syncStatus } = useGraphSync({ 
    graphId, 
    enableSync,
    nodeDef,
    debounceMs: 0 // Disable internal debouncing - we handle it at a higher level
  });
  
  const lastStateRef = useRef<string>('');
  const lastChangeCountRef = useRef(0);
  const isInitializedRef = useRef(false);
  const lastPositionsRef = useRef<Record<string, { x: number; y: number }>>({});
  const movementTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingMoveNodesRef = useRef<Node[]>([]);
  const pendingMoveEdgesRef = useRef<Edge[]>([]);
  
  // Debounce timers for different operation types
  const standardTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Smart sync function that implements debouncing BEFORE calling syncGraph
  const smartSync = useCallback((currentNodes: Node[], currentEdges: Edge[], operationType?: string) => {
    // Clear any pending timers
    if (movementTimerRef.current) {
      clearTimeout(movementTimerRef.current);
      movementTimerRef.current = null;
    }
    if (standardTimerRef.current) {
      clearTimeout(standardTimerRef.current);
      standardTimerRef.current = null;
    }
    
    // Detect operation type if not provided
    if (!operationType) {
      operationType = detectOperationType(currentNodes, currentEdges, lastPositionsRef.current);
    }
    
    console.debug('🔄 Smart sync - detected operation:', operationType);
    
    // Apply operation-specific debouncing BEFORE triggering sync
    if (operationType === 'move') {
      // Store pending movement data
      pendingMoveNodesRef.current = currentNodes;
      pendingMoveEdgesRef.current = currentEdges;
      
      // Set longer debounce timer for movements - NO sync status change until timer completes
      movementTimerRef.current = setTimeout(() => {
        console.debug('🔄 Movement debounce completed, syncing...');
        syncGraph(pendingMoveNodesRef.current, pendingMoveEdgesRef.current);
        movementTimerRef.current = null;
      }, moveDebounceMs);
      
      console.debug(`⏱️ Movement debounced for ${moveDebounceMs}ms - sync status unchanged`);
      
    } else if (immediateSync.includes(operationType)) {
      // Immediate sync for critical operations - sync status changes immediately
      console.debug('🚀 Immediate sync for critical operation:', operationType);
      syncGraph(currentNodes, currentEdges);
      
    } else {
      // Standard debounced sync for other operations - NO sync status change until timer completes
      console.debug(`⏱️ Standard operation debounced for ${debounceMs}ms - sync status unchanged`);
      
      standardTimerRef.current = setTimeout(() => {
        console.debug('🔄 Standard debounce completed, syncing...');
        syncGraph(currentNodes, currentEdges);
        standardTimerRef.current = null;
      }, debounceMs);
    }
    
    // Update position tracking
    lastPositionsRef.current = currentNodes.reduce((acc, node) => {
      acc[node.id] = { x: node.position.x, y: node.position.y };
      return acc;
    }, {} as Record<string, { x: number; y: number }>);
    
  }, [syncGraph, moveDebounceMs, immediateSync, debounceMs]);
  
  // Helper function to detect operation type based on state changes
  const detectOperationType = useCallback((
    currentNodes: Node[], 
    currentEdges: Edge[], 
    lastPositions: Record<string, { x: number; y: number }>
  ): string => {
    // Get previous state for comparison
    const prevState = lastStateRef.current ? JSON.parse(lastStateRef.current) : { nodes: [], edges: [] };
    const prevNodes = prevState.nodes || [];
    const prevEdges = prevState.edges || [];
    
    // Check for node count changes
    if (currentNodes.length > prevNodes.length) {
      return 'create';
    }
    if (currentNodes.length < prevNodes.length) {
      return 'delete';
    }
    
    // Check for edge count changes
    if (currentEdges.length > prevEdges.length) {
      return 'connect';
    }
    if (currentEdges.length < prevEdges.length) {
      return 'disconnect';
    }
    
    // Check for position changes
    const hasPositionChanges = currentNodes.some(node => {
      const lastPos = lastPositions[node.id];
      if (!lastPos) return false;
      return Math.abs(node.position.x - lastPos.x) > 1 || Math.abs(node.position.y - lastPos.y) > 1;
    });
    
    if (hasPositionChanges) {
      return 'move';
    }
    
    // Check for data changes (form updates)
    const hasDataChanges = currentNodes.some(node => {
      const prevNode = prevNodes.find((n: any) => n.id === node.id);
      if (!prevNode) return false;
      return JSON.stringify(node.data) !== JSON.stringify(prevNode.data);
    });
    
    if (hasDataChanges) {
      return 'update';
    }
    
    return 'unknown';
  }, []);
  
  // Auto-sync whenever nodes/edges change (Phase 1) or changeCount changes (Phase 2)
  useEffect(() => {
    // Skip sync if sync is disabled or no graph ID
    if (!enableSync || !graphId) {
      console.debug('🔄 Auto-sync skipped:', { enableSync, hasGraphId: !!graphId });
      return;
    }
    
    // Skip sync if nodes array is empty (likely initial state)
    if (nodes.length === 0 && edges.length === 0) {
      console.debug('🔄 Auto-sync skipped: empty graph state');
      return;
    }
    
    let hasStateChanged = false;
    
    if (changeCount !== undefined) {
      // Phase 2: Use changeCount for efficient change detection
      if (changeCount > lastChangeCountRef.current) {
        hasStateChanged = true;
        lastChangeCountRef.current = changeCount;
        console.debug('🔄 Auto-sync: Change detected via changeCount:', {
          from: lastChangeCountRef.current,
          to: changeCount
        });
      }
    } else {
      // Phase 1: Use JSON comparison fallback
      const currentState = JSON.stringify({ 
        nodes: nodes.map(n => ({ id: n.id, position: n.position, data: n.data })),
        edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target, sourceHandle: e.sourceHandle, targetHandle: e.targetHandle }))
      });
      
      if (currentState !== lastStateRef.current) {
        hasStateChanged = true;
        lastStateRef.current = currentState;
        console.debug('🔄 Auto-sync: Change detected via JSON comparison');
      }
    }
    
    if (hasStateChanged) {
      // Skip the very first auto-sync on component initialization
      if (!isInitializedRef.current) {
        console.debug('🔄 Auto-sync: initializing with current state');
        isInitializedRef.current = true;
        // Initialize position tracking
        lastPositionsRef.current = nodes.reduce((acc, node) => {
          acc[node.id] = { x: node.position.x, y: node.position.y };
          return acc;
        }, {} as Record<string, { x: number; y: number }>);
        return;
      }
      
      console.debug('🔄 Auto-sync triggered by state change:', {
        nodeCount: nodes.length,
        edgeCount: edges.length,
        graphId: graphId,
        method: changeCount !== undefined ? 'changeCount' : 'JSON comparison'
      });
      
      // Use smart sync with operation detection and debouncing
      smartSync(nodes, edges);
    }
  }, [
    nodes, edges, smartSync, enableSync, graphId,
    ...(changeCount !== undefined ? [changeCount] : [])
  ]); // React handles dependency tracking
  
  // Reset initialization flag when graphId changes
  useEffect(() => {
    isInitializedRef.current = false;
    lastStateRef.current = '';
    lastChangeCountRef.current = 0;
    lastPositionsRef.current = {};
    
    // Clear any pending timers
    if (movementTimerRef.current) {
      clearTimeout(movementTimerRef.current);
      movementTimerRef.current = null;
    }
    if (standardTimerRef.current) {
      clearTimeout(standardTimerRef.current);
      standardTimerRef.current = null;
    }
  }, [graphId]);
  
  // Monitor sync status and save history when sync completes successfully
  const lastSyncStatusRef = useRef<{ isSyncing: boolean; lastSyncedAt: Date | null }>({ 
    isSyncing: false, 
    lastSyncedAt: null 
  });
  
  useEffect(() => {
    const currentSyncStatus = syncStatus;
    const lastStatus = lastSyncStatusRef.current;
    
    // Check if sync just completed successfully (was syncing, now not syncing, and has lastSyncedAt)
    if (lastStatus.isSyncing && 
        !currentSyncStatus.isSyncing && 
        currentSyncStatus.lastSyncedAt && 
        !currentSyncStatus.error) {
      
      // ✅ No manual saveHistoryToStorage needed - persist middleware handles it automatically
      console.debug('💾 Sync completed successfully - history auto-saved by persist middleware');
    }
    
    // Update last status
    lastSyncStatusRef.current = {
      isSyncing: currentSyncStatus.isSyncing,
      lastSyncedAt: currentSyncStatus.lastSyncedAt
    };
  }, [syncStatus.isSyncing, syncStatus.lastSyncedAt, syncStatus.error]);
  
  // Cleanup effect to clear timers on unmount
  useEffect(() => {
    return () => {
      if (movementTimerRef.current) {
        clearTimeout(movementTimerRef.current);
        movementTimerRef.current = null;
      }
      if (standardTimerRef.current) {
        clearTimeout(standardTimerRef.current);
        standardTimerRef.current = null;
      }
    };
  }, []);
  
  return {
    // Expose sync status for UI feedback
    syncStatus,
    // Force sync for special cases (undo/redo)
    forceSyncGraph,
    // Manual sync fallback (should rarely be needed)
    manualSync: syncGraph
  };
} 