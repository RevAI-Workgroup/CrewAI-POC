import React, { useRef, useMemo, useState, useCallback, useEffect } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
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

const FlowEditor: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
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

  // Initialize sync and history hooks
  const { syncGraph, forceSyncGraph, loadGraphData, syncStatus } = useGraphSync({
    graphId: selectedGraph?.id || '',
    debounceMs: 2000,
    enableSync: !!selectedGraph?.id
  });

  const {
    canUndo,
    canRedo,
    addHistoryState,
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

  // Load initial graph data
  useEffect(() => {
    if (selectedGraph) {
      const { nodes: initialNodes, edges: initialEdges } = loadGraphData({
        nodes: selectedGraph.nodes || [],
        edges: selectedGraph.edges || []
      });
      setNodes(initialNodes);
      setEdges(initialEdges);
      initializeHistory(initialNodes, initialEdges);
    }
  }, [selectedGraph?.id, loadGraphData, setNodes, setEdges, initializeHistory]);

  // Enhanced nodes change handler with coordinated history and sync
  const handleNodesChange: OnNodesChange = useCallback((changes) => {
    onNodesChange(changes);
    
    if (!historySuppressionRef.current) {
      // Determine operation type from changes
      const hasNewNodes = changes.some(change => change.type === 'add');
      const hasRemovedNodes = changes.some(change => change.type === 'remove');
      const hasPositionChanges = changes.some(change => change.type === 'position' && change.position);
      
              // Coordinate history and sync together
        setTimeout(() => {
          let operation: HistoryOperation = 'update_node';
          if (hasNewNodes) operation = 'create_node';
          else if (hasRemovedNodes) operation = 'delete_node';
          else if (hasPositionChanges) operation = 'move_node';
          
          // Add to history first, then sync to backend
          addHistoryStateWithSync(
            nodes, 
            edges, 
            operation, 
            undefined, 
            nodes.length > 0 ? syncGraph : undefined
          );
        }, 50); // Small delay to ensure state is updated
    }
    }, [onNodesChange, nodes, edges, addHistoryStateWithSync, syncGraph]);

  // Enhanced edges change handler with coordinated history and sync
  const handleEdgesChange: OnEdgesChange = useCallback((changes) => {
    onEdgesChange(changes);
    
    if (!historySuppressionRef.current) {
      // Determine operation type from changes
      const hasNewEdges = changes.some(change => change.type === 'add');
      const hasRemovedEdges = changes.some(change => change.type === 'remove');
      
      // Coordinate history and sync together
      setTimeout(() => {
        const operation: HistoryOperation = hasNewEdges ? 'create_edge' : hasRemovedEdges ? 'delete_edge' : 'update_node';
        
        // Add to history first, then sync to backend
        addHistoryStateWithSync(
          nodes, 
          edges, 
          operation, 
          undefined, 
          nodes.length > 0 ? syncGraph : undefined
        );
      }, 50); // Small delay to ensure state is updated
    }
  }, [onEdgesChange, nodes, edges, addHistoryStateWithSync, syncGraph]);

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
        className="absolute top-4 left-4 z-10"
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