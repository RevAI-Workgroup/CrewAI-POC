import React from 'react';
import { Button } from '@/components/ui/button';
import { Copy, Trash2, Settings, Clipboard } from 'lucide-react';
import {
  NodeToolbar,
  Position,
} from '@xyflow/react';
 
import '@xyflow/react/dist/style.css';

interface NodeToolbarProps {
  selected: boolean;
  onCopy: () => void;
  onDuplicate: () => void;
  onSettings: () => void;
  onDelete: () => void;
}

const ToolbarNode: React.FC<NodeToolbarProps> = ({
  selected,
  onCopy,
  onDuplicate,
  onSettings,
  onDelete
}) => {
  if (!selected) return null;

  return (
    <NodeToolbar
    isVisible={selected}
    position={Position.Top}
    className="flex items-center gap-1 bg-background border rounded-md shadow-lg p-1">
      <Button
        size="sm"
        variant="ghost"
        onClick={onCopy}
        className="h-8 w-8 p-0"
        title="Copy node (Ctrl+C)"
      >
        <Clipboard className="w-3 h-3" />
      </Button>
      <Button
        size="sm"
        variant="ghost"
        onClick={onDuplicate}
        className="h-8 w-8 p-0"
        title="Duplicate node (Ctrl+D)"
      >
        <Copy className="w-3 h-3" />
      </Button>
      <Button
        size="sm"
        variant="ghost"
        onClick={onSettings}
        className="h-8 w-8 p-0"
        title="Node settings"
      >
        <Settings className="w-3 h-3" />
      </Button>
      <Button
        size="sm"
        variant="ghost"
        onClick={onDelete}
        className="h-8 w-8 p-0 text-red-500 hover:text-red-600"
        title="Delete node (Delete)"
      >
        <Trash2 className="w-3 h-3" />
      </Button>
    </NodeToolbar>
  );
};

export default ToolbarNode;