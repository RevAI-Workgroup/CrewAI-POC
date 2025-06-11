import { useReducer, useCallback, useMemo } from 'react';
import type { Node, Edge } from '@xyflow/react';

// Graph Action Types
type GraphAction = 
  | { type: 'SET_NODES'; payload: Node[] }
  | { type: 'SET_EDGES'; payload: Edge[] }
  | { type: 'ADD_NODE'; payload: Node }
  | { type: 'ADD_EDGE'; payload: Edge }
  | { type: 'UPDATE_NODE'; payload: { id: string; data: any } }
  | { type: 'UPDATE_NODE_POSITION'; payload: { id: string; position: { x: number; y: number } } }
  | { type: 'DELETE_NODES'; payload: string[] }
  | { type: 'DELETE_EDGES'; payload: string[] }
  | { type: 'LOAD_GRAPH'; payload: { nodes: Node[]; edges: Edge[] } }
  | { type: 'BATCH_UPDATE'; payload: { nodes?: Node[]; edges?: Edge[] } }
  | { type: 'RESET_GRAPH' };

// Graph State Interface
interface GraphState {
  nodes: Node[];
  edges: Edge[];
  lastModified: Date;
  changeCount: number;
  isInitialized: boolean;
}

// Initial State
const initialState: GraphState = {
  nodes: [],
  edges: [],
  lastModified: new Date(),
  changeCount: 0,
  isInitialized: false
};

// State Reducer
function graphReducer(state: GraphState, action: GraphAction): GraphState {
  const baseUpdate = {
    lastModified: new Date(),
    changeCount: state.changeCount + 1
  };

  switch (action.type) {
    case 'SET_NODES':
      return { 
        ...state,
        ...baseUpdate,
        nodes: action.payload
      };

    case 'SET_EDGES':
      return { 
        ...state,
        ...baseUpdate,
        edges: action.payload
      };

    case 'ADD_NODE':
      return {
        ...state,
        ...baseUpdate,
        nodes: [...state.nodes, action.payload]
      };

    case 'ADD_EDGE':
      return {
        ...state,
        ...baseUpdate,
        edges: [...state.edges, action.payload]
      };

    case 'UPDATE_NODE':
      return {
        ...state,
        ...baseUpdate,
        nodes: state.nodes.map(node => 
          node.id === action.payload.id 
            ? { ...node, data: { ...node.data, ...action.payload.data } }
            : node
        )
      };

    case 'UPDATE_NODE_POSITION':
      return {
        ...state,
        ...baseUpdate,
        nodes: state.nodes.map(node => 
          node.id === action.payload.id 
            ? { ...node, position: action.payload.position }
            : node
        )
      };

    case 'DELETE_NODES':
      return {
        ...state,
        ...baseUpdate,
        nodes: state.nodes.filter(node => !action.payload.includes(node.id)),
        edges: state.edges.filter(edge => 
          !action.payload.includes(edge.source) && !action.payload.includes(edge.target)
        )
      };

    case 'DELETE_EDGES':
      return {
        ...state,
        ...baseUpdate,
        edges: state.edges.filter(edge => !action.payload.includes(edge.id))
      };

    case 'LOAD_GRAPH':
      return {
        ...state,
        nodes: action.payload.nodes,
        edges: action.payload.edges,
        lastModified: new Date(),
        changeCount: 0, // Reset change count on load
        isInitialized: true
      };

    case 'BATCH_UPDATE':
      return {
        ...state,
        ...baseUpdate,
        ...(action.payload.nodes && { nodes: action.payload.nodes }),
        ...(action.payload.edges && { edges: action.payload.edges })
      };

    case 'RESET_GRAPH':
      return {
        ...initialState,
        lastModified: new Date()
      };

    default:
      return state;
  }
}

// Graph State Hook
export function useGraphState() {
  const [state, dispatch] = useReducer(graphReducer, initialState);
  
  // Memoized action creators
  const actions = useMemo(() => ({
    // Node Actions
    setNodes: (nodes: Node[]) => dispatch({ type: 'SET_NODES', payload: nodes }),
    addNode: (node: Node) => dispatch({ type: 'ADD_NODE', payload: node }),
    updateNode: (id: string, data: any) => dispatch({ type: 'UPDATE_NODE', payload: { id, data } }),
    updateNodePosition: (id: string, position: { x: number; y: number }) => 
      dispatch({ type: 'UPDATE_NODE_POSITION', payload: { id, position } }),
    deleteNodes: (nodeIds: string[]) => dispatch({ type: 'DELETE_NODES', payload: nodeIds }),
    
    // Edge Actions
    setEdges: (edges: Edge[]) => dispatch({ type: 'SET_EDGES', payload: edges }),
    addEdge: (edge: Edge) => dispatch({ type: 'ADD_EDGE', payload: edge }),
    deleteEdges: (edgeIds: string[]) => dispatch({ type: 'DELETE_EDGES', payload: edgeIds }),
    
    // Graph Actions
    loadGraph: (nodes: Node[], edges: Edge[]) => 
      dispatch({ type: 'LOAD_GRAPH', payload: { nodes, edges } }),
    batchUpdate: (updates: { nodes?: Node[]; edges?: Edge[] }) => 
      dispatch({ type: 'BATCH_UPDATE', payload: updates }),
    resetGraph: () => dispatch({ type: 'RESET_GRAPH' })
  }), []);

  // Computed state
  const computed = useMemo(() => ({
    isEmpty: state.nodes.length === 0 && state.edges.length === 0,
    nodeCount: state.nodes.length,
    edgeCount: state.edges.length,
    hasChanges: state.changeCount > 0,
    isModified: state.changeCount > 0 && state.isInitialized
  }), [state.nodes.length, state.edges.length, state.changeCount, state.isInitialized]);

  return {
    // State
    state,
    computed,
    
    // Actions
    actions,
    
    // Utilities
    getState: () => state,
    getNodeById: useCallback((id: string) => state.nodes.find(n => n.id === id), [state.nodes]),
    getEdgeById: useCallback((id: string) => state.edges.find(e => e.id === id), [state.edges])
  };
}

// Export types for external use
export type { GraphAction, GraphState }; 