import React from 'react';
import { Button } from '@/components/ui/button';
import { Trash2, Copy, Settings } from 'lucide-react';

interface NodeToolbarProps {
  onDelete: () => void;
  onDuplicate: () => void;
  onSettings?: () => void;
}

const NodeToolbar: React.FC<NodeToolbarProps> = ({
  onDelete,
  onDuplicate,
  onSettings
}) => {
  return (
    <div className="absolute -top-12 left-0 flex gap-1 bg-background border rounded-md shadow-lg p-1 z-10">
      <Button
        size="sm"
        variant="ghost"
        onClick={onDuplicate}
        className="h-8 w-8 p-0"
        title="Duplicate node"
      >
        <Copy className="h-4 w-4" />
      </Button>
      {onSettings && (
        <Button
          size="sm"
          variant="ghost"
          onClick={onSettings}
          className="h-8 w-8 p-0"
          title="Node settings"
        >
          <Settings className="h-4 w-4" />
        </Button>
      )}
      <Button
        size="sm"
        variant="ghost"
        onClick={onDelete}
        className="h-8 w-8 p-0 text-destructive hover:text-destructive"
        title="Delete node"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
};

export default NodeToolbar; 