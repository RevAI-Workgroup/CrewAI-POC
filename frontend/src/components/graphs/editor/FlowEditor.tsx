import { useRef, useMemo, useState, useCallback, useEffect } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlow,
  type Node,
  type Edge,
  type OnConnect,
  type Connection,
  type NodeTypes,
  type EdgeTypes,
  type OnNodesChange,
  type OnEdgesChange,
} from '@xyflow/react';
import '@xyflow/react/dist/base.css';

import { useHandleSelection } from '@/contexts/HandleSelectionProvider';
import CustomNode from './CustomNode';
import KeyboardShortcutsDialog from './KeyboardShortcutsDialog';

import { useTheme } from '@/contexts/ThemeProvider';
import { useGraphStore } from '@/stores';
import ShortcutsButton from './ShortcutsButton';
import ConnectionLine from './ConnectionLine';
import CustomEdge from './CustomEdge';
import ConnectionDropDialog from './ConnectionDropDialog';
import SyncToolbar from './SyncToolbar';

// Import custom hooks
import { useConnectionHandler } from './ConnectionHandler';
import { useDragDropHandler } from './DragDropHandler';
import { useNodeTypeSelector } from './NodeTypeSelector';
import { useGraphSync } from '@/hooks/useGraphSync';
  import { useAutoSync } from '@/hooks/useAutoSync';
  import { useGraphHistory } from '@/hooks/useGraphHistory';
  import type { HistoryOperation } from '@/types/history.types';

const proOptions = { hideAttribution: true };

const FlowEditor = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { getNodes, getEdges } = useReactFlow();
  const { clearSelection } = useHandleSelection();
  const historySuppressionRef = useRef(false);

  // Connection drop dialog state
  const [showConnectionDialog, setShowConnectionDialog] = useState(false);
  const [connectionDropPosition, setConnectionDropPosition] = useState<{ x: number; y: number } | null>(null);
  const [draggedConnectionInfo, setDraggedConnectionInfo] = useState<{
    sourceNodeId: string;
    sourceNodeType: string;
    sourceHandle: string;
    handleType: 'source' | 'target';
  } | null>(null);

  const { theme } = useTheme();
  const { nodeDef, selectedGraph } = useGraphStore();

  // Check if we have a valid graph to work with
  const hasValidGraph = !!(selectedGraph && selectedGraph.id && selectedGraph.id.trim());

  // Load graph data function - separate from sync
  const { loadGraphData } = useGraphSync({
    graphId: selectedGraph?.id || '',
    debounceMs: 1000,
    enableSync: false, // Only use for loading, auto-sync handles syncing
    nodeDef: nodeDef
  });

  // Auto-sync functionality
  const { syncStatus, forceSyncGraph, manualSync } = useAutoSync(nodes, edges, {
    graphId: selectedGraph?.id || '',
    enableSync: hasValidGraph,
    nodeDef
  });

  // History functionality with proper state restoration
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
    onStateRestore: (historyNodes, historyEdges) => {
      historySuppressionRef.current = true;
      setNodes(historyNodes);
      setEdges(historyEdges);
      // Force sync after undo/redo
      forceSyncGraph(historyNodes, historyEdges);
      setTimeout(() => {
        historySuppressionRef.current = false;
      }, 100);
    },
    onHistoryChange: (operation, historyOperation) => {
      console.debug(`${operation}: ${historyOperation}`);
    }
  });

  // Create toolbar props object
  const toolbarProps = {
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
  };

  // Keyboard shortcuts are handled by KeyboardShortcutsProvider context

  // Debug: Log node definitions when they change
  useEffect(() => {
    if (nodeDef) {
      console.debug('📊 Node definitions loaded:', {
        categories: nodeDef.categories?.map(c => c.id),
        nodeTypes: Object.keys(nodeDef.node_types),
        sampleAgentFields: nodeDef.node_types.agent ? Object.keys(nodeDef.node_types.agent.fields) : 'No agent type'
      });
      
      // Log fields with filters for reference detection
      Object.entries(nodeDef.node_types).forEach(([nodeType, def]) => {
        const referenceFields = Object.entries(def.fields || {}).filter(([_, fieldDef]) => 
          fieldDef.filter?.type || fieldDef.filter?.category
        );
        if (referenceFields.length > 0) {
          console.debug(`🔗 ${nodeType} reference fields:`, referenceFields.map(([name, def]) => ({
            name, 
            filter: def.filter
          })));
        }
      });
    }
  }, [nodeDef]);

  // Load initial graph data from graph_data field
  useEffect(() => {
    if (selectedGraph) {
      console.debug('🎯 Loading graph:', selectedGraph.id, selectedGraph);
      
      // ✅ FIX: Don't reload graph if we're currently syncing - this prevents overwriting user changes
      if (syncStatus.isSyncing) {
        console.debug('⚠️ Skipping graph reload - sync in progress');
        return;
      }
      
      // ✅ FIX: Don't reload if we recently synced (within last 2 seconds) - likely a sync update
      if (syncStatus.lastSyncedAt && (Date.now() - syncStatus.lastSyncedAt.getTime()) < 2000) {
        console.debug('⚠️ Skipping graph reload - recent sync detected');
        return;
      }
      
      // Use graph_data if available, fallback to direct nodes/edges for backward compatibility
      const graphDataToLoad = selectedGraph.graph_data || {
        nodes: selectedGraph.nodes || [],
        edges: selectedGraph.edges || []
      };
      
      const { nodes: initialNodes, edges: initialEdges } = loadGraphData(graphDataToLoad);
      
      setNodes(initialNodes);
      setEdges(initialEdges);
      initializeHistory(initialNodes, initialEdges, selectedGraph.id);
      
      // Initialize counters
      nodeCountRef.current = initialNodes.length;
    }
  }, [selectedGraph?.id, loadGraphData, setNodes, setEdges, initializeHistory, syncStatus.isSyncing, syncStatus.lastSyncedAt]); // ✅ Use selectedGraph.id instead of selectedGraph object

  // Track node count to detect additions/removals
  const nodeCountRef = useRef(0);

  // Track sync triggers to prevent duplicates
  const lastSyncTriggerRef = useRef<string>('');

  // Enhanced nodes change handler with coordinated history and sync
  const handleNodesChange: OnNodesChange = useCallback((changes) => {
    console.debug('📝 Nodes changed:', changes);
    const oldNodeCount = nodeCountRef.current;
    
    onNodesChange(changes);
    
    if (!historySuppressionRef.current) {
      // Use setTimeout to get updated node count and fresh state
      setTimeout(() => {
        // Get fresh node and edge state
        const currentNodes = getNodes();
        const currentEdges = getEdges();
        const newNodeCount = currentNodes.length;
        nodeCountRef.current = newNodeCount;
        
        // Determine operation type from changes and node count
        const hasNewNodes = newNodeCount > oldNodeCount;
        const hasRemovedNodes = newNodeCount < oldNodeCount;
        const hasPositionChanges = changes.some(change => change.type === 'position' && change.position);
        const hasDataChanges = changes.some(change => {
          const isDataChange = change.type === 'replace' && 
            change.item && 
            'data' in change.item;
          
          if (isDataChange) {
            console.debug('📝 Data change detected:', change);
            
            // Check if this is just automatic default initialization
            const item = change.item as Node;
            if (item.data?.autoInit) {
              console.debug('⚠️ Skipping sync for automatic default initialization');
              return false; // Skip automatic default initialization
            }
          }
          
          return isDataChange;
        });
        
        console.debug('🔄 Processing changes:', { 
          hasNewNodes, 
          hasRemovedNodes, 
          hasPositionChanges,
          hasDataChanges,
          oldCount: oldNodeCount,
          newCount: newNodeCount,
          changes 
        });
        
                  // Only proceed if there are actual changes we care about (ignore selection changes)
        if (hasNewNodes || hasRemovedNodes || hasPositionChanges || hasDataChanges) {
          let operation: HistoryOperation = 'update_node';
          
          if (hasNewNodes) {
            operation = 'create_node';
          } else if (hasRemovedNodes) {
            operation = 'delete_node';
          } else if (hasDataChanges) {
            operation = 'update_node';
            // Form data changes will be synced automatically by useAutoSync
            console.debug('💾 Form data changed, auto-sync will handle it');
          } else if (hasPositionChanges) {
            operation = 'move_node';
            // Move operations will be synced automatically by useAutoSync with debouncing
            console.debug('💾 Position changed, auto-sync will handle it');
          }
          
          console.debug('💾 Adding to history:', operation, '(auto-sync will handle synchronization)');
          
          // Simplified: Just add to history, auto-sync handles synchronization
          addHistoryState(currentNodes, currentEdges, operation);
        }
      }, 10); // Small delay to ensure state is updated
    }
  }, [onNodesChange, getNodes, getEdges, addHistoryState]);

  // Function to update form fields based on edge connections
  const updateFormFieldsFromEdges = useCallback((nodes: Node[], edges: Edge[]) => {
    console.debug('🔗 Updating form fields from edges...');
    console.debug('🔗 Input edges:', edges.map(e => ({id: e.id, source: e.source, target: e.target, sourceHandle: e.sourceHandle, targetHandle: e.targetHandle})));
    
    // Create a map of target node ID + field name to source node ID
    const fieldConnections: Record<string, string> = {};
    
    edges.forEach(edge => {
      if (edge.targetHandle && edge.target && edge.source) {
        const connectionKey = `${edge.target}:${edge.targetHandle}`;
        fieldConnections[connectionKey] = edge.source;
        console.debug(`🔗 Edge connection: ${edge.target}.${edge.targetHandle} -> ${edge.source}`);
      } else {
        console.debug(`⚠️ Edge missing handle info:`, edge);
      }
    });
    
    console.debug('🔗 Field connections map:', fieldConnections);
    
    // Update nodes with new form field values
    const updatedNodes = nodes.map(node => {
      const nodeDefinition = nodeDef?.node_types?.[node.type as any];
      if (!nodeDefinition || !nodeDefinition.fields) {
        console.debug(`⚠️ No node definition found for ${node.type}`);
        return node;
      }
      
      let hasChanges = false;
      const newFormData: Record<string, any> = { ...(node.data?.formData || {}) };
      
      console.debug(`🔍 Checking node ${node.id} (${node.type}) fields:`, Object.keys(nodeDefinition.fields));
      
      // Check each field in the node definition
      Object.entries(nodeDefinition.fields).forEach(([fieldName, fieldDef]: [string, any]) => {
        // Skip non-reference fields - should be OR logic (either type OR category filter)
        if (!fieldDef?.filter || (!fieldDef.filter.type && !fieldDef.filter.category)) {
          console.debug(`📝 Skipping non-reference field ${fieldName} for ${node.type}`);
          return;
        }
        
        console.debug(`🔗 Processing reference field ${fieldName} for ${node.type}:`, fieldDef.filter);
        
        const connectionKey = `${node.id}:${fieldName}`;
        const connectedSourceId = fieldConnections[connectionKey];
        
        if (connectedSourceId) {
          // Field is connected to a source node
          if (newFormData[fieldName] !== connectedSourceId) {
            console.debug(`🔗 Updating ${node.type} node ${node.id}: ${fieldName} = ${connectedSourceId} (was: ${newFormData[fieldName]})`);
            newFormData[fieldName] = connectedSourceId;
            hasChanges = true;
          } else {
            console.debug(`✅ Field ${fieldName} already has correct value: ${connectedSourceId}`);
          }
        } else {
          // Field is not connected - only clear if it currently has a value that looks like a node ID
          const currentValue = newFormData[fieldName];
          if (currentValue && typeof currentValue === 'string' && currentValue.length > 10) {
            console.debug(`🔗 Clearing ${node.type} node ${node.id}: ${fieldName} (was: ${currentValue}, no connection found)`);
            newFormData[fieldName] = '';
            hasChanges = true;
          }
        }
      });
      
      if (hasChanges) {
        console.debug(`✅ Node ${node.id} form data updated:`, newFormData);
        return {
          ...node,
          data: {
            ...node.data,
            formData: newFormData
          }
        };
      }
      
      return node;
    });
    
    console.debug('🔗 Form field update complete');
    return updatedNodes;
  }, [nodeDef]);

  // Enhanced edges change handler with coordinated history and sync
  const handleEdgesChange: OnEdgesChange = useCallback((changes) => {
    console.debug('🔗 Edges changed:', changes);
    console.debug('🔗 Change types detected:', changes.map(c => c.type));
    
    onEdgesChange(changes);
    
    if (!historySuppressionRef.current) {
      // Use setTimeout to get updated edge state
      setTimeout(() => {
        // Get fresh node and edge state
        const currentNodes = getNodes();
        const currentEdges = getEdges();
        
        console.debug('🔗 Current edges after change:', currentEdges.map(e => ({id: e.id, source: e.source, target: e.target, sourceHandle: e.sourceHandle, targetHandle: e.targetHandle})));
        
        // Determine operation type from changes
        const hasNewEdges = changes.some(change => change.type === 'add');
        const hasRemovedEdges = changes.some(change => change.type === 'remove');
        const hasUpdatedEdges = changes.some(change => change.type === 'replace');
        
        console.debug('🔄 Processing edge changes:', { 
          hasNewEdges, 
          hasRemovedEdges, 
          hasUpdatedEdges,
          totalEdges: currentEdges.length,
          changes 
        });
        
        // Proceed if there are actual changes we care about
        if (hasNewEdges || hasRemovedEdges || hasUpdatedEdges) {
          let operation: HistoryOperation = 'update_node';
          
          if (hasNewEdges) {
            operation = 'create_edge';
          } else if (hasRemovedEdges) {
            operation = 'delete_edge';
          } else if (hasUpdatedEdges) {
            operation = 'update_node'; // Edge data updated
          }
          
          console.debug('💾 Adding edge change to history and syncing:', operation);
          
          // Track that normal sync is happening
          lastSyncTriggerRef.current = Date.now().toString();
          
          // Update form fields based on new edge connections
          const updatedNodes = updateFormFieldsFromEdges(currentNodes, currentEdges);
          
          // Check if nodes were actually updated
          const nodesChanged = updatedNodes.some((node, index) => 
            JSON.stringify(node.data?.formData) !== JSON.stringify(currentNodes[index]?.data?.formData)
          );
          
          console.debug('🔗 Nodes changed by edge mapping:', nodesChanged);
          
          // If we updated nodes, apply the changes immediately
          if (nodesChanged) {
            console.debug('🔗 Applying form field updates from edge mapping');
            
            // Suppress history tracking for these automatic node updates
            historySuppressionRef.current = true;
            setNodes(updatedNodes);
            
            // Re-enable history tracking after a brief delay
            setTimeout(() => {
              historySuppressionRef.current = false;
            }, 50);
            
            // Simplified: Just add to history, auto-sync will handle synchronization
            addHistoryState(updatedNodes, currentEdges, operation);
          } else {
            // Simplified: Just add to history, auto-sync will handle synchronization
            addHistoryState(currentNodes, currentEdges, operation);
          }
        } else {
          console.debug('⚠️ No significant edge changes detected');
        }
      }, 10); // Small delay to ensure state is updated
    } else {
      console.debug('⚠️ Edge changes suppressed due to history operation');
    }
  }, [onEdgesChange, getNodes, getEdges, addHistoryState, updateFormFieldsFromEdges, setNodes]);

  // Use custom hooks for separated concerns
  const { onConnectStart, onConnectEnd, isValidConnection, getCompatibleNodeTypes } = useConnectionHandler({
    setDraggedConnectionInfo,
    setConnectionDropPosition,
    setShowConnectionDialog,
    draggedConnectionInfo,
    setEdges
  });

  const { onDragOver, onDrop } = useDragDropHandler({ setNodes });

  const { handleNodeTypeSelection, handleDialogClose } = useNodeTypeSelector({
    setNodes,
    setEdges,
    setShowConnectionDialog,
    setConnectionDropPosition,
    setDraggedConnectionInfo
  });

  // Create node types mapping - all node types use the CustomNode component
  const nodeTypes: NodeTypes = useMemo(() => {
    if (!nodeDef) return {};
    
    const types: NodeTypes = {};
    Object.keys(nodeDef.node_types).forEach(nodeType => {
      types[nodeType] = CustomNode;
    });
    
    return types;
  }, [nodeDef]);

  // Create edge types mapping
  const edgeTypes: EdgeTypes = useMemo(() => ({
    default: CustomEdge,
  }), []);

  const onConnect: OnConnect = useCallback(
    (params: Connection) => {
      console.debug('🔗 onConnect called with params:', params);
      console.debug('🔗 Handle info - source:', params.sourceHandle, 'target:', params.targetHandle);
      
      // Double-check validation before adding the edge
      if (!isValidConnection(params)) {
        console.debug('❌ Connection validation failed:', params);
        return;
      }
      
      console.debug('✅ Connection validated, adding edge...');
      
      // Clear connection info when a successful connection is made
      setDraggedConnectionInfo(null);
      
      setEdges((eds: Edge[]) => {
        // Explicitly create edge with handle information
        const newEdge = {
          id: `xy-edge__${params.source}${params.sourceHandle || 'output'}-${params.target}${params.targetHandle || 'input'}`,
          source: params.source!,
          target: params.target!,
          sourceHandle: params.sourceHandle || null,
          targetHandle: params.targetHandle || null,
          type: 'default',
          data: {}
        };
        
        console.debug('🔗 Creating edge with handles:', newEdge);
        const newEdges = [...eds, newEdge];
        console.debug('🔗 Edges updated from', eds.length, 'to', newEdges.length);
        
        return newEdges;
      });
    }, 
    [setEdges, isValidConnection, getNodes, getEdges, setNodes]
  );

  // Handle pane click to clear handle selection
  const onPaneClick = useCallback(() => {
    clearSelection();
  }, [clearSelection]);

  // Wrapper function for handleNodeTypeSelection to match expected signature
  const onSelectNodeType = useCallback((selectedNodeType: string) => {
    handleNodeTypeSelection(selectedNodeType, connectionDropPosition, draggedConnectionInfo);
  }, [handleNodeTypeSelection, connectionDropPosition, draggedConnectionInfo]);

  // Show message if no graph is selected (after all hooks are called)
  if (!hasValidGraph) {
    return (
      <div className="flex w-full h-full items-center justify-center">
        <div className="text-center p-8 max-w-md">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-semibold mb-2">No Graph Selected</h2>
          <p className="text-muted-foreground mb-4">
            Please select a graph from the sidebar to start editing, or create a new graph.
          </p>
          <div className="text-sm text-muted-foreground">
            The graph editor requires an active graph to enable saving and synchronization.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full h-full relative" id="flow-editor">
      {/* Editor Toolbar */}
      <SyncToolbar
        {...toolbarProps}
        className="absolute top-4 right-4 z-10"
      />

      {/* Keyboard Shortcuts Button */}
      <ShortcutsButton />

      {/* Keyboard Shortcuts Dialog */}
      <KeyboardShortcutsDialog />

      {/* Connection Drop Dialog */}
      <ConnectionDropDialog
        isOpen={showConnectionDialog}
        onClose={handleDialogClose}
        compatibleTypes={getCompatibleNodeTypes()}
        onSelectNodeType={onSelectNodeType}
        sourceNodeType={draggedConnectionInfo?.sourceNodeType}
        sourceHandle={draggedConnectionInfo?.sourceHandle}
      />

      {/* Main flow area */}
      <div className="flex-1 h-full" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onConnectStart={onConnectStart}
          onConnectEnd={onConnectEnd}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          isValidConnection={isValidConnection}
          connectionLineComponent={ConnectionLine}
          fitView
          proOptions={proOptions}
          colorMode={theme} // or 'dark' based on your theme context
          multiSelectionKeyCode="Shift"
          panOnDrag={[0]} // Allow panning with left and middle mouse buttons
          selectionOnDrag={false}
          selectNodesOnDrag={false}
          nodesDraggable={true}
          nodeDragThreshold={0}
          onlyRenderVisibleElements={false}
          nodesConnectable={true}
          elementsSelectable={true}
          
        >
          <Controls className="flex bg-background rounded-md p-1" orientation='horizontal' />
          <Background
            gap={20}
            size={1}
          />
          <MiniMap
            className=""
            maskColor="rgba(0, 0, 0, 0.6)"
          />
        </ReactFlow>
      </div>
    </div>
  );
};

export default FlowEditor; 