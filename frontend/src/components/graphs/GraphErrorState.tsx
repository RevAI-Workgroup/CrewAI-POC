import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface GraphErrorStateProps {
  error: string;
  onCreateGraph: () => void;
  onRetry: () => void;
  isCreating: boolean;
}

export function GraphErrorState({ error, onCreateGraph, onRetry, isCreating }: GraphErrorStateProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">My Graphs</h1>
        <Button onClick={onCreateGraph} disabled={isCreating}>
          <Plus className="h-4 w-4 mr-2" />
          {isCreating ? 'Creating...' : 'New Graph'}
        </Button>
      </div>
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Error: {error}</p>
          <Button 
            variant="outline" 
            onClick={onRetry}
            className="mt-4"
          >
            Try Again
          </Button>
        </CardContent>
      </Card>
    </div>
  );
} 