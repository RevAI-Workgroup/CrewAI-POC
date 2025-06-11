import React, { useEffect } from 'react';
import { ReactFlowProvider } from '@xyflow/react';

import { DnDProvider } from '@/contexts/DnDProvider';
import { HandleSelectionProvider } from '@/contexts/HandleSelectionProvider';
import { KeyboardShortcutsProvider } from '@/contexts/KeyboardShortcutsProvider';
import FlowEditor from './FlowEditor';

import type { Graph } from '@/types';
import useGraphStore from '@/stores/graphStore';

interface VisualEditorProps {
  graph: Graph;
}

const VisualEditor: React.FC<VisualEditorProps> = ({graph}) => {

  const { setSelectedGraph } = useGraphStore();

  useEffect(() => {
    console.debug('🔍 VisualEditor graph:', graph);
    setSelectedGraph(graph);
  }, [graph, setSelectedGraph]);

  return (
    <ReactFlowProvider>
      <DnDProvider>
        <HandleSelectionProvider>
          <KeyboardShortcutsProvider>
            <FlowEditor/>
          </KeyboardShortcutsProvider>
        </HandleSelectionProvider>
      </DnDProvider>
    </ReactFlowProvider>
  )
};

export default VisualEditor;