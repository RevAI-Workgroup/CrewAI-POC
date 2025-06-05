import React from 'react';
import { BaseEdge, getBezierPath, type EdgeProps } from '@xyflow/react';

const CustomEdge: React.FC<EdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  selected,
  style = {},
}) => {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      style={{
        ...style,
        stroke: selected ? 'var(--primary)' : 'var(--muted-foreground)',
        strokeWidth: selected ? 2 : 1,
      }}
    />
  );
};

export default CustomEdge; 