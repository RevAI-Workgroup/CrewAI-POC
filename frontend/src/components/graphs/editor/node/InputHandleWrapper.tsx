import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { useHandleSelection } from '@/contexts/HandleSelectionProvider';
import type { FieldDefinition } from '@/types';

interface InputHandleWrapperProps {
  fieldName: string;
  field: FieldDefinition;
  nodeId: string;
  children: React.ReactNode;
}

const InputHandleWrapper: React.FC<InputHandleWrapperProps> = ({
  fieldName,
  field,
  nodeId,
  children
}) => {
  const { selectedHandle } = useHandleSelection();
  const handleId = `input-${nodeId}-${fieldName}`;
  const isSelected = selectedHandle?.handleId === handleId;

  return (
    <div className="flex items-center gap-3 p-3 hover:bg-muted/50 group relative">
      <Handle
        type="target"
        position={Position.Left}
        id={fieldName}
        className={`
          w-3 h-3 border-2 border-background transition-all
          ${isSelected 
            ? 'bg-primary ring-2 ring-primary/50' 
            : 'bg-muted-foreground group-hover:bg-primary'
          }
        `}
      />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium mb-1">
          {field.label}
          {field.required && <span className="text-red-500 ml-1">*</span>}
        </div>
        {children}
        {field.description && (
          <p className="text-xs text-muted-foreground mt-1">{field.description}</p>
        )}
      </div>
    </div>
  );
};

export default InputHandleWrapper; 