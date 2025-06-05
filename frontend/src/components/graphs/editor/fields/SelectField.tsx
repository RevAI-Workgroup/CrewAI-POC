import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { FieldDefinition } from '@/types';

interface SelectFieldProps {
  fieldName: string;
  field: FieldDefinition;
  value: any;
  onFormChange: (fieldName: string, value: any) => void;
}

const SelectField: React.FC<SelectFieldProps> = ({
  fieldName,
  field,
  value,
  onFormChange
}) => {
  return (
    <Select
      value={value || ''}
      onValueChange={(newValue) => onFormChange(fieldName, newValue)}
    >
      <SelectTrigger className="w-full" id={fieldName}>
        <SelectValue placeholder={`Select ${field.label || fieldName}`} />
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
};

export default SelectField; 