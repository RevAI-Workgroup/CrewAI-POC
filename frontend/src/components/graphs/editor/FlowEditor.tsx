import React, { useRef, useMemo, useState, useCallback, useEffect } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  addEdge,
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
import EditorToolbar from './EditorToolbar';

// Import custom hooks
import { useConnectionHandler } from './ConnectionHandler';
import { useDragDropHandler } from './DragDropHandler';
import { useNodeTypeSelector } from './NodeTypeSelector';
import { useGraphSync } from '@/hooks/useGraphSync';
import { useGraphHistory } from '@/hooks/useGraphHistory';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
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

  // Initialize sync and history hooks (always call hooks, but adjust parameters)
  const { syncGraph, forceSyncGraph, loadGraphData, syncStatus } = useGraphSync({
    graphId: selectedGraph?.id || '',
    debounceMs: 1000,
    enableSync: hasValidGraph
  });

  const {
    canUndo,
    canRedo,
    addHistoryStateWithSync,
    undoOperation,
    redoOperation,
    initializeHistory,
    getUndoTooltip,
    getRedoTooltip
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
      console.log(`${operation}: ${historyOperation}`);
    }
  });

  // Add keyboard shortcuts for undo/redo
  useKeyboardShortcuts({
    onUndo: undoOperation,
    onRedo: redoOperation,
    canUndo,
    canRedo
  });

  

  // Load initial graph data from graph_data field
  useEffect(() => {
    if (selectedGraph) {
      console.log('🎯 Loading graph:', selectedGraph.id, selectedGraph);
      
      // Use graph_data if available, fallback to direct nodes/edges for backward compatibility
      const graphDataToLoad = selectedGraph.graph_data || {
        nodes: selectedGraph.nodes || [],
        edges: selectedGraph.edges || []
      };
      
      const { nodes: initialNodes, edges: initialEdges } = loadGraphData(graphDataToLoad);
      
      console.log(`🎯 Setting ${initialNodes.length} nodes and ${initialEdges.length} edges`);
      setNodes(initialNodes);
      setEdges(initialEdges);
      initializeHistory(initialNodes, initialEdges);
    }
  }, [selectedGraph?.id, loadGraphData, setNodes, setEdges, initializeHistory]);

  // Track node count to detect additions/removals
  const nodeCountRef = useRef(0);
  const lastMoveTimeRef = useRef(0);

  // Enhanced nodes change handler with coordinated history and sync
  const handleNodesChange: OnNodesChange = useCallback((changes) => {
    console.log('📝 Nodes changed:', changes);
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
            console.log('📝 Data change detected:', change);
            
            // Check if this is just automatic default initialization
            const item = change.item as Node;
            if (item.data?.autoInit) {
              console.log('⚠️ Skipping sync for automatic default initialization');
              return false; // Skip automatic default initialization
            }
          }
          
          return isDataChange;
        });
        
        console.log('🔄 Processing changes:', { 
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
          let shouldSync = true;
          
          if (hasNewNodes) {
            operation = 'create_node';
          } else if (hasRemovedNodes) {
            operation = 'delete_node';
          } else if (hasDataChanges) {
            operation = 'update_node';
            // Form data changes should sync immediately to preserve user input
            console.log('💾 Form data changed, syncing immediately');
          } else if (hasPositionChanges) {
            operation = 'move_node';
            // Debounce move operations - only sync after user stops moving for 1 second
            const now = Date.now();
            lastMoveTimeRef.current = now;
            
            setTimeout(() => {
              // Only sync if this was the last move operation
              if (lastMoveTimeRef.current === now) {
                console.log('💾 Syncing final move position');
                // Get fresh state for the delayed sync
                const latestNodes = getNodes();
                const latestEdges = getEdges();
                syncGraph(latestNodes, latestEdges);
              }
            }, 1000);
            
            shouldSync = false; // Don't sync immediately for moves
          }
          
          console.log('💾 Adding to history:', operation, shouldSync ? 'and syncing' : 'without immediate sync');
          
          // Add to history and optionally sync with fresh state
          addHistoryStateWithSync(
            currentNodes, 
            currentEdges, 
            operation, 
            undefined, 
            shouldSync ? syncGraph : undefined
          );
        }
      }, 10); // Small delay to ensure state is updated
    }
  }, [onNodesChange, getNodes, getEdges, addHistoryStateWithSync, syncGraph]);

  // Enhanced edges change handler with coordinated history and sync
  const handleEdgesChange: OnEdgesChange = useCallback((changes) => {
    console.log('🔗 Edges changed:', changes);
    
    onEdgesChange(changes);
    
    if (!historySuppressionRef.current) {
      // Use setTimeout to get updated edge state
      setTimeout(() => {
        // Get fresh node and edge state
        const currentNodes = getNodes();
        const currentEdges = getEdges();
        
        console.log('🔗 Current edges after change:', currentEdges);
        
        // Determine operation type from changes
        const hasNewEdges = changes.some(change => change.type === 'add');
        const hasRemovedEdges = changes.some(change => change.type === 'remove');
        const hasUpdatedEdges = changes.some(change => change.type === 'replace');
        
        console.log('🔄 Processing edge changes:', { 
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
          
          console.log('💾 Adding edge change to history and syncing:', operation);
          
          // Add to history first, then sync to backend with fresh state
          addHistoryStateWithSync(
            currentNodes, 
            currentEdges, 
            operation, 
            undefined, 
            syncGraph // Always sync for edge changes
          );
        } else {
          console.log('⚠️ No significant edge changes detected');
        }
      }, 10); // Small delay to ensure state is updated
    }
  }, [onEdgesChange, getNodes, getEdges, addHistoryStateWithSync, syncGraph]);

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
      // Double-check validation before adding the edge
      if (!isValidConnection(params)) {
        return;
      }
      
      // Clear connection info when a successful connection is made
      setDraggedConnectionInfo(null);
      
      setEdges((eds: Edge[]) => addEdge(params, eds));
    }, 
    [setEdges, isValidConnection]
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
      <EditorToolbar
        canUndo={canUndo}
        canRedo={canRedo}
        onUndo={undoOperation}
        onRedo={redoOperation}
        undoTooltip={getUndoTooltip()}
        redoTooltip={getRedoTooltip()}
        isSyncing={syncStatus.isSyncing}
        lastSyncedAt={syncStatus.lastSyncedAt}
        syncError={syncStatus.error}
        pendingChanges={syncStatus.pendingChanges}
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