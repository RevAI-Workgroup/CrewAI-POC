import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { DynamicIcon } from '@/components/DynamicIcon';
import type { NodeTypeDefinition } from '@/types';

interface CompatibleNodeType {
  nodeType: string;
  definition: NodeTypeDefinition;
  reason: string;
}

interface ConnectionDropDialogProps {
  isOpen: boolean;
  onClose: () => void;
  compatibleTypes: CompatibleNodeType[];
  onSelectNodeType: (nodeType: string) => void;
  sourceNodeType?: string;
  sourceHandle?: string;
}

const ConnectionDropDialog: React.FC<ConnectionDropDialogProps> = ({
  isOpen,
  onClose,
  compatibleTypes,
  onSelectNodeType,
  sourceNodeType,
  sourceHandle
}) => {
  const handleNodeTypeSelect = (nodeType: string) => {
    onSelectNodeType(nodeType);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>Connect to New Node</span>
          </DialogTitle>
          {sourceNodeType && sourceHandle && (
            <p className="text-sm text-muted-foreground">
              Select a node type to connect from <strong>{sourceNodeType}</strong>
            </p>
          )}
        </DialogHeader>
        
        <div className="space-y-4">
          {compatibleTypes.length > 0 ? (
            <ScrollArea className="h-80">
              <div className="space-y-2 pr-4">
                {compatibleTypes.map(({ nodeType, definition, reason }) => (
                  <Button
                    key={nodeType}
                    variant="outline"
                    className="w-full justify-start h-auto p-4"
                    onClick={() => handleNodeTypeSelect(nodeType)}
                  >
                    <div className="flex items-start gap-3">
                      <DynamicIcon 
                        name={definition.icon} 
                        className="w-5 h-5 text-muted-foreground mt-0.5" 
                      />
                      <div className="flex-1 text-left">
                        <div className="font-medium">{definition.name}</div>
                        {definition.description && (
                          <div className="text-xs text-muted-foreground mt-1">
                            {definition.description}
                          </div>
                        )}
                        <div className="text-xs text-primary mt-1">
                          {reason}
                        </div>
                      </div>
                    </div>
                  </Button>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                No compatible node types found for this connection.
              </p>
            </div>
          )}
          
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ConnectionDropDialog; 