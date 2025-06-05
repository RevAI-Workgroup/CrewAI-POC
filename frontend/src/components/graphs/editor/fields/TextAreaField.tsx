import React from 'react';
import { Textarea } from '@/components/ui/textarea';
import type { FieldDefinition } from '@/types';

interface TextAreaFieldProps {
  fieldName: string;
  field: FieldDefinition;
  value: any;
  onFormChange: (fieldName: string, value: any) => void;
}

const TextAreaField: React.FC<TextAreaFieldProps> = ({
  fieldName,
  field,
  value,
  onFormChange
}) => {
  return (
    <Textarea
      placeholder={field.placeholder}
      value={value || ''}
      onChange={(e) => onFormChange(fieldName, e.target.value)}
      rows={3}
    />
  );
};

export default TextAreaField; 