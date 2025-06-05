import type { LoaderFunction } from 'react-router-dom';
import { fetchGraphs, fetchGraphById, fetchGraphsNodes } from '@/stores/graphStore';
import type { Graph, NodeDefinitions } from '@/types/graph.types';

export interface GraphsLoaderData {
  graphs: Graph[];
}

export interface GraphLoaderData {
  graph: Graph;
  nodeDefinitions: NodeDefinitions;
}

// Loader for the graphs list page
export const graphsLoader: LoaderFunction = async (): Promise<GraphsLoaderData> => {
  try {
    await fetchGraphs();
    // Return empty array as the actual data will be in the store
    // The component will get it from the store via useGraphStore
    return { graphs: [] };
  } catch (error) {
    console.error('Failed to load graphs:', error);
    throw new Response('Failed to load graphs', { status: 500 });
  }
};

// Loader for individual graph page
export const graphLoader: LoaderFunction = async ({ params }): Promise<GraphLoaderData> => {
  const { id } = params;

  if (!id) {
    throw new Response('Graph ID is required', { status: 400 });
  }

  try {
    const graphPromise = fetchGraphById(id);
    const nodeDefinitionsPromise = fetchGraphsNodes();
    
    const [graph, nodeDefinitions] = await Promise.all([graphPromise, nodeDefinitionsPromise]);
    return { graph, nodeDefinitions };
  } catch (error) {
    console.error('Failed to load graph:', error);
    throw new Response('Graph not found', { status: 404 });
  }
};
