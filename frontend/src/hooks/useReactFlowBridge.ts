import { useCallback, useMemo } from 'react';
import type { 
  Node, 
  Edge, 
  OnNodesChange, 
  OnEdgesChange, 
  OnConnect,
  Connection,
  NodeChange,
  EdgeChange
} from '@xyflow/react';
import type { GraphState } from './useGraphState';

interface GraphActions {
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (node: Node) => void;
  addEdge: (edge: Edge) => void;
  updateNode: (id: string, data: any) => void;
  updateNodePosition: (id: string, position: { x: number; y: number }) => void;
  deleteNodes: (nodeIds: string[]) => void;
  deleteEdges: (edgeIds: string[]) => void;
  batchUpdate: (updates: { nodes?: Node[]; edges?: Edge[] }) => void;
}

interface UseReactFlowBridgeOptions {
  isValidConnection?: (connection: Connection) => boolean;
  createEdgeFromConnection?: (connection: Connection) => Edge;
}

/**
 * ReactFlow Integration Bridge Hook
 * 
 * This hook bridges ReactFlow events with the unified graph state management.
 * It converts ReactFlow change events into graph state actions, providing
 * a clean separation between ReactFlow's event system and our state management.
 * 
 * Benefits:
 * - Centralizes ReactFlow event handling
 * - Converts ReactFlow changes to structured actions
 * - Maintains type safety between ReactFlow and our state
 * - Provides consistent edge creation logic
 * - Enables easy testing of ReactFlow integration
 */
export function useReactFlowBridge(
  graphState: GraphState, 
  actions: GraphActions,
  options: UseReactFlowBridgeOptions = {}
) {
  const { 
    isValidConnection,
    createEdgeFromConnection = defaultCreateEdge
  } = options;

  // Convert graph state to ReactFlow state
  const reactFlowNodes = useMemo(() => graphState.nodes, [graphState.nodes]);
  const reactFlowEdges = useMemo(() => graphState.edges, [graphState.edges]);

  // ReactFlow nodes change handler
  const onNodesChange: OnNodesChange = useCallback((changes: NodeChange[]) => {
    console.debug('🔄 ReactFlow nodes change:', changes);

    // Group changes by type for efficient processing
    const changesByType = {
      position: [] as { id: string; position: { x: number; y: number } }[],
      remove: [] as string[],
      select: [] as string[],
      replace: [] as { id: string; item: Node }[]
    };

    changes.forEach(change => {
      switch (change.type) {
        case 'position':
          if (change.position) {
            changesByType.position.push({
              id: change.id,
              position: change.position
            });
          }
          break;
        
        case 'remove':
          changesByType.remove.push(change.id);
          break;
        
        case 'select':
          changesByType.select.push(change.id);
          // Note: Selection state is handled by ReactFlow, not our state
          break;
        
        case 'replace':
          if (change.item) {
            changesByType.replace.push({
              id: change.id,
              item: change.item as Node
            });
          }
          break;
      }
    });

    // Apply changes to state
    if (changesByType.position.length > 0) {
      // Batch position updates for performance
      changesByType.position.forEach(({ id, position }) => {
        actions.updateNodePosition(id, position);
      });
    }

    if (changesByType.remove.length > 0) {
      actions.deleteNodes(changesByType.remove);
    }

    if (changesByType.replace.length > 0) {
      // Handle node data updates
      changesByType.replace.forEach(({ id, item }) => {
        actions.updateNode(id, item.data);
      });
    }

    // Selection changes are handled by ReactFlow internally
    // We don't need to sync selection state to backend
    
  }, [actions]);

  // ReactFlow edges change handler
  const onEdgesChange: OnEdgesChange = useCallback((changes: EdgeChange[]) => {
    console.debug('🔄 ReactFlow edges change:', changes);

    // Group changes by type
    const changesByType = {
      remove: [] as string[],
      select: [] as string[],
      replace: [] as { id: string; item: Edge }[]
    };

    changes.forEach(change => {
      switch (change.type) {
        case 'remove':
          changesByType.remove.push(change.id);
          break;
        
        case 'select':
          changesByType.select.push(change.id);
          // Selection handled by ReactFlow
          break;
        
        case 'replace':
          if (change.item) {
            changesByType.replace.push({
              id: change.id,
              item: change.item as Edge
            });
          }
          break;
      }
    });

    // Apply changes to state
    if (changesByType.remove.length > 0) {
      actions.deleteEdges(changesByType.remove);
    }

    if (changesByType.replace.length > 0) {
      // Handle edge updates (rare, but possible)
      const updatedEdges = graphState.edges.map(edge => {
        const replacement = changesByType.replace.find(r => r.id === edge.id);
        return replacement ? replacement.item : edge;
      });
      actions.setEdges(updatedEdges);
    }

  }, [actions, graphState.edges]);

  // ReactFlow connection handler
  const onConnect: OnConnect = useCallback((connection: Connection) => {
    console.debug('🔗 ReactFlow connection:', connection);

    // Validate connection if validator provided
    if (isValidConnection && !isValidConnection(connection)) {
      console.debug('❌ Connection validation failed:', connection);
      return;
    }

    console.debug('✅ Connection validated, creating edge');

    // Create edge from connection
    const newEdge = createEdgeFromConnection(connection);
    
    // Add edge to state
    actions.addEdge(newEdge);

    console.debug('🔗 Edge added to state:', newEdge);
  }, [actions, isValidConnection, createEdgeFromConnection]);

  // Utility functions for common operations
  const bridgeUtils = useMemo(() => ({
    // Add node with position
    addNodeAtPosition: (nodeType: string, position: { x: number; y: number }, data: any = {}) => {
      const newNode: Node = {
        id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: nodeType,
        position,
        data: {
          label: nodeType,
          type: nodeType,
          ...data
        }
      };
      actions.addNode(newNode);
      return newNode;
    },

    // Connect two nodes
    connectNodes: (sourceId: string, targetId: string, sourceHandle?: string, targetHandle?: string) => {
      const connection: Connection = {
        source: sourceId,
        target: targetId,
        sourceHandle: sourceHandle || null,
        targetHandle: targetHandle || null
      };
      
      if (isValidConnection && !isValidConnection(connection)) {
        console.warn('Cannot connect nodes: validation failed', connection);
        return null;
      }

      const edge = createEdgeFromConnection(connection);
      actions.addEdge(edge);
      return edge;
    },

    // Batch update nodes and edges
    batchUpdate: (nodes?: Node[], edges?: Edge[]) => {
      actions.batchUpdate({ nodes, edges });
    }
  }), [actions, isValidConnection, createEdgeFromConnection]);

  return {
    // ReactFlow props
    nodes: reactFlowNodes,
    edges: reactFlowEdges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    
    // Utility functions
    utils: bridgeUtils,
    
    // State information
    nodeCount: reactFlowNodes.length,
    edgeCount: reactFlowEdges.length,
    isEmpty: reactFlowNodes.length === 0 && reactFlowEdges.length === 0
  };
}

// Default edge creation function
function defaultCreateEdge(connection: Connection): Edge {
  const { source, target, sourceHandle, targetHandle } = connection;
  
  return {
    id: `edge-${source}${sourceHandle || 'output'}-${target}${targetHandle || 'input'}-${Date.now()}`,
    source: source!,
    target: target!,
    sourceHandle: sourceHandle || null,
    targetHandle: targetHandle || null,
    type: 'default',
    data: {}
  };
}

// Export types
export type { GraphActions, UseReactFlowBridgeOptions }; 