import { useCallback, useRef, useState, useEffect } from 'react';
import type { Node, Edge } from '@xyflow/react';
import { useGraphStore } from '@/stores';
import { useDebouncedCallback } from 'use-debounce';
import type { GraphNode } from '@/types/graph.types';

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
  
  // Debounced sync trigger
  const debouncedSyncTrigger = useDebouncedCallback(
    useCallback(() => {
      if (pendingSync.current && enableSync) {
        performSync(pendingSync.current.nodes, pendingSync.current.edges);
      }
    }, [enableSync]),
    debounceMs
  );
  
  // Perform the actual sync to backend
  const performSync = useCallback(async (nodes: Node[], edges: Edge[]) => {
    console.log('🚀 performSync called:', { graphId, enableSync, nodeCount: nodes.length, edgeCount: edges.length });
    
    if (!graphId || !enableSync) {
      console.log('⚠️ performSync skipped:', { graphId, enableSync });
      return;
    }
    
    const dataString = JSON.stringify({ nodes, edges });
    
    // Skip if data hasn't changed since last sync
    if (dataString === lastSyncedData.current) {
      console.log('⚠️ No changes detected, skipping sync');
      setSyncStatus(prev => ({ ...prev, pendingChanges: false }));
      return;
    }
    
    console.log('📡 Making API call to updateGraph...');
    
    setSyncStatus(prev => ({ 
      ...prev, 
      isSyncing: true, 
      error: null,
      pendingChanges: false
    }));
    
    try {

        // Convert nodes and edges to GraphNode and GraphEdge with complete form data
        const graphNodes = nodes.map(node => {
            console.log(`📝 Syncing node ${node.id} with data:`, node.data);
            
            return {
                id: node.id,
                type: node.type as GraphNode['type'],
                position: node.position,
                data: {
                    ...node.data,
                    // Ensure formData is preserved and up-to-date
                    formData: node.data.formData || {},
                    // Include any other node-specific data
                    label: node.data.label || node.type,
                    // Preserve visibility settings
                    fieldVisibility: node.data.fieldVisibility || {},
                    // Include metadata for better tracking
                    lastModified: new Date().toISOString()
                }
            };
        });

        const graphEdges = edges.map(edge => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            type: edge.type || 'default',
            data: edge.data || {}
        }));

        const updatePayload = {
            graph_data: {
                nodes: graphNodes,
                edges: graphEdges,
                metadata: {
                    lastModified: new Date().toISOString(),
                    version: Date.now()
                }
            }
        };
        
        console.log('📤 API payload:', updatePayload);
        
        await updateGraph(graphId, updatePayload);
        
        console.log('✅ Graph synced successfully');
        
        lastSyncedData.current = dataString;
        setSyncStatus(prev => ({
            ...prev,
            isSyncing: false,
            lastSyncedAt: new Date(),
            error: null
        }));
      
    } catch (error) {
      console.error('❌ Failed to sync graph:', error);
      setSyncStatus(prev => ({
        ...prev,
        isSyncing: false,
        error: error instanceof Error ? error.message : 'Sync failed'
      }));
    }
  }, [graphId, updateGraph, enableSync]);
  
  // Main sync function called by components
  const syncGraph = useCallback((nodes: Node[], edges: Edge[]) => {
    console.log('🔄 syncGraph called:', { enableSync, graphId, nodeCount: nodes.length, edgeCount: edges.length });
    
    if (!enableSync || !graphId) {
      console.log('⚠️ Sync skipped:', { 
        enableSync, 
        graphId,
        reason: !enableSync ? 'Sync disabled (no valid graph selected)' : 'Missing graph ID'
      });
      return;
    }
    
    // Update pending sync data
    pendingSync.current = { nodes, edges };
    
    setSyncStatus(prev => ({ ...prev, pendingChanges: true }));
    
    console.log('⏱️ Triggering debounced sync (2s delay)');
    
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
  
  // Load initial graph data and populate nodes/edges from graph_data
  const loadGraphData = useCallback((graphData: any) => {
    console.log('📥 Loading graph data:', graphData);
    
    if (!graphData) {
      console.log('⚠️ No graph data provided');
      return { nodes: [], edges: [] };
    }
    
    // Handle both direct nodes/edges and graph_data wrapper
    let sourceNodes = [];
    let sourceEdges = [];
    
    if (graphData.graph_data) {
      // Backend format: { graph_data: { nodes: [...], edges: [...] } }
      console.log('📦 Loading from graph_data wrapper');
      sourceNodes = graphData.graph_data.nodes || [];
      sourceEdges = graphData.graph_data.edges || [];
    } else {
      // Direct format: { nodes: [...], edges: [...] }
      console.log('📦 Loading from direct nodes/edges');
      sourceNodes = graphData.nodes || [];
      sourceEdges = graphData.edges || [];
    }
    
    // Transform nodes to ReactFlow format with proper data restoration
    const nodes = sourceNodes.map((node: any) => {
      console.log(`📝 Loading node ${node.id} with data:`, node.data);
      
      return {
        id: node.id,
        type: node.type,
        position: node.position || { x: 0, y: 0 },
        data: {
          label: node.data?.label || node.type,
          type: node.type,
          // Restore form data with all field values
          formData: node.data?.formData || {},
          // Restore field visibility settings
          fieldVisibility: node.data?.fieldVisibility || {},
          // Preserve any other custom data
          ...node.data
        },
        selected: false,
        dragging: false
      };
    });
    
    // Transform edges to ReactFlow format
    const edges = sourceEdges.map((edge: any) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: edge.type || 'default',
      data: edge.data || {},
      selected: false
    }));
    
    console.log(`✅ Loaded ${nodes.length} nodes and ${edges.length} edges`);
    
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