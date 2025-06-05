import React, { useRef, useMemo, useState, useCallback } from 'react';
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

// Import custom hooks
import { useConnectionHandler } from './ConnectionHandler';
import { useDragDropHandler } from './DragDropHandler';
import { useNodeTypeSelector } from './NodeTypeSelector';

const proOptions = { hideAttribution: true };

const FlowEditor: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { clearSelection } = useHandleSelection();

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
  const { nodeDef } = useGraphStore();

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
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
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