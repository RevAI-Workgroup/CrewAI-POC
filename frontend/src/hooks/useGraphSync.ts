import { useCallback, useRef, useState, useEffect } from 'react';
import type { Node, Edge } from '@xyflow/react';
import { useGraphStore } from '@/stores';
import { useDebounce } from './useDebounce';

interface UseGraphSyncOptions {
  graphId: string;
  debounceMs?: number;
  enableSync?: boolean;
}

interface SyncStatus {
  isSyncing: boolean;
  lastSyncedAt: Date | null;
  error: string | null;
  pendingChanges: boolean;
}

export function useGraphSync({ 
  graphId, 
  debounceMs = 2000, 
  enableSync = true 
}: UseGraphSyncOptions) {
  const { updateGraph, isUpdating, error: storeError } = useGraphStore();
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    isSyncing: false,
    lastSyncedAt: null,
    error: null,
    pendingChanges: false
  });
  
  const pendingSync = useRef<{ nodes: Node[]; edges: Edge[] } | null>(null);
  const lastSyncedData = useRef<string>('');
  
  // Track the current data that needs to be synced
  const [currentData, setCurrentData] = useState<{ nodes: Node[]; edges: Edge[] } | null>(null);
  
  // Debounced sync trigger
  const debouncedSyncTrigger = useDebounce(
    useCallback(() => {
      if (pendingSync.current && enableSync) {
        performSync(pendingSync.current.nodes, pendingSync.current.edges);
      }
    }, [enableSync]),
    debounceMs
  );
  
  // Perform the actual sync to backend
  const performSync = useCallback(async (nodes: Node[], edges: Edge[]) => {
    if (!graphId || !enableSync) return;
    
    const dataString = JSON.stringify({ nodes, edges });
    
    // Skip if data hasn't changed since last sync
    if (dataString === lastSyncedData.current) {
      setSyncStatus(prev => ({ ...prev, pendingChanges: false }));
      return;
    }
    
    setSyncStatus(prev => ({ 
      ...prev, 
      isSyncing: true, 
      error: null,
      pendingChanges: false
    }));
    
    try {
      await updateGraph(graphId, {
        graph_data: {
          nodes,
          edges,
          metadata: {
            lastModified: new Date().toISOString(),
            version: Date.now()
          }
        }
      });
      
      lastSyncedData.current = dataString;
      setSyncStatus(prev => ({
        ...prev,
        isSyncing: false,
        lastSyncedAt: new Date(),
        error: null
      }));
      
    } catch (error) {
      console.error('Failed to sync graph:', error);
      setSyncStatus(prev => ({
        ...prev,
        isSyncing: false,
        error: error instanceof Error ? error.message : 'Sync failed'
      }));
    }
  }, [graphId, updateGraph, enableSync]);
  
  // Main sync function called by components
  const syncGraph = useCallback((nodes: Node[], edges: Edge[]) => {
    if (!enableSync || !graphId) return;
    
    // Update pending sync data
    pendingSync.current = { nodes, edges };
    setCurrentData({ nodes, edges });
    
    setSyncStatus(prev => ({ ...prev, pendingChanges: true }));
    
    // Trigger debounced sync
    debouncedSyncTrigger();
  }, [graphId, enableSync, debouncedSyncTrigger]);
  
  // Force immediate sync (for undo/redo operations)
  const forceSyncGraph = useCallback(async (nodes: Node[], edges: Edge[]) => {
    if (!enableSync || !graphId) return;
    
    // Cancel any pending debounced sync
    pendingSync.current = null;
    
    await performSync(nodes, edges);
  }, [graphId, enableSync, performSync]);
  
  // Load initial graph data
  const loadGraphData = useCallback((graphData: any) => {
    if (!graphData) return { nodes: [], edges: [] };
    
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    
    // Store as last synced data to prevent immediate re-sync
    lastSyncedData.current = JSON.stringify({ nodes, edges });
    
    return { nodes, edges };
  }, []);
  
  // Clear sync status on graph change
  useEffect(() => {
    setSyncStatus({
      isSyncing: false,
      lastSyncedAt: null,
      error: null,
      pendingChanges: false
    });
    pendingSync.current = null;
    lastSyncedData.current = '';
  }, [graphId]);
  
  // Update error from store
  useEffect(() => {
    if (storeError) {
      setSyncStatus(prev => ({
        ...prev,
        error: storeError,
        isSyncing: false
      }));
    }
  }, [storeError]);
  
  return {
    syncGraph,
    forceSyncGraph,
    loadGraphData,
    syncStatus: {
      ...syncStatus,
      isSyncing: syncStatus.isSyncing || isUpdating
    }
  };
} 