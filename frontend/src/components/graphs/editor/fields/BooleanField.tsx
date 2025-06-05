import React from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import type { FieldDefinition } from '@/types';

interface BooleanFieldProps {
  fieldName: string;
  field: FieldDefinition;
  value: any;
  onFormChange: (fieldName: string, value: any) => void;
}

const BooleanField: React.FC<BooleanFieldProps> = ({
  fieldName,
  field,
  value,
  onFormChange
}) => {
  return (
    <div className="flex items-center space-x-2">
      <Checkbox
        id={fieldName}
        checked={Boolean(value)}
        onCheckedChange={(checked) => onFormChange(fieldName, checked)}
      />
      <Label htmlFor={fieldName} className="text-sm">
        {field.label}
      </Label>
    </div>
  );
};

export default BooleanField; 