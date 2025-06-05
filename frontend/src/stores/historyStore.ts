import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type { Node, Edge } from '@xyflow/react';
import type { HistoryState, HistoryOperation, HistoryStore } from '@/types/history.types';

const MAX_HISTORY_SIZE = 20;

const useHistoryStore = create<HistoryStore>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    history: [],
    currentIndex: -1,
    maxHistorySize: MAX_HISTORY_SIZE,
    
    // Computed getters
    get canUndo() {
      const state = get();
      return state.currentIndex > 0;
    },
    
    get canRedo() {
      const state = get();
      return state.currentIndex < state.history.length - 1;
    },
    
    // Actions
    pushState: (nodes: Node[], edges: Edge[], operation: HistoryOperation, description?: string) => {
      set((state) => {
        const newState: HistoryState = {
          nodes: JSON.parse(JSON.stringify(nodes)), // Deep clone
          edges: JSON.parse(JSON.stringify(edges)), // Deep clone
          timestamp: Date.now(),
          operation,
          description
        };
        
        let newHistory = [...state.history];
        let newIndex = state.currentIndex;
        
        // If we're not at the end of history, remove everything after current index
        if (newIndex < newHistory.length - 1) {
          newHistory = newHistory.slice(0, newIndex + 1);
        }
        
        // Add new state
        newHistory.push(newState);
        newIndex = newHistory.length - 1;
        
        // Enforce max history size (circular buffer behavior)
        if (newHistory.length > MAX_HISTORY_SIZE) {
          newHistory = newHistory.slice(-MAX_HISTORY_SIZE);
          newIndex = newHistory.length - 1;
        }
        
        return {
          ...state,
          history: newHistory,
          currentIndex: newIndex
        };
      });
    },
    
    undo: () => {
      const state = get();
      if (!state.canUndo) return null;
      
      const newIndex = state.currentIndex - 1;
      const previousState = state.history[newIndex];
      
      set((state) => ({
        ...state,
        currentIndex: newIndex
      }));
      
      return previousState;
    },
    
    redo: () => {
      const state = get();
      if (!state.canRedo) return null;
      
      const newIndex = state.currentIndex + 1;
      const nextState = state.history[newIndex];
      
      set((state) => ({
        ...state,
        currentIndex: newIndex
      }));
      
      return nextState;
    },
    
    clear: () => {
      set((state) => ({
        ...state,
        history: [],
        currentIndex: -1
      }));
    },
    
    getCurrentState: () => {
      const state = get();
      if (state.currentIndex >= 0 && state.currentIndex < state.history.length) {
        return state.history[state.currentIndex];
      }
      return null;
    },
    
    getPreviousOperation: () => {
      const state = get();
      if (state.currentIndex > 0) {
        return state.history[state.currentIndex - 1].operation;
      }
      return null;
    }
  }))
);

export default useHistoryStore;

// Export individual action functions for convenience
export const pushHistoryState = (nodes: Node[], edges: Edge[], operation: HistoryOperation, description?: string) => 
  useHistoryStore.getState().pushState(nodes, edges, operation, description);

export const undoHistory = () => useHistoryStore.getState().undo();
export const redoHistory = () => useHistoryStore.getState().redo();
export const clearHistory = () => useHistoryStore.getState().clear();
export const getCurrentHistoryState = () => useHistoryStore.getState().getCurrentState();
export const canUndoHistory = () => useHistoryStore.getState().canUndo;
export const canRedoHistory = () => useHistoryStore.getState().canRedo; 