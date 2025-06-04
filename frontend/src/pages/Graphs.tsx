import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Trash2, Copy, Edit, Plus, MoreVertical } from 'lucide-react';
import { useGraphStore } from '@/stores';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { Graph } from '@/types/graph.types';

export function GraphsPage() {
  const navigate = useNavigate();
  const {
    graphs,
    isLoading,
    isCreating,
    error,
    fetchGraphs,
    createGraph,
    deleteGraph,
    duplicateGraph,
    clearError,
  } = useGraphStore();

  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    fetchGraphs();
  }, []);

  const handleCreateGraph = async () => {
    try {
      const newGraph = await createGraph();
      console.log("New graph", newGraph)

      //navigate(`/graphs/${newGraph.id}`);
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">My Graphs</h1>
          <Button onClick={handleCreateGraph} disabled={isCreating}>
            <Plus className="h-4 w-4 mr-2" />
            {isCreating ? 'Creating...' : 'New Graph'}
          </Button>
        </div>
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">Error: {error}</p>
            <Button 
              variant="outline" 
              onClick={() => {
                clearError();
                fetchGraphs();
              }}
              className="mt-4"
            >
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">My Graphs</h1>
        <Button onClick={handleCreateGraph} disabled={isCreating}>
          <Plus className="h-4 w-4 mr-2" />
          {isCreating ? 'Creating...' : 'New Graph'}
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-1/2 mb-2" />
                <Skeleton className="h-4 w-2/3" />
              </CardContent>
              <CardFooter>
                <Skeleton className="h-8 w-full" />
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : graphs.count === 0 ? (
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
              <Button onClick={handleCreateGraph} disabled={isCreating}>
                <Plus className="h-4 w-4 mr-2" />
                {isCreating ? 'Creating...' : 'Create First Graph'}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {graphs.data.map((graph) => (
            <Card key={graph.id} className="cursor-pointer hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-lg truncate">
                      {graph.name || 'Untitled Graph'}
                    </CardTitle>
                    {graph.description && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {graph.description}
                      </p>
                    )}
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleEditGraph(graph)}>
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => handleDuplicateGraph(graph.id)}>
                        <Copy className="h-4 w-4 mr-2" />
                        Duplicate
                      </DropdownMenuItem>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete Graph</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to delete "{graph.name || 'Untitled Graph'}"? 
                              This action cannot be undone.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteGraph(graph.id)}
                              disabled={deletingId === graph.id}
                              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                              {deletingId === graph.id ? 'Deleting...' : 'Delete'}
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex justify-between">
                    <span>Nodes:</span>
                    <span>{graph.nodes?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Connections:</span>
                    <span>{graph.edges?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Updated:</span>
                    <span>{formatDate(graph.updated_at)}</span>
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button 
                  variant="outline" 
                  className="w-full" 
                  onClick={() => handleEditGraph(graph)}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Open Graph
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
