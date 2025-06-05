import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X, Eye, EyeOff } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { ScrollArea } from '@/components/ui/scroll-area';
import { DynamicIcon } from '@/components/DynamicIcon';
import type { NodeTypeDefinition } from '@/types';

interface CustomNodeData {
  label: string;
  type: string;
  formData?: Record<string, any>;
  fieldVisibility?: Record<string, boolean>;
  [key: string]: unknown;
}

interface NodeSettingsPanelProps {
  nodeData: CustomNodeData;
  nodeDefinition: NodeTypeDefinition;
  onFormChange: (fieldName: string, value: any) => void;
  onClose: () => void;
}

const NodeSettingsPanel: React.FC<NodeSettingsPanelProps> = ({
  nodeData,
  nodeDefinition,
  onFormChange,
  onClose,
}) => {
  const panelRef = useRef<HTMLDivElement>(null);
  const [fieldVisibility, setFieldVisibility] = useState<Record<string, boolean>>(() => {
    // Initialize field visibility from node data or use field's show_by_default setting
    const savedVisibility = nodeData.fieldVisibility || {};
    const defaultVisibility: Record<string, boolean> = {};
    
    Object.entries(nodeDefinition.fields).forEach(([fieldName, field]) => {
      // Use saved visibility if available, otherwise use field's show_by_default setting
      defaultVisibility[fieldName] = savedVisibility[fieldName] !== undefined 
        ? savedVisibility[fieldName] 
        : field.show_by_default;
    });
    
    return defaultVisibility;
  });

  // Handle click outside to close panel
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  // Handle field visibility toggle
  const handleFieldVisibilityToggle = useCallback((fieldName: string, visible: boolean) => {
    const newVisibility = {
      ...fieldVisibility,
      [fieldName]: visible,
    };
    setFieldVisibility(newVisibility);
    
    // Save visibility to form data
    onFormChange('fieldVisibility', newVisibility);
  }, [fieldVisibility, onFormChange]);

  return (
    <div 
      ref={panelRef}
      className="absolute left-full top-0 ml-4 z-50"
      style={{ width: '300px' }}
    >
      <Card className="shadow-xl border-2 bg-background">
        <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2 text-sm">
            <DynamicIcon 
              name={nodeDefinition.icon} 
              className="w-4 h-4 text-muted-foreground" 
            />
            Node Settings
          </CardTitle>
          <Button
            size="sm"
            variant="ghost"
            onClick={onClose}
            className="h-6 w-6 p-0"
          >
            <X className="w-3 h-3" />
          </Button>
        </CardHeader>
        
        <CardContent className="p-0">
          <ScrollArea className="h-80 px-4 pb-4">
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-3">Field Visibility</h4>
                <div className="space-y-3">
                  {Object.entries(nodeDefinition.fields).map(([fieldName, field]) => {
                    const isDefaultVisible = field.show_by_default;
                    const isVisible = fieldVisibility[fieldName];
                    
                    return (
                      <div key={fieldName} className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-1">
                          {isVisible ? (
                            <Eye className="w-4 h-4 text-muted-foreground" />
                          ) : (
                            <EyeOff className="w-4 h-4 text-muted-foreground" />
                          )}
                          <div className="flex-1">
                            <div className={`text-sm font-medium ${isDefaultVisible ? 'text-foreground' : 'text-muted-foreground'}`}>
                              {field.label || fieldName}
                              {isDefaultVisible && (
                                <span className="ml-1 text-xs text-muted-foreground">(default)</span>
                              )}
                            </div>
                            {field.description && (
                              <div className="text-xs text-muted-foreground">{field.description}</div>
                            )}
                          </div>
                        </div>
                        <Switch
                          checked={isVisible}
                          onCheckedChange={(checked) => 
                            handleFieldVisibilityToggle(fieldName, checked)
                          }
                          disabled={isDefaultVisible}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="border-t pt-4">
                <h4 className="text-sm font-medium mb-2">Node Information</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Type:</span>
                    <span>{nodeDefinition.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Category:</span>
                    <span>{nodeDefinition.category}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Fields:</span>
                    <span>{Object.keys(nodeDefinition.fields).length}</span>
                  </div>
                </div>
              </div>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default NodeSettingsPanel; 