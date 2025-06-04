import React, { useCallback, useRef } from 'react';
import type { DragEvent } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  addEdge,
  ReactFlow,
  useReactFlow,
  type Node,
  type Edge,
  type OnConnect,
  type Connection
} from '@xyflow/react';
import '@xyflow/react/dist/base.css';

import { EditorSidebar } from './Sidebar';
import { DnDProvider, useDnD } from '@/contexts/DnDContext';
import type { VisualEditorState } from '@/types';

import { v4 as uuidv4 } from 'uuid';
import { useTheme } from '@/contexts/ThemeContext';



interface VisualEditorProps {
  onSave?: (state: VisualEditorState) => void;
  onLoad?: () => VisualEditorState | null;
}

const proOptions = { hideAttribution: true };

const DnDFlow: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { screenToFlowPosition } = useReactFlow();
  const { type } = useDnD();

  const {theme} = useTheme();

  const onConnect: OnConnect = useCallback(
    (params: Connection) => setEdges((eds: Edge[]) => addEdge(params, eds)), 
    [setEdges]
  );

  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();

      // check if the dropped element is valid
      if (!type) {
        return;
      }

      // project was renamed to screenToFlowPosition
      // and you don't need to subtract the reactFlowBounds.left/top anymore
      // details: https://reactflow.dev/whats-new/2023-11-10
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode: Node = {
        id: uuidv4(),
        type: type || 'default',
        position,
        data: { label: `${type || 'default'} node` },
      };

      setNodes((nds: Node[]) => nds.concat(newNode));
    },
    [screenToFlowPosition, type, setNodes],
  );

  return (
    <div className="flex h-full w-full ">
      <EditorSidebar />
      
      {/* Main flow area */}
      <div className="flex-1 h-full" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          fitView
          proOptions={proOptions}
          colorMode={theme} // or 'dark' based on your theme context
          
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

const VisualEditor: React.FC<VisualEditorProps> = () => (
  <ReactFlowProvider>
    <DnDProvider>
      <DnDFlow />
    </DnDProvider>
  </ReactFlowProvider>
);

export default VisualEditor;