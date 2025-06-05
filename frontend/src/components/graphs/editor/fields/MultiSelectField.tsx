import React from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import type { FieldDefinition } from '@/types';

interface MultiSelectFieldProps {
  fieldName: string;
  field: FieldDefinition;
  value: any;
  onFormChange: (fieldName: string, value: any) => void;
}

const MultiSelectField: React.FC<MultiSelectFieldProps> = ({
  fieldName,
  field,
  value,
  onFormChange
}) => {
  return (
    <div className="space-y-2">
      {field.options?.map((option) => (
        <div key={option.value} className="flex items-center space-x-2">
          <Checkbox
            id={`${fieldName}-${option.value}`}
            checked={(value || []).includes(option.value)}
            onCheckedChange={(checked) => {
              const currentValues = Array.isArray(value) ? value : [];
              const newValues = checked
                ? [...currentValues, option.value]
                : currentValues.filter((v: string) => v !== option.value);
              onFormChange(fieldName, newValues);
            }}
          />
          <Label htmlFor={`${fieldName}-${option.value}`} className="text-sm">
            {option.label}
          </Label>
        </div>
      ))}
    </div>
  );
};

export default MultiSelectField; 