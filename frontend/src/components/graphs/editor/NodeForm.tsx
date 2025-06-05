import React, { useCallback, useMemo } from 'react';
import { Label } from '@/components/ui/label';
import { Form } from '@/components/ui/form';
import type { NodeTypeDefinition, FieldDefinition } from '@/types';
import { type UseFormReturn } from 'react-hook-form';

// Import field components
import {
  StringField,
  TextAreaField,
  NumberField,
  BooleanField,
  SelectField,
  MultiSelectField,
  SliderField,
  JsonField
} from './fields';

interface NodeFormProps {
  nodeDefinition: NodeTypeDefinition;
  localFormData: Record<string, any>;
  onFormChange: (fieldName: string, value: any) => void;
  form: UseFormReturn<any>;
  fieldNeedsHandle: (field: FieldDefinition) => boolean;
  renderInputHandle: (fieldName: string, field: FieldDefinition) => React.ReactNode;
  fieldVisibility?: Record<string, boolean>;
}

// Field component mapping for better maintainability
const fieldComponents = {
  string: StringField,
  password: StringField,
  text: TextAreaField,
  number: NumberField,
  boolean: BooleanField,
  select: SelectField,
  multi_select: MultiSelectField,
  slider: SliderField,
  json: JsonField,
} as const;

const NodeForm: React.FC<NodeFormProps> = ({
  nodeDefinition,
  localFormData,
  onFormChange,
  form,
  fieldNeedsHandle,
  renderInputHandle,
  fieldVisibility
}) => {
  // Memoize sorted and filtered fields for performance
  const sortedFields = useMemo(() => {
    return Object.entries(nodeDefinition.fields)
      .filter(([fieldName, field]) => {
        // For fields that are visible by default, always show them
        if (field.show_by_default) {
          return true;
        }
        
        // For fields that are hidden by default, only show them if explicitly made visible
        return fieldVisibility?.[fieldName] === true;
      })
      .sort(([, a], [, b]) => a.display_order - b.display_order);
  }, [nodeDefinition.fields, fieldVisibility]);

  // Get default value for a field
  const getFieldValue = useCallback((fieldName: string, field: FieldDefinition) => {
    const currentValue = localFormData[fieldName];
    
    if (currentValue !== undefined && currentValue !== null) {
      return currentValue;
    }
    
    if (field.default !== undefined) {
      return field.default;
    }
    
    // Return appropriate default based on field type
    switch (field.type) {
      case 'select':
        return field.options?.[0]?.value || '';
      case 'multi_select':
        return [];
      case 'boolean':
        return false;
      case 'number':
      case 'slider':
        return field.validation?.min || 0;
      case 'json':
        return {};
      default:
        return '';
    }
  }, [localFormData]);

  // Render field component based on type
  const renderField = useCallback((fieldName: string, field: FieldDefinition) => {
    const value = getFieldValue(fieldName, field);
    const hasHandle = fieldNeedsHandle(field);

    // Don't render input component if field has a handle
    if (hasHandle) {
      return renderInputHandle(fieldName, field);
    }

    // Get the appropriate field component
    const FieldComponent = fieldComponents[field.type as keyof typeof fieldComponents] || StringField;

    return (
      <div key={fieldName} className="space-y-2 px-4">
        {field.type !== 'boolean' && (
          <Label htmlFor={fieldName} className="text-sm font-medium">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
        )}
        
        <FieldComponent
          fieldName={fieldName}
          field={field}
          value={value}
          onFormChange={onFormChange}
        />
        
        {field.description && (
          <p className="text-xs text-muted-foreground">{field.description}</p>
        )}
      </div>
    );
  }, [getFieldValue, fieldNeedsHandle, onFormChange, renderInputHandle]);

  return (
    <Form {...form}>
      <div className="space-y-4">
        {sortedFields.map(([fieldName, field]) => renderField(fieldName, field))}
      </div>
    </Form>
  );
};

export default NodeForm; 