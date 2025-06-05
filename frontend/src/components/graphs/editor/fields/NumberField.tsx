import React from 'react';
import { Input } from '@/components/ui/input';
import type { FieldDefinition } from '@/types';

interface NumberFieldProps {
  fieldName: string;
  field: FieldDefinition;
  value: any;
  onFormChange: (fieldName: string, value: any) => void;
}

const NumberField: React.FC<NumberFieldProps> = ({
  fieldName,
  field,
  value,
  onFormChange
}) => {
  return (
    <Input
      type="number"
      placeholder={field.placeholder}
      value={value || ''}
      onChange={(e) => {
        const numValue = parseFloat(e.target.value);
        onFormChange(fieldName, isNaN(numValue) ? 0 : numValue);
      }}
      min={field.validation?.min}
      max={field.validation?.max}
      step={field.validation?.step}
    />
  );
};

export default NumberField; 