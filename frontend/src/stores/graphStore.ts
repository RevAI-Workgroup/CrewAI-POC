import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import apiClient from '@/services/api';
import { API_ROUTES } from '@/config/api';
import type { Graph, NodeDefinitions } from '@/types/graph.types';


interface FetchGraphsResponse {
  success:boolean
  count: number
  data: Graph[]
}

interface GetGraphResponse {
  data: Graph
  success: boolean
}

interface GetNodesDefinitionsResponse {
  success: boolean
  data: NodeDefinitions
}

interface CreateGraphResponse {
  success:boolean
  message: string
  data: Graph
}

interface GraphStoreState {
  // State
  graphs: FetchGraphsResponse;
  nodeDef: NodeDefinitions;
  selectedGraph: Graph | null;
  
  // Loading states
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  
  // Error handling
  error: string | null;

  // Actions
  fetchGraphs: () => Promise<void>;
  fetchGraphsNodes: () => Promise<NodeDefinitions>
  fetchGraphById: (id: string) => Promise<Graph>;
  createGraph: () => Promise<Graph>;
  updateGraph: (id: string, data: Partial<Graph>) => Promise<void>;
  deleteGraph: (id: string) => Promise<void>;
  duplicateGraph: (id: string) => Promise<Graph>;
  
  // Selection
  setSelectedGraph: (graph: Graph | null) => void;
  getGraphById: (id: string) => Graph | undefined;
  
  // Utilities
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

const useGraphStore = create<GraphStoreState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    graphs: {
      count: 0,
      data: [],
      success: true,
    },
    nodeDef: {
      categories: [],
      node_types: {},
      connection_constraints: {},
      enums: {
        process_types: [],
        output_formats: [],
        llm_providers: []
      }
    },
    selectedGraph: null,
    isLoading: false,
    isCreating: false,
    isUpdating: false,
    isDeleting: false,
    error: null,

    // Actions
    fetchGraphs: async (): Promise<void> => {
      set({ isLoading: true, error: null });
      
      try {
        const response = await apiClient.get<FetchGraphsResponse>(API_ROUTES.GRAPHS.LIST, {
          cache: {
            ttl: 1000 * 60 * 2
          }
        });

        set({
          graphs: response.data,
          isLoading: false,
          error: null,
        });
      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.detail || 
                           axiosError.response?.data?.message || 
                           'Failed to fetch graphs. Please try again.';
        
        set({
          error: errorMessage,
          isLoading: false,
        });
        
        throw new Error(errorMessage);
      }
    },

    fetchGraphsNodes: async (): Promise<NodeDefinitions> => {
      

      set({ isLoading: true, error: null });

      try {
        const response = await apiClient.get<GetNodesDefinitionsResponse>(API_ROUTES.NODES.DEFINITIONS, {
          cache: {
            ttl: 1000 * 60 * 15
          }
        });
        if(!response.data.success) {
          throw new Error("Error fetching nodes definitions");
        }

        const nodeDef = response.data.data;
        console.log("Node def", nodeDef)
        set({
          nodeDef,
          isLoading: false,
          error: null,
        });

        return nodeDef

      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.detail || 
                           axiosError.response?.data?.message || 
                           'Failed to fetch graph nodes. Please try again.';

        set({
          error: errorMessage,
          isLoading: false,
        });

        throw new Error(errorMessage);
      }
    },

    fetchGraphById: async (id: string): Promise<Graph> => {
      set({ isLoading: true, error: null });
      
      try {
        const response = await apiClient.get<GetGraphResponse>(API_ROUTES.GRAPHS.GET(id), {
          cache: false
        });
        const graph = response.data.data;

        // Update local store with the fetched graph if it's not already there
        set((state) => {
          const existingGraphIndex = state.graphs.data.findIndex(g => g.id === id);
          if (existingGraphIndex >= 0) {
            // Update existing graph
            const updatedGraphs = [...state.graphs.data];
            updatedGraphs[existingGraphIndex] = graph;
            return {
              graphs: {
                ...state.graphs,
                data: updatedGraphs,
              },
              isLoading: false,
              error: null,
            };
          } else {
            // Add new graph to store
            return {
              graphs: {
                ...state.graphs,
                data: [...state.graphs.data, graph],
              },
              isLoading: false,
              error: null,
            };
          }
        });

        return graph;
      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.detail || 
                           axiosError.response?.data?.message || 
                           'Failed to fetch graph. Please try again.';

        set({
          error: errorMessage,
          isLoading: false,
        });
        
        throw new Error(errorMessage);
      }
    },

    createGraph: async (): Promise<Graph> => {
      set({ isCreating: true, error: null });
      
      try {
        // Send POST request with empty body as requested
        const requestBody = {};
        const response = await apiClient.post<CreateGraphResponse>(API_ROUTES.GRAPHS.CREATE, requestBody, {
          cache: false
        });
        
        const newGraph = response.data;
        
        // Update local state
        set((state) => ({
          graphs: {
            ...state.graphs,
            data: [...state.graphs.data, newGraph.data],
          },
          isCreating: false,
          error: null,
        }));

        return newGraph.data;
      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.detail || 
                           axiosError.response?.data?.message || 
                           'Failed to create graph. Please try again.';
        
        set({
          error: errorMessage,
          isCreating: false,
        });
        
        throw new Error(errorMessage);
      }
    },

    updateGraph: async (id: string, data: Partial<Graph>): Promise<void> => {
      set({ isUpdating: true, error: null });
      
      try {
        const response = await apiClient.put<Graph>(API_ROUTES.GRAPHS.UPDATE(id), data);
        
        const updatedGraph = response.data;
        
        // Update local state
        set((state) => ({
          graphs: {
            ...state.graphs,
            data: state.graphs.data.map((graph) => 
              graph.id === id ? updatedGraph : graph
            ),
          },
          selectedGraph: state.selectedGraph?.id === id ? updatedGraph : state.selectedGraph,
          isUpdating: false,
          error: null,
        }));
      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.detail || 
                           axiosError.response?.data?.message || 
                           'Failed to update graph. Please try again.';
        
        set({
          error: errorMessage,
          isUpdating: false,
        });
        
        throw new Error(errorMessage);
      }
    },

    deleteGraph: async (id: string): Promise<void> => {
      set({ isDeleting: true, error: null });
      
      try {
        await apiClient.delete(API_ROUTES.GRAPHS.DELETE(id));
        
        // Update local state
        set((state) => ({
          graphs: {
            ...state.graphs,
            data: state.graphs.data.filter((graph) => graph.id !== id)
          },
          selectedGraph: state.selectedGraph?.id === id ? null : state.selectedGraph,
          isDeleting: false,
          error: null,
        }));
      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.detail || 
                           axiosError.response?.data?.message || 
                           'Failed to delete graph. Please try again.';
        
        set({
          error: errorMessage,
          isDeleting: false,
        });
        
        throw new Error(errorMessage);
      }
    },

    duplicateGraph: async (id: string): Promise<Graph> => {
      set({ isCreating: true, error: null });
      
      try {
        const response = await apiClient.post<Graph>(API_ROUTES.GRAPHS.DUPLICATE(id));
        
        const duplicatedGraph = response.data;
        
        // Update local state
        set((state) => ({
          graphs: {
            ...state.graphs,
            data: [...state.graphs.data, duplicatedGraph],
          },
          isCreating: false,
          error: null,
        }));

        return duplicatedGraph;
      } catch (error: unknown) {
        const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.detail ||
                           axiosError.response?.data?.message ||
                           'Failed to duplicate graph. Please try again.';
        
        set({
          error: errorMessage,
          isCreating: false,
        });
        
        throw new Error(errorMessage);
      }
    },

    // Selection methods
    setSelectedGraph: (graph: Graph | null) => {
      set({ selectedGraph: graph });
    },

    getGraphById: (id: string): Graph | undefined => {
      return get().graphs.data.find((graph) => graph.id === id);
    },

    // Utility methods
    clearError: () => {
      set({ error: null });
    },

    setLoading: (loading: boolean) => {
      set({ isLoading: loading });
    },
  }))
);

export default useGraphStore;

// Export individual action functions for convenience
export const fetchGraphs = () => useGraphStore.getState().fetchGraphs();
export const fetchGraphById = (id: string) => useGraphStore.getState().fetchGraphById(id);
export const createGraph = () => useGraphStore.getState().createGraph();
export const updateGraph = (id: string, data: Partial<Graph>) => 
  useGraphStore.getState().updateGraph(id, data);
export const deleteGraph = (id: string) => useGraphStore.getState().deleteGraph(id);
export const duplicateGraph = (id: string) => useGraphStore.getState().duplicateGraph(id);
export const setSelectedGraph = (graph: Graph | null) => 
  useGraphStore.getState().setSelectedGraph(graph);
export const getGraphById = (id: string) => useGraphStore.getState().getGraphById(id);
export const clearGraphError = () => useGraphStore.getState().clearError(); 
export const fetchGraphsNodes = () => useGraphStore.getState().fetchGraphsNodes();