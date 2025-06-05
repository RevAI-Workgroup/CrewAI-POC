import React, { useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Form } from '@/components/ui/form';
import type { NodeTypeDefinition, FieldDefinition } from '@/types';
import { type UseFormReturn } from 'react-hook-form';

interface NodeFormProps {
  nodeDefinition: NodeTypeDefinition;
  localFormData: Record<string, any>;
  onFormChange: (fieldName: string, value: any) => void;
  form: UseFormReturn<any>;
  fieldNeedsHandle: (field: FieldDefinition) => boolean;
  renderInputHandle: (fieldName: string, field: FieldDefinition) => React.ReactNode;
  fieldVisibility?: Record<string, boolean>;
}

const NodeForm: React.FC<NodeFormProps> = ({
  nodeDefinition,
  localFormData,
  onFormChange,
  form,
  fieldNeedsHandle,
  renderInputHandle,
  fieldVisibility
}) => {
  // Sort fields by display_order and filter by visibility
  const sortedFields = Object.entries(nodeDefinition.fields)
    .filter(([fieldName, field]) => {
      // For fields that are visible by default, always show them
      if (field.show_by_default) {
        return true;
      }
      
      // For fields that are hidden by default, only show them if explicitly made visible
      const isVisible = fieldVisibility ? fieldVisibility[fieldName] === true : false;
      return isVisible;
    })
    .sort(([, a], [, b]) => a.display_order - b.display_order);

  // Render field component based on type
  const renderField = useCallback((fieldName: string, field: FieldDefinition) => {
    const value = localFormData[fieldName] ?? field.default ?? (field.type === 'select' ? field.options?.[0]?.value : '');
    const hasHandle = fieldNeedsHandle(field);

    // Don't render input component if field has a handle
    if (hasHandle) {
      return renderInputHandle(fieldName, field);
    }

    const fieldComponent = (() => {
      switch (field.type) {
        case 'string':
        case 'password':
          return (
            <Input
              type={field.type === 'password' ? 'password' : 'text'}
              placeholder={field.placeholder}
              value={value}
              onChange={(e) => onFormChange(fieldName, e.target.value)}
            />
          );

        case 'text':
          return (
            <Textarea
              placeholder={field.placeholder}
              value={value}
              onChange={(e) => onFormChange(fieldName, e.target.value)}
              rows={3}
            />
          );

        case 'number':
          return (
            <Input
              type="number"
              placeholder={field.placeholder}
              value={value}
              onChange={(e) => onFormChange(fieldName, parseFloat(e.target.value) || 0)}
              min={field.validation?.min}
              max={field.validation?.max}
            />
          );

        case 'boolean':
          return (
            <div className="flex items-center space-x-2">
              <Checkbox
                checked={Boolean(value)}
                onCheckedChange={(checked) => onFormChange(fieldName, checked)}
              />
              <Label className="text-sm">{field.label}</Label>
            </div>
          );

        case 'select':
          return (
            <Select
              value={value}
              onValueChange={(value) => onFormChange(fieldName, value)}

            >
              <SelectTrigger className='w-full' id={fieldName}>
                <SelectValue placeholder={`Select a ${fieldName}`} />
              </SelectTrigger>
              <SelectContent>
                {field.options?.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          );

        case 'multi_select':
          return (
            <div className="space-y-2">
              {field.options?.map((option) => (
                <div key={option.value} className="flex items-center space-x-2">
                  <Checkbox
                    checked={(value || []).includes(option.value)}
                    onCheckedChange={(checked) => {
                      const currentValues = value || [];
                      const newValues = checked
                        ? [...currentValues, option.value]
                        : currentValues.filter((v: string) => v !== option.value);
                      onFormChange(fieldName, newValues);
                    }}
                  />
                  <Label className="text-sm">{option.label}</Label>
                </div>
              ))}
            </div>
          );

        case 'slider':
          return (
            <div className="space-y-2">
              <Slider
                value={[value || field.validation?.min || 0]}
                onValueChange={(values) => onFormChange(fieldName, values[0])}
                min={field.validation?.min || 0}
                max={field.validation?.max || 100}
                step={field.validation?.step || 1}
                className="w-full"
              />
              <div className="text-xs text-muted-foreground text-center">
                {value || field.validation?.min || 0}
              </div>
            </div>
          );

        case 'json':
          return (
            <Textarea
              placeholder={field.placeholder || 'Enter JSON...'}
              value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  onFormChange(fieldName, parsed);
                } catch {
                  onFormChange(fieldName, e.target.value);
                }
              }}
              rows={4}
              className="font-mono text-sm"
            />
          );

        default:
          return (
            <Input
              placeholder={field.placeholder}
              value={value}
              onChange={(e) => onFormChange(fieldName, e.target.value)}
            />
          );
      }
    })();

    return (
      <div key={fieldName} className="space-y-2 px-4">
        {field.type !== 'boolean' && (
          <Label className="">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
        )}
        
        {fieldComponent}
        
        {field.description && (
          <p className="text-xs text-muted-foreground">{field.description}</p>
        )}
      </div>
    );
  }, [localFormData, fieldNeedsHandle, onFormChange, renderInputHandle]);

  return (
    <Form {...form}>
      {sortedFields.map(([fieldName, field]) => renderField(fieldName, field))}
    </Form>
  );
};

export default NodeForm; 