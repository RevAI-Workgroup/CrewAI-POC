import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface GraphsHeaderProps {
  onCreateGraph: () => void;
  isCreating: boolean;
}

export function GraphsHeader({ onCreateGraph, isCreating }: GraphsHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <h1 className="text-3xl font-bold">My Graphs</h1>
      <Button onClick={onCreateGraph} disabled={isCreating}>
        <Plus className="h-4 w-4 mr-2" />
        {isCreating ? 'Creating...' : 'New Graph'}
      </Button>
    </div>
  );
} 