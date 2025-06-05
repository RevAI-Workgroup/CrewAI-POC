import React from 'react';
import { Input } from '@/components/ui/input';
import type { FieldDefinition } from '@/types';

interface StringFieldProps {
  fieldName: string;
  field: FieldDefinition;
  value: any;
  onFormChange: (fieldName: string, value: any) => void;
}

const StringField: React.FC<StringFieldProps> = ({
  fieldName,
  field,
  value,
  onFormChange
}) => {
  return (
    <Input
      type={field.type === 'password' ? 'password' : 'text'}
      placeholder={field.placeholder}
      value={value || ''}
      onChange={(e) => onFormChange(fieldName, e.target.value)}
    />
  );
};

export default StringField; 