import { useCallback } from 'react';
import { useReactFlow, type Node } from '@xyflow/react';
import { useDnD } from '@/contexts/DnDProvider';
import { useGraphStore } from '@/stores';
import { v4 as uuidv4 } from 'uuid';
import type { DragEvent } from 'react';
import { initializeNodeDefaults } from '@/utils/nodeDefaults';

interface DragDropHandlerProps {
  setNodes: (updater: (nodes: Node[]) => Node[]) => void;
}

export const useDragDropHandler = ({ setNodes }: DragDropHandlerProps) => {
  const { screenToFlowPosition } = useReactFlow();
  const { setType } = useDnD();
  const { nodeDef } = useGraphStore();



  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

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
      
      // Initialize default form data and field visibility
      const { formData, fieldVisibility } = initializeNodeDefaults(draggedType, nodeDef);
      
      const newNode: Node = {
        id: uuidv4(),
        type: draggedType,
        position,
        data: { 
          label: nodeDefinition.name,
          type: draggedType,
          formData,
          fieldVisibility
        },
      };

      setNodes((nds: Node[]) => nds.concat(newNode));
      setType(null);
    },
    [screenToFlowPosition, setNodes, setType, nodeDef],
  );

  return {
    onDragOver,
    onDrop
  };
}; 