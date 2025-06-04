import type { Graph } from '@/types/graph.types';
import { GraphCard } from './GraphCard';
import { GraphLoadingSkeleton } from './GraphLoadingSkeleton';
import { GraphEmptyState } from './GraphEmptyState';

interface GraphGridProps {
  graphs: Graph[];
  isLoading: boolean;
  isCreating: boolean;
  deletingId: string | null;
  onEdit: (graph: Graph) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
  onCreateGraph: () => void;
}

export function GraphGrid({
  graphs,
  isLoading,
  isCreating,
  deletingId,
  onEdit,
  onDelete,
  onDuplicate,
  onCreateGraph,
}: GraphGridProps) {
  if (isLoading) {
    return <GraphLoadingSkeleton />;
  }

  if (graphs.length === 0) {
    return <GraphEmptyState onCreateGraph={onCreateGraph} isCreating={isCreating} />;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {graphs.map((graph) => (
        <GraphCard
          key={graph.id}
          graph={graph}
          onEdit={onEdit}
          onDelete={onDelete}
          onDuplicate={onDuplicate}
          isDeleting={deletingId === graph.id}
        />
      ))}
    </div>
  );
} 