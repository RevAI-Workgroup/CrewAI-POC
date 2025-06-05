import { useCallback } from 'react';
import { type Node, type Edge } from '@xyflow/react';
import { useGraphStore } from '@/stores';
import { v4 as uuidv4 } from 'uuid';

interface NodeTypeSelectorProps {
  setNodes: (updater: (nodes: Node[]) => Node[]) => void;
  setEdges: (updater: (edges: Edge[]) => Edge[]) => void;
  setShowConnectionDialog: (show: boolean) => void;
  setConnectionDropPosition: (position: { x: number; y: number } | null) => void;
  setDraggedConnectionInfo: (info: any) => void;
}

export const useNodeTypeSelector = ({
  setNodes,
  setEdges,
  setShowConnectionDialog,
  setConnectionDropPosition,
  setDraggedConnectionInfo
}: NodeTypeSelectorProps) => {
  const { nodeDef } = useGraphStore();

  // Handle node type selection from dialog
  const handleNodeTypeSelection = useCallback((
    selectedNodeType: string,
    connectionDropPosition: { x: number; y: number } | null,
    draggedConnectionInfo: any
  ) => {
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
  }, [nodeDef, setNodes, setEdges, setShowConnectionDialog, setConnectionDropPosition, setDraggedConnectionInfo]);

  // Handle dialog close
  const handleDialogClose = useCallback(() => {
    setShowConnectionDialog(false);
    setConnectionDropPosition(null);
    setDraggedConnectionInfo(null);
  }, [setShowConnectionDialog, setConnectionDropPosition, setDraggedConnectionInfo]);

  return {
    handleNodeTypeSelection,
    handleDialogClose
  };
}; 