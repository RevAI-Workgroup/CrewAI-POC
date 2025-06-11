import { useCallback, useRef, useState, useEffect } from 'react';
import type { Node, Edge } from '@xyflow/react';
import { useGraphStore } from '@/stores';
import { useDebouncedCallback } from 'use-debounce';
import type { GraphNode } from '@/types/graph.types';
import { convertFormDataForStorage, convertFormDataFromStorage, validateNodeReferences } from '@/utils/nodeReferences';

interface UseGraphSyncOptions {
  graphId: string;
  debounceMs?: number;
  enableSync?: boolean;
  nodeDef?: any; // Node definitions for field type detection
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
  enableSync = true,
  nodeDef = null
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
    console.debug('🚀 performSync called:', { graphId, enableSync, nodeCount: nodes.length, edgeCount: edges.length });
    
    if (!graphId || !enableSync) {
      console.debug('⚠️ performSync skipped:', { graphId, enableSync });
      return;
    }
    
    const dataString = JSON.stringify({ nodes, edges });
    
    // Skip if data hasn't changed since last sync
    if (dataString === lastSyncedData.current) {
      console.debug('⚠️ No changes detected, skipping sync');
      setSyncStatus(prev => ({ ...prev, pendingChanges: false }));
      return;
    }
    
    console.debug('📡 Making API call to updateGraph...');
    
    setSyncStatus(prev => ({ 
      ...prev, 
      isSyncing: true, 
      error: null,
      pendingChanges: false
    }));
    
    try {

        // Convert nodes and edges to GraphNode and GraphEdge with enhanced storage format
        const graphNodes = nodes.map(node => {
            console.debug(`📝 Syncing node ${node.id} with data:`, node.data);
            
            const nodeType = node.type as GraphNode['type'];
            const formData = node.data?.formData || {};
            
            // Convert form data to storage format (with "node/ID" references)
            const convertedFormData = convertFormDataForStorage(
                formData, 
                nodeType,
                nodeDef
            );
            
            // Extract category from node definition
            const category = nodeDef?.node_types?.[nodeType]?.category || 'Unknown';
            
            return {
                id: node.id,
                type: nodeType,
                category: category, // Category at node level, not in data
                position: node.position,
                data: {
                    formData: convertedFormData, // Use converted form data with "node/ID" references
                    fieldVisibility: node.data?.fieldVisibility || {},
                    // Include other existing data
                    label: node.data?.label || nodeType,
                    // Include metadata for better tracking
                    lastModified: new Date().toISOString(),
                    // Preserve any other custom data (but filter out formData, fieldVisibility, category to avoid duplication)
                    ...Object.fromEntries(
                        Object.entries(node.data || {}).filter(([key]) => 
                            !['formData', 'fieldVisibility', 'label', 'category'].includes(key)
                        )
                    )
                }
            };
        });

        // Validate node references before syncing
        const validationErrors: string[] = [];
        graphNodes.forEach(node => {
            const validation = validateNodeReferences(
                node.data.formData,
                node.type,
                nodeDef,
                nodes
            );
            validationErrors.push(...validation.errors);
        });

        if (validationErrors.length > 0) {
            console.warn('Node reference validation warnings:', validationErrors);
            // Log warnings but don't block sync - references might be intentionally missing temporarily
        }

        const graphEdges = edges.map(edge => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            sourceHandle: edge.sourceHandle || null,
            targetHandle: edge.targetHandle || null,
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
        
        console.debug('📤 API payload:', updatePayload);
        
        await updateGraph(graphId, updatePayload);
        
        console.debug('✅ Graph synced successfully');
        
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
  }, [graphId, updateGraph, enableSync, nodeDef]);
  
  // Main sync function called by components
  const syncGraph = useCallback((nodes: Node[], edges: Edge[]) => {
    console.debug('🔄 syncGraph called:', { enableSync, graphId, nodeCount: nodes.length, edgeCount: edges.length });
    
    if (!enableSync || !graphId) {
      console.debug('⚠️ Sync skipped:', { 
        enableSync, 
        graphId,
        reason: !enableSync ? 'Sync disabled (no valid graph selected)' : 'Missing graph ID'
      });
      return;
    }
    
    const dataString = JSON.stringify({ nodes, edges });
    
    // Skip if this exact data is already pending sync
    if (pendingSync.current && JSON.stringify(pendingSync.current) === dataString) {
      console.debug('⚠️ Duplicate sync call with same data, skipping');
      return;
    }
    
    // Skip if data hasn't changed since last sync
    if (dataString === lastSyncedData.current) {
      console.debug('⚠️ No changes detected since last sync, skipping');
      setSyncStatus(prev => ({ ...prev, pendingChanges: false }));
      return;
    }
    
    // Update pending sync data
    pendingSync.current = { nodes, edges };
    
    setSyncStatus(prev => ({ ...prev, pendingChanges: true }));
    
    console.debug('⏱️ Triggering debounced sync (1s delay)');
    
    // Trigger debounced sync
    debouncedSyncTrigger();
  }, [graphId, enableSync, debouncedSyncTrigger, lastSyncedData]);
  
  // Force immediate sync (for undo/redo operations)
  const forceSyncGraph = useCallback(async (nodes: Node[], edges: Edge[]) => {
    if (!enableSync || !graphId) return;
    
    // Cancel any pending debounced sync
    pendingSync.current = null;
    
    await performSync(nodes, edges);
  }, [graphId, enableSync, performSync]);
  
  // Load initial graph data and populate nodes/edges from graph_data
  const loadGraphData = useCallback((graphData: any) => {
    console.debug('📥 Loading graph data:', graphData);
    
    if (!graphData) {
      console.debug('⚠️ No graph data provided');
      return { nodes: [], edges: [] };
    }
    
    // Handle both direct nodes/edges and graph_data wrapper
    let sourceNodes = [];
    let sourceEdges = [];
    
    if (graphData.graph_data) {
      // Backend format: { graph_data: { nodes: [...], edges: [...] } }
      console.debug('📦 Loading from graph_data wrapper');
      sourceNodes = graphData.graph_data.nodes || [];
      sourceEdges = graphData.graph_data.edges || [];
    } else {
      // Direct format: { nodes: [...], edges: [...] }
      console.debug('📦 Loading from direct nodes/edges');
      sourceNodes = graphData.nodes || [];
      sourceEdges = graphData.edges || [];
    }
    
    // Transform nodes to ReactFlow format with proper data restoration
    // First pass: Create nodes with basic data structure
    const basicNodes = sourceNodes.map((node: any) => {
      console.debug(`📝 Loading node ${node.id} with data:`, node.data);
      
      // Handle both old and new storage formats
      let formData = {};
      let fieldVisibility = {};
      let category = 'Unknown';
      
      if (node.data) {
        // New format: data contains formData, fieldVisibility
        formData = node.data.formData || {};
        fieldVisibility = node.data.fieldVisibility || {};
        // Category is at node level, not in data
        category = node.category || node.data.category || 'Unknown';
      } else if (node.formData) {
        // Legacy format: formData at root level
        formData = node.formData || {};
        fieldVisibility = node.fieldVisibility || {};
        category = node.category || 'Unknown';
      }
      
      return {
        id: node.id,
        type: node.type,
        position: node.position || { x: 0, y: 0 },
        data: {
          label: node.data?.label || node.type,
          type: node.type,
          category: category,
          // Store raw form data temporarily for conversion
          _rawFormData: formData,
          // Restore field visibility settings
          fieldVisibility: fieldVisibility,
          // Preserve any other custom data
          ...node.data
        },
        selected: false,
        dragging: false
      };
    });
    
    // Second pass: Convert stored form data references using all nodes
    const nodes = basicNodes.map((node: any) => {
      const displayFormData = convertFormDataFromStorage(node.data._rawFormData, basicNodes);
      
      return {
        ...node,
        data: {
          ...node.data,
          formData: displayFormData,
          // Remove temporary raw form data and redundant category
          _rawFormData: undefined,
          category: undefined
        }
      };
    });
    
    // Transform edges to ReactFlow format
    const edges = sourceEdges.map((edge: any) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourceHandle || null,
      targetHandle: edge.targetHandle || null,
      type: edge.type || 'default',
      data: edge.data || {},
      selected: false
    }));
    
    console.debug(`✅ Loaded ${nodes.length} nodes and ${edges.length} edges`);
    
    // Store as last synced data to prevent immediate re-sync
    lastSyncedData.current = JSON.stringify({ nodes, edges });
    
    return { nodes, edges };
  }, []);
  
  // Initialize sync status on graph change - loaded graphs should show as "Saved"
  useEffect(() => {
    setSyncStatus({
      isSyncing: false,
      lastSyncedAt: graphId ? new Date() : null, // Set current time for loaded graphs
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