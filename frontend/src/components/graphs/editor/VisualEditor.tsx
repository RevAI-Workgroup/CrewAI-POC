import React from 'react';
import { ReactFlowProvider } from '@xyflow/react';

import { DnDProvider } from '@/contexts/DnDProvider';
import { HandleSelectionProvider } from '@/contexts/HandleSelectionProvider';
import { KeyboardShortcutsProvider } from '@/contexts/KeyboardShortcutsProvider';
import FlowEditor from './FlowEditor';

import type { Graph } from '@/types';

interface VisualEditorProps {
  graph: Graph;
}

const VisualEditor: React.FC<VisualEditorProps> = () => (
  <ReactFlowProvider>
    <DnDProvider>
      <HandleSelectionProvider>
        <KeyboardShortcutsProvider>
          <FlowEditor/>
        </KeyboardShortcutsProvider>
      </HandleSelectionProvider>
    </DnDProvider>
  </ReactFlowProvider>
);

export default VisualEditor;