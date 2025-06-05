import React from 'react';
import { Slider } from '@/components/ui/slider';
import type { FieldDefinition } from '@/types';

interface SliderFieldProps {
  fieldName: string;
  field: FieldDefinition;
  value: any;
  onFormChange: (fieldName: string, value: any) => void;
}

const SliderField: React.FC<SliderFieldProps> = ({
  fieldName,
  field,
  value,
  onFormChange
}) => {
  const minValue = field.validation?.min || 0;
  const maxValue = field.validation?.max || 100;
  const stepValue = field.validation?.step || 1;
  const currentValue = typeof value === 'number' ? value : minValue;

  return (
    <div className="space-y-2">
      <Slider
        value={[currentValue]}
        onValueChange={(values) => onFormChange(fieldName, values[0])}
        min={minValue}
        max={maxValue}
        step={stepValue}
        className="w-full"
      />
      <div className="text-xs text-muted-foreground text-center">
        {currentValue}
      </div>
    </div>
  );
};

export default SliderField; 