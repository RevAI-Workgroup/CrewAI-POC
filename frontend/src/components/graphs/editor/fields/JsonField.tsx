import React from 'react';
import { Textarea } from '@/components/ui/textarea';
import type { FieldDefinition } from '@/types';

interface JsonFieldProps {
  fieldName: string;
  field: FieldDefinition;
  value: any;
  onFormChange: (fieldName: string, value: any) => void;
}

const JsonField: React.FC<JsonFieldProps> = ({
  fieldName,
  field,
  value,
  onFormChange
}) => {
  const displayValue = typeof value === 'string' ? value : JSON.stringify(value || {}, null, 2);
  
  return (
    <Textarea
      placeholder={field.placeholder || 'Enter JSON...'}
      value={displayValue}
      onChange={(e) => {
        try {
          const parsed = JSON.parse(e.target.value);
          onFormChange(fieldName, parsed);
        } catch {
          // Keep the raw string value if JSON is invalid
          onFormChange(fieldName, e.target.value);
        }
      }}
      rows={4}
      className="font-mono text-sm"
    />
  );
};

export default JsonField; 