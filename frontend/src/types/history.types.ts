import type { Node, Edge } from '@xyflow/react';

export type HistoryOperation = 
  | 'create_node' 
  | 'delete_node' 
  | 'move_node' 
  | 'update_node' 
  | 'create_edge' 
  | 'delete_edge' 
  | 'batch'
  | 'initial';

export interface HistoryState {
  nodes: Node[];
  edges: Edge[];
  timestamp: number;
  operation: HistoryOperation;
  description?: string;
}

export interface HistoryStore {
  // State
  history: HistoryState[];
  currentIndex: number;
  maxHistorySize: number;
  
  // Computed
  canUndo: boolean;
  canRedo: boolean;
  
  // Actions
  pushState: (nodes: Node[], edges: Edge[], operation: HistoryOperation, description?: string) => void;
  undo: () => HistoryState | null;
  redo: () => HistoryState | null;
  clear: () => void;
  getCurrentState: () => HistoryState | null;
  getPreviousOperation: () => HistoryOperation | null;
} 