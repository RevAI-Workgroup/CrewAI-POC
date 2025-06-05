import React from 'react';
import { Handle, Position } from '@xyflow/react';
import type { NodeTypeDefinition } from '@/types';

interface NodeHeaderProps {
  nodeType: string;
  nodeDefinition: NodeTypeDefinition;
  nodeName: string;
  hasOutputHandle: boolean;
}

const NodeHeader: React.FC<NodeHeaderProps> = ({
  nodeType,
  nodeDefinition,
  nodeName,
  hasOutputHandle
}) => {
  return (
    <div className="flex items-center justify-between p-3 bg-muted rounded-t-lg border-b">
      <div className="flex items-center gap-2">
        <div
          className="w-3 h-3 rounded-full flex-shrink-0"
          style={{ backgroundColor: nodeDefinition.color || '#9CA3AF' }}
        />
        <div className="min-w-0">
          <div className="text-sm font-medium text-foreground truncate">
            {nodeName || nodeDefinition.name}
          </div>
          <div className="text-xs text-muted-foreground">{nodeType}</div>
        </div>
      </div>

      {/* Output handle */}
      {hasOutputHandle && (
        <Handle
          type="source"
          position={Position.Right}
          id="output"
          className="w-3 h-3 border-2 border-background bg-primary"
        />
      )}
    </div>
  );
};

export default NodeHeader; 