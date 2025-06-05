import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { cn } from '@/lib/utils';
import { useHandleSelection, type HandleInfo } from '@/contexts/HandleSelectionProvider';
import type { FieldDefinition } from '@/types';

interface NodeHandlesProps {
  nodeId: string;
  nodeType: string;
  fieldName?: string;
  field?: FieldDefinition;
  handleType: 'source' | 'target';
  onHandleClick: (e: React.MouseEvent) => void;
  getHandleCompatibleTypes: (handleInfo: HandleInfo) => string[];
}

interface InputHandleProps extends Omit<NodeHandlesProps, 'handleType'> {
  fieldName: string;
  field: FieldDefinition;
}

type OutputHandleProps = Pick<NodeHandlesProps, 'nodeId' | 'nodeType' | 'onHandleClick' | 'getHandleCompatibleTypes'>;

const InputHandle: React.FC<InputHandleProps> = ({
  nodeId,
  nodeType,
  fieldName,
  field,
  onHandleClick,
  getHandleCompatibleTypes
}) => {
  const {
    selectedHandle,
    isHandleSelected,
    shouldDimHandle,
    isHandleCompatible
  } = useHandleSelection();

  const handleInfo: HandleInfo = {
    nodeId,
    nodeType,
    fieldName,
    handleType: 'target',
    handleId: `input-${nodeId}-${fieldName}`
  };

  const isSelected = isHandleSelected(handleInfo.handleId);
  const isDimmed = shouldDimHandle(handleInfo);
  const isCompatible = selectedHandle ? isHandleCompatible(handleInfo) : false;
  const compatibleTypes = getHandleCompatibleTypes(handleInfo);

  return (
    <div className="relative space-y-2 w-full px-4">
      <HoverCard>
        <HoverCardTrigger>
          <Handle
            type="target"
            position={Position.Left}
            id={fieldName}
            onClick={onHandleClick}
            className={cn(
              "!w-3 !h-3 !border-2 transition-all duration-200 cursor-pointer absolute top-0 -left-12 rounded-full hover:drop-shadow-sm",
              {
                "!bg-blue-200 !border-blue-500 drop-shadow-blue-500/40": isSelected,
                "!bg-gray-100 !border-gray-300 opacity-30": isDimmed,
                "!bg-indigo-200 !border-white": !isSelected && !isDimmed && isCompatible,
                "!bg-indigo-200 !border-indigo-500": !isSelected && !isDimmed && !isCompatible
              }
            )}
          />
        </HoverCardTrigger>
        <HoverCardContent side="left" sideOffset={30}>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Input type:</span>
              <Badge variant="secondary">{nodeType}</Badge>
            </div>
            {isDimmed && (
              <div className="text-sm text-red-600 bg-red-50 p-2 rounded border">
                <p className="font-medium">⚠️ Connection Not Allowed</p>
                <p className="text-xs">This input is not compatible with the selected output due to connection constraints.</p>
              </div>
            )}
            <div className="text-sm text-muted-foreground">
              <p>Drag to connect compatible outputs</p>
              <p>Click to filter compatible outputs and components</p>
            </div>
            {compatibleTypes.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">Compatible with:</p>
                <div className="flex flex-wrap gap-1">
                  {compatibleTypes.slice(0, 3).map((type) => (
                    <Badge key={type} variant="outline" className="text-xs">
                      {type}
                    </Badge>
                  ))}
                  {compatibleTypes.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{compatibleTypes.length - 3} more
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </div>
        </HoverCardContent>
      </HoverCard>
      
      <Label>
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      
      {field.description && (
        <p className="text-xs text-muted-foreground">{field.description}</p>
      )}
    </div>
  );
};

const OutputHandle: React.FC<OutputHandleProps> = ({
  nodeId,
  nodeType,
  onHandleClick,
  getHandleCompatibleTypes
}) => {
  const {
    selectedHandle,
    isHandleSelected,
    shouldDimHandle,
    isHandleCompatible
  } = useHandleSelection();

  const handleInfo: HandleInfo = {
    nodeId,
    nodeType,
    handleType: 'source',
    handleId: `output-${nodeId}`
  };

  const isSelected = isHandleSelected(handleInfo.handleId);
  const isDimmed = shouldDimHandle(handleInfo);
  const isCompatible = selectedHandle ? isHandleCompatible(handleInfo) : false;
  const compatibleTypes = getHandleCompatibleTypes(handleInfo);

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <span>Output</span>
      <HoverCard>
        <HoverCardTrigger>
          <Handle
            type="source"
            position={Position.Right}
            id="output"
            onClick={onHandleClick}
            className={cn(
              "!w-3 !h-3 !border-2 transition-all duration-200 cursor-pointer rounded-full",
              {
                "!bg-blue-200 !border-blue-500": isSelected,
                "!bg-gray-100 !border-gray-300 opacity-30": isDimmed,
                "!bg-orange-200 !border-white": !isSelected && !isDimmed && isCompatible,
                "!bg-orange-200 !border-orange-500": !isSelected && !isDimmed && !isCompatible,
              }
            )}
            style={{
              right: '-6px',
              top: '50%',
              transform: 'translateY(-50%)',
            }}
          />
        </HoverCardTrigger>
        <HoverCardContent side="right" sideOffset={30}>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Output type:</span>
              <Badge variant="secondary">{nodeType}</Badge>
            </div>
            {isDimmed && (
              <div className="text-sm text-red-600 bg-red-50 p-2 rounded border">
                <p className="font-medium">⚠️ Connection Not Allowed</p>
                <p className="text-xs">This output cannot connect to the selected input due to connection constraints.</p>
              </div>
            )}
            <div className="text-sm text-muted-foreground">
              <p>Drag to connect compatible inputs</p>
              <p>Click to filter compatible inputs and components</p>
            </div>
            {compatibleTypes.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2">Compatible with:</p>
                <div className="flex flex-wrap gap-1">
                  {compatibleTypes.slice(0, 3).map((type) => (
                    <Badge key={type} variant="outline" className="text-xs">
                      {type}
                    </Badge>
                  ))}
                  {compatibleTypes.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{compatibleTypes.length - 3} more
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </div>
        </HoverCardContent>
      </HoverCard>
    </div>
  );
};

export { InputHandle, OutputHandle }; 