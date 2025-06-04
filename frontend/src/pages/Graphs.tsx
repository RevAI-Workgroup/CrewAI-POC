import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGraphStore } from '@/stores';
import { GraphsHeader, GraphGrid, GraphErrorState } from '@/components/graphs';
import type { Graph } from '@/types/graph.types';

export function GraphsPage() {
  const navigate = useNavigate();
  const {
    graphs,
    isLoading,
    isCreating,
    error,
    createGraph,
    deleteGraph,
    duplicateGraph,
    clearError,
  } = useGraphStore();

  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleCreateGraph = async () => {
    try {
      const newGraph = await createGraph();
      navigate(`/graphs/${newGraph.id}`);
    } catch (error) {
      console.error('Failed to create graph:', error);
    }
  };

  const handleDeleteGraph = async (id: string) => {
    try {
      setDeletingId(id);
      await deleteGraph(id);
    } catch (error) {
      console.error('Failed to delete graph:', error);
    } finally {
      setDeletingId(null);
    }
  };

  const handleDuplicateGraph = async (id: string) => {
    try {
      await duplicateGraph(id);
    } catch (error) {
      console.error('Failed to duplicate graph:', error);
    }
  };

  const handleEditGraph = (graph: Graph) => {
    navigate(`/graphs/${graph.id}`);
  };

  const handleRetry = () => {
    clearError();
    window.location.reload();
  };

  if (error) {
    return (
      <GraphErrorState
        error={error}
        onCreateGraph={handleCreateGraph}
        onRetry={handleRetry}
        isCreating={isCreating}
      />
    );
  }

  return (
    <div className="space-y-6">
      <GraphsHeader onCreateGraph={handleCreateGraph} isCreating={isCreating} />
      
      <GraphGrid
        graphs={graphs.data}
        isLoading={isLoading}
        isCreating={isCreating}
        deletingId={deletingId}
        onEdit={handleEditGraph}
        onDelete={handleDeleteGraph}
        onDuplicate={handleDuplicateGraph}
        onCreateGraph={handleCreateGraph}
      />
    </div>
  );
}
