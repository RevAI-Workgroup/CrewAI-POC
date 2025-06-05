import React, { useCallback, useRef, useMemo, useState } from 'react';
import type { DragEvent } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  ReactFlow,
  useReactFlow,
  type Node,
  type Edge,
  type OnConnect,
  type Connection,
  type NodeTypes,
  type IsValidConnection,
  type OnConnectStart,
  type OnConnectEnd,
  type EdgeTypes,

} from '@xyflow/react';
import '@xyflow/react/dist/base.css';

import { useDnD } from '@/contexts/DnDProvider';
import { useHandleSelection } from '@/contexts/HandleSelectionProvider';
import CustomNode from './CustomNode';
import KeyboardShortcutsDialog from './KeyboardShortcutsDialog';

import { v4 as uuidv4 } from 'uuid';
import { useTheme } from '@/contexts/ThemeProvider';
import { useGraphStore } from '@/stores';
import type { NodeTypeDefinition } from '@/types';
import ShortcutsButton from './ShortcutsButton';
import ConnectionLine from './ConnectionLine';
import CustomEdge from './CustomEdge';
import ConnectionDropDialog from './ConnectionDropDialog';

const proOptions = { hideAttribution: true };

const FlowEditor: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { screenToFlowPosition, getNode } = useReactFlow();
  const { type, setType } = useDnD();
  const { clearSelection, startConnectionDrag, endConnectionDrag } = useHandleSelection();

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

  // Debug effect to track state changes (commented out)
  // useEffect(() => {
  //   console.log('State changed:', { 
  //     showConnectionDialog, 
  //     connectionDropPosition, 
  //     draggedConnectionInfo 
  //   });
  // }, [showConnectionDialog, connectionDropPosition, draggedConnectionInfo]);

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

  // Handle connection drag start
  const onConnectStart: OnConnectStart = useCallback((_, { nodeId, handleId, handleType }) => {
    if (!nodeId || !handleId || !handleType) return;
    
    const node = getNode(nodeId);
    if (!node) return;

    const nodeType = (node.data as any).type as string;
    const fieldName = handleType === 'source' ? undefined : handleId;

    const connectionInfo = {
      sourceNodeId: nodeId,
      sourceNodeType: nodeType,
      sourceHandle: handleId,
      handleType: handleType as 'source' | 'target'
    };
    
    // Store connection info for potential dialog
    setDraggedConnectionInfo(connectionInfo);

    startConnectionDrag({
      nodeId,
      nodeType,
      fieldName,
      handleType: handleType as 'source' | 'target',
      handleId: `${handleType === 'source' ? 'output' : 'input'}-${nodeId}${fieldName ? `-${fieldName}` : ''}`
    });
  }, [getNode, startConnectionDrag]);

  // Handle connection drag end
  const onConnectEnd: OnConnectEnd = useCallback((_event) => {
    endConnectionDrag();
    
    // Use setTimeout to check if connection was successful
    setTimeout(() => {
      // If we still have connection info, it means no successful connection was made
      if (draggedConnectionInfo) {
        // Get current mouse position from the last known position
        // Since ReactFlow doesn't provide mouse coordinates in onConnectEnd,
        // we'll place the node at a default offset from the source
        if (draggedConnectionInfo.sourceNodeId) {
          const sourceNode = getNode(draggedConnectionInfo.sourceNodeId);
          if (sourceNode) {
            const position = {
              x: sourceNode.position.x + 200,
              y: sourceNode.position.y
            };
            
            setConnectionDropPosition(position);
            setShowConnectionDialog(true);
          }
        }
      }
      
      // Clear connection info
      setDraggedConnectionInfo(null);
    }, 50);
  }, [endConnectionDrag, draggedConnectionInfo, getNode]);

  // Validate if a connection is allowed based on field constraints
  const isValidConnection: IsValidConnection = useCallback((connection: Connection | Edge) => {

    if (!nodeDef) {
      return true; // Allow connections if no node definitions
    }
    
    const sourceNode = getNode(connection.source!);
    const targetNode = getNode(connection.target!);
    
    if (!sourceNode || !targetNode) {
      return false;
    }
    
    // Can't connect to same node
    if (connection.source === connection.target) {
      return false;
    }
    
    // Get node types
    const sourceNodeType = (sourceNode.data as any).type as string;
    const targetNodeType = (targetNode.data as any).type as string;
    const targetFieldName = connection.targetHandle;
    
    
    if (!targetFieldName) {
      return false;
    }

    // Get the target field definition
    const targetNodeDef = nodeDef.node_types[targetNodeType];
    const targetField = targetNodeDef?.fields[targetFieldName];
    
    if (!targetField) {
      return false;
    }
    
    // If no filter is defined, allow the connection (basic compatibility)
    if (!targetField.filter) {
      return true;
    }
    
    // Check connection_constraints if they exist
    const fieldConstraintKey = `${targetNodeType}.${targetFieldName}`;
    const fieldConstraints = nodeDef.connection_constraints?.[fieldConstraintKey];
    
    if (fieldConstraints && fieldConstraints[targetFieldName]) {
      const constraints = fieldConstraints[targetFieldName];
      // Check if the source type matches the target_type constraint
      if (constraints.target_type && constraints.target_type !== sourceNodeType) {
        return false;
      }
    }
    
    // Check basic field filter compatibility
    if (targetField.filter.type) {
      const allowedTypes = Array.isArray(targetField.filter.type) 
        ? targetField.filter.type 
        : [targetField.filter.type];
      if (!allowedTypes.includes(sourceNodeType)) {
        return false;
      }
    }
    
    if (targetField.filter.category) {
      const allowedCategories = Array.isArray(targetField.filter.category)
        ? targetField.filter.category
        : [targetField.filter.category];
      const sourceNodeDef = nodeDef.node_types[sourceNodeType];
      if (!allowedCategories.includes(sourceNodeDef?.category || '')) {
        return false;
      }
    }
    
    return true;
  }, [nodeDef, getNode]);

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

  // Find compatible node types for the current source
  const getCompatibleNodeTypes = useCallback(() => {
    if (!draggedConnectionInfo || !nodeDef) return [];

    const { sourceNodeType, handleType } = draggedConnectionInfo;
    const compatibleTypes: Array<{
      nodeType: string;
      definition: NodeTypeDefinition;
      reason: string;
    }> = [];

    // If dragging from an output (source), find nodes with compatible input fields
    if (handleType === 'source') {
      Object.entries(nodeDef.node_types).forEach(([targetNodeType, targetNodeDef]) => {
        // Don't suggest the same node type
        if (targetNodeType === sourceNodeType) return;

        // Check each field to see if it can accept this source type
        Object.entries(targetNodeDef.fields).forEach(([fieldName, field]) => {
          if (!field.filter) return;

          // Check connection constraints
          const fieldConstraintKey = `${targetNodeType}.${fieldName}`;
          const fieldConstraints = nodeDef.connection_constraints?.[fieldConstraintKey];

          let isCompatible = false;
          let reason = '';

          if (fieldConstraints && fieldConstraints[fieldName]) {
            const constraints = fieldConstraints[fieldName];
            if (constraints.target_type === sourceNodeType) {
              isCompatible = true;
              reason = `Can connect to ${field.label || fieldName} field`;
            }
          } else if (field.filter.type) {
            const allowedTypes = Array.isArray(field.filter.type) 
              ? field.filter.type 
              : [field.filter.type];
            if (allowedTypes.includes(sourceNodeType)) {
              isCompatible = true;
              reason = `Compatible with ${field.label || fieldName} field`;
            }
          } else if (field.filter.category) {
            const allowedCategories = Array.isArray(field.filter.category)
              ? field.filter.category
              : [field.filter.category];
            const sourceNodeDef = nodeDef.node_types[sourceNodeType];
            if (allowedCategories.includes(sourceNodeDef?.category || '')) {
              isCompatible = true;
              reason = `Category match for ${field.label || fieldName} field`;
            }
          }

          if (isCompatible && !compatibleTypes.find(ct => ct.nodeType === targetNodeType)) {
            compatibleTypes.push({
              nodeType: targetNodeType,
              definition: targetNodeDef,
              reason
            });
          }
        });
      });
    }

    return compatibleTypes;
  }, [draggedConnectionInfo, nodeDef]);

  // Handle node type selection from dialog
  const handleNodeTypeSelection = useCallback((selectedNodeType: string) => {
    if (!connectionDropPosition || !draggedConnectionInfo || !nodeDef) return;

    const nodeDefinition = nodeDef.node_types[selectedNodeType];
    if (!nodeDefinition) return;

    // Create new node
    const newNodeId = uuidv4();
    const newNode: Node = {
      id: newNodeId,
      type: selectedNodeType,
      position: connectionDropPosition,
      data: { 
        label: nodeDefinition.name,
        type: selectedNodeType,
        formData: {}
      },
    };

    // Add the new node
    setNodes((nds: Node[]) => nds.concat(newNode));

    // Create the connection
    if (draggedConnectionInfo.handleType === 'source') {
      // Find a compatible input field in the new node
      const compatibleField = Object.entries(nodeDefinition.fields).find(([fieldName, field]) => {
        if (!field.filter) return false;

        // Check connection constraints first
        const fieldConstraintKey = `${selectedNodeType}.${fieldName}`;
        const fieldConstraints = nodeDef.connection_constraints?.[fieldConstraintKey];
        
        if (fieldConstraints && fieldConstraints[fieldName]) {
          const constraints = fieldConstraints[fieldName];
          return constraints.target_type === draggedConnectionInfo.sourceNodeType;
        }

        // Check field filters
        if (field.filter.type) {
          const allowedTypes = Array.isArray(field.filter.type) 
            ? field.filter.type 
            : [field.filter.type];
          return allowedTypes.includes(draggedConnectionInfo.sourceNodeType);
        }

        if (field.filter.category) {
          const allowedCategories = Array.isArray(field.filter.category)
            ? field.filter.category
            : [field.filter.category];
          const sourceNodeDef = nodeDef.node_types[draggedConnectionInfo.sourceNodeType];
          return allowedCategories.includes(sourceNodeDef?.category || '');
        }

        return false;
      });

      if (compatibleField) {
        const [fieldName] = compatibleField;
        const newEdge: Edge = {
          id: uuidv4(),
          source: draggedConnectionInfo.sourceNodeId,
          sourceHandle: draggedConnectionInfo.sourceHandle,
          target: newNodeId,
          targetHandle: fieldName,
        };

        setEdges((eds: Edge[]) => [...eds, newEdge]);
      }
    }

    // Close dialog and clear state
    setShowConnectionDialog(false);
    setConnectionDropPosition(null);
    setDraggedConnectionInfo(null);
  }, [connectionDropPosition, draggedConnectionInfo, nodeDef, setNodes, setEdges]);

  // Handle dialog close
  const handleDialogClose = useCallback(() => {
    setShowConnectionDialog(false);
    setConnectionDropPosition(null);
    setDraggedConnectionInfo(null);
  }, []);

  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle pane click to clear handle selection
  const onPaneClick = useCallback(() => {
    clearSelection();
  }, [clearSelection]);

  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();

      // Get the type from dataTransfer instead of just React state
      const draggedType = event.dataTransfer.getData('text/plain');
      // check if the dropped element is valid
      if (!draggedType || !nodeDef?.node_types[draggedType]) {
        console.log("No type from dataTransfer or node type not found");
        return;
      }

      // project was renamed to screenToFlowPosition
      // and you don't need to subtract the reactFlowBounds.left/top anymore
      // details: https://reactflow.dev/whats-new/2023-11-10
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const nodeDefinition = nodeDef.node_types[draggedType];
      const newNode: Node = {
        id: uuidv4(),
        type: draggedType,
        position,
        data: { 
          label: nodeDefinition.name,
          type: draggedType,
          formData: {}
        },
      };

      setNodes((nds: Node[]) => nds.concat(newNode));
      setType(null)
    },
    [screenToFlowPosition, type, setNodes, setType, nodeDef],
  );

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
        onSelectNodeType={handleNodeTypeSelection}
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
          panOnDrag={[1]} // Allow panning with left and middle mouse buttons
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