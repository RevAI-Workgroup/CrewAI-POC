import { useCallback } from 'react';
import { useReactFlow, type OnConnectStart, type OnConnectEnd, type IsValidConnection, type Connection, type Edge } from '@xyflow/react';
import { useHandleSelection } from '@/contexts/HandleSelectionProvider';
import { useGraphStore } from '@/stores';
import { v4 as uuidv4 } from 'uuid';

interface ConnectionHandlerProps {
  setDraggedConnectionInfo: (info: any) => void;
  setConnectionDropPosition: (position: { x: number; y: number } | null) => void;
  setShowConnectionDialog: (show: boolean) => void;
  draggedConnectionInfo: any;
  setEdges: (updater: (edges: Edge[]) => Edge[]) => void;
}

export const useConnectionHandler = ({
  setDraggedConnectionInfo,
  setConnectionDropPosition,
  setShowConnectionDialog,
  draggedConnectionInfo,
  setEdges
}: ConnectionHandlerProps) => {
  const { getNode } = useReactFlow();
  const { startConnectionDrag, endConnectionDrag } = useHandleSelection();
  const { nodeDef } = useGraphStore();

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
  }, [getNode, startConnectionDrag, setDraggedConnectionInfo]);

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
  }, [endConnectionDrag, draggedConnectionInfo, getNode, setConnectionDropPosition, setShowConnectionDialog, setDraggedConnectionInfo]);

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

  // Find compatible node types for the current source
  const getCompatibleNodeTypes = useCallback(() => {
    if (!draggedConnectionInfo || !nodeDef) return [];

    const { sourceNodeType, handleType } = draggedConnectionInfo;
    const compatibleTypes: Array<{
      nodeType: string;
      definition: any;
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

  return {
    onConnectStart,
    onConnectEnd,
    isValidConnection,
    getCompatibleNodeTypes
  };
}; 