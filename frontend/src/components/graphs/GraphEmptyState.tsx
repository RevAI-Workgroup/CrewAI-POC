import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface GraphEmptyStateProps {
  onCreateGraph: () => void;
  isCreating: boolean;
}

export function GraphEmptyState({ onCreateGraph, isCreating }: GraphEmptyStateProps) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-16">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-muted rounded-full flex items-center justify-center">
            <Plus className="h-8 w-8 text-muted-foreground" />
          </div>
          <div>
            <h3 className="text-lg font-medium">No graphs yet</h3>
            <p className="text-muted-foreground">
              Create your first graph to get started building AI crews
            </p>
          </div>
          <Button onClick={onCreateGraph} disabled={isCreating}>
            <Plus className="h-4 w-4 mr-2" />
            {isCreating ? 'Creating...' : 'Create First Graph'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
} 