import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { subscribeWithSelector } from 'zustand/middleware';
import type { Node, Edge } from '@xyflow/react';
import type { HistoryState, HistoryOperation, HistoryStore } from '@/types/history.types';

const MAX_HISTORY_SIZE = 50; // Increased to 50 steps

// ✅ Enhanced store interface to support per-graph history with persistence
interface PersistedHistoryStore extends HistoryStore {
  // Per-graph history storage
  graphHistories: Record<string, {
    history: HistoryState[];
    currentIndex: number;
  }>;
  // Initialization guard
  isInitializing: boolean;
  // Helper method
  _updateComputedProperties: (state: any) => { canUndo: boolean; canRedo: boolean };
}

const useHistoryStore = create<PersistedHistoryStore>()(
  persist(
    subscribeWithSelector((set, get) => ({
      // Current active state (for the currently loaded graph)
      history: [],
      currentIndex: -1,
      maxHistorySize: MAX_HISTORY_SIZE,
      currentGraphId: null,
      canUndo: false,
      canRedo: false,
      
      // ✅ Initialization guard to prevent auto-saves during loading
      isInitializing: false,
      
      // ✅ NEW: Per-graph history storage (automatically persisted)
      graphHistories: {},
      
      // Helper to update computed properties
      _updateComputedProperties: (state: any) => {
        const canUndo = state.currentIndex > 0;
        const canRedo = state.currentIndex < state.history.length - 1;
        console.log('🔄 UPDATE COMPUTED:', { currentIndex: state.currentIndex, historyLength: state.history.length, canUndo, canRedo });
        return { canUndo, canRedo };
      },
      
      // Actions
      pushState: (nodes: Node[], edges: Edge[], operation: HistoryOperation, description?: string) => {
        set((state) => {
          // ✅ INITIALIZATION GUARD: Don't save during initialization unless it's the initial state
          if (state.isInitializing && operation !== 'initial') {
            console.log(`⚠️ INIT GUARD: Blocking ${operation} save during initialization`);
            return state;
          }
          
          // ✅ DEDUPLICATION: Don't add duplicate states for rapid updates
          if (state.history.length > 0) {
            const lastState = state.history[state.history.length - 1];
            const timeDiff = Date.now() - lastState.timestamp;
            
            // If last operation was same type within 2 seconds, skip this save
            if (lastState.operation === operation && timeDiff < 2000) {
              console.log(`⚠️ DEDUPE: Skipping duplicate ${operation} (${timeDiff}ms ago)`);
              return state;
            }
          }
          
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
            const removedCount = newHistory.length - (newIndex + 1);
            newHistory = newHistory.slice(0, newIndex + 1);
            console.log(`✂️ BRANCH HISTORY: Removed ${removedCount} future states (was at index ${newIndex} of ${state.history.length - 1})`);
          }
          
          // Add new state
          newHistory.push(newState);
          newIndex = newHistory.length - 1;
          console.log(`➕ ADD TO HISTORY: ${operation} (index ${newIndex}, total: ${newHistory.length})`);
          
          // Enforce max history size (keep only last 50 steps)
          if (newHistory.length > MAX_HISTORY_SIZE) {
            newHistory = newHistory.slice(-MAX_HISTORY_SIZE);
            newIndex = newHistory.length - 1;
          }
          
          const updatedState = {
            ...state,
            history: newHistory,
            currentIndex: newIndex
          };
          
          // ✅ Update computed properties
          const computedProps = state._updateComputedProperties(updatedState);
          Object.assign(updatedState, computedProps);
          
          // ✅ Auto-save to per-graph storage if we have a graphId
          if (state.currentGraphId) {
            updatedState.graphHistories = {
              ...state.graphHistories,
              [state.currentGraphId]: {
                history: newHistory,
                currentIndex: newIndex
              }
            };
          }
          
          return updatedState;
        });
      },
      
      undo: () => {
        const state = get();
        console.log('🔙 UNDO called:', { currentIndex: state.currentIndex, historyLength: state.history.length });
        
        // ✅ Check raw condition instead of potentially stale canUndo property
        if (state.currentIndex <= 0) {
          console.log('❌ Cannot undo - at beginning of history');
          return null;
        }
        
        if (!state.history[state.currentIndex - 1]) {
          console.log('❌ Cannot undo - previous state does not exist');
          return null;
        }
        
        const newIndex = state.currentIndex - 1;
        const previousState = state.history[newIndex];
        console.log('✅ Undoing to index:', newIndex, 'operation:', previousState.operation);
        
        set((state) => {
          const updatedState = {
            ...state,
            currentIndex: newIndex
          };
          
          // ✅ Update computed properties
          const computedProps = state._updateComputedProperties(updatedState);
          Object.assign(updatedState, computedProps);
          
          console.log('🔙 UNDO STATE UPDATE:', { 
            oldIndex: state.currentIndex, 
            newIndex, 
            newCanUndo: computedProps.canUndo, 
            newCanRedo: computedProps.canRedo 
          });
          
          // ✅ Update per-graph storage
          if (state.currentGraphId) {
            updatedState.graphHistories = {
              ...state.graphHistories,
              [state.currentGraphId]: {
                history: state.history,
                currentIndex: newIndex
              }
            };
          }
          
          return updatedState;
        });
        
        return previousState;
      },
      
      redo: () => {
        const state = get();
        console.log('🔜 REDO called:', { currentIndex: state.currentIndex, historyLength: state.history.length });
        // ✅ Check raw condition instead of potentially stale canRedo property
        if (state.currentIndex >= state.history.length - 1) {
          console.log('❌ Cannot redo - at end of history');
          return null;
        }
        
        const newIndex = state.currentIndex + 1;
        const nextState = state.history[newIndex];
        console.log('✅ Redoing to index:', newIndex);
        
        set((state) => {
          const updatedState = {
            ...state,
            currentIndex: newIndex
          };
          
          // ✅ Update computed properties
          const computedProps = state._updateComputedProperties(updatedState);
          Object.assign(updatedState, computedProps);
          
          // ✅ Update per-graph storage
          if (state.currentGraphId) {
            updatedState.graphHistories = {
              ...state.graphHistories,
              [state.currentGraphId]: {
                history: state.history,
                currentIndex: newIndex
              }
            };
          }
          
          return updatedState;
        });
        
        return nextState;
      },
      
      clear: () => {
        set((state) => {
          const clearedState = {
            ...state,
            history: [],
            currentIndex: -1
          };
          
          // ✅ Update computed properties
          const computedProps = state._updateComputedProperties(clearedState);
          Object.assign(clearedState, computedProps);
          
          return clearedState;
        });
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
      },
      
      // ✅ Simplified localStorage operations (now handled by persist middleware)
      loadHistory: (graphId: string) => {
        // Start initialization guard
        set((state) => ({ ...state, isInitializing: true }));
        
        set((state) => {
          // 🔍 DEBUG: Check what Zustand actually has vs localStorage
          console.log('🔍 ZUSTAND STATE graphHistories:', state.graphHistories);
          console.log('🔍 ZUSTAND graphHistories keys:', Object.keys(state.graphHistories));
          
          // Check localStorage directly and force manual load if persist failed
          const rawData = localStorage.getItem('graph-editor-history');
          if (rawData) {
            try {
              const parsed = JSON.parse(rawData);
              console.log('🔍 LOCALSTORAGE RAW:', parsed);
              const localStorageGraphHistories = parsed?.state?.graphHistories || parsed?.graphHistories;
              console.log('🔍 LOCALSTORAGE graphHistories:', localStorageGraphHistories);
              console.log('🔍 LOCALSTORAGE has target graph:', !!localStorageGraphHistories?.[graphId]);
              
              // 🚨 FORCE MANUAL LOAD if persist middleware failed
              if (Object.keys(state.graphHistories).length === 0 && localStorageGraphHistories && Object.keys(localStorageGraphHistories).length > 0) {
                console.log('🔧 MANUAL PERSIST LOAD: Zustand persist failed, loading manually');
                // Manually set the graphHistories from localStorage
                const newState = {
                  ...state,
                  graphHistories: localStorageGraphHistories
                };
                
                // Now try to load the specific graph
                const graphHistory = localStorageGraphHistories[graphId];
                if (graphHistory) {
                  console.log(`📥 MANUAL LOADING: ${graphHistory.history.length} history steps, canUndo: ${graphHistory.currentIndex > 0}`);
                  const loadedState = {
                    ...newState,
                    history: graphHistory.history,
                    currentIndex: graphHistory.currentIndex,
                    currentGraphId: graphId
                  };
                  
                  // ✅ Update computed properties
                  const computedProps = state._updateComputedProperties(loadedState);
                  Object.assign(loadedState, computedProps);
                  
                  return loadedState;
                }
                
                return newState;
              }
              
            } catch (e) {
              console.log('❌ Failed to parse localStorage:', e);
            }
          }
          
          const graphHistory = state.graphHistories[graphId];
          
          if (graphHistory) {
            console.debug(`📥 LOADING: ${graphHistory.history.length} history steps, canUndo: ${graphHistory.currentIndex > 0}`);
            const loadedState = {
              ...state,
              history: graphHistory.history,
              currentIndex: graphHistory.currentIndex,
              currentGraphId: graphId
            };
            
            // ✅ Update computed properties
            const computedProps = state._updateComputedProperties(loadedState);
            Object.assign(loadedState, computedProps);
            
            return loadedState;
          } else {
            console.debug(`❌ NO HISTORY FOUND for graph ${graphId}`);
            return {
              ...state,
              history: [],
              currentIndex: -1,
              currentGraphId: graphId
            };
          }
        });
      },
      
      saveHistory: () => {
        // ✅ No-op: persist middleware handles saving automatically
        console.debug('💾 History auto-saved by persist middleware');
      },
      
      endInitialization: () => {
        set((state) => {
          console.log('🏁 ENDING INITIALIZATION - auto-saves now enabled', { 
            currentHistoryLength: state.history.length,
            currentIndex: state.currentIndex
          });
          return { ...state, isInitializing: false };
        });
      },
      
      clearStoredHistory: (graphId: string) => {
        set((state) => {
          const newGraphHistories = { ...state.graphHistories };
          delete newGraphHistories[graphId];
          
          console.debug(`🗑️ History cleared for graph ${graphId}`);
          
          // If this is the current graph, also clear in-memory history
          if (state.currentGraphId === graphId) {
            return {
              ...state,
              graphHistories: newGraphHistories,
              history: [],
              currentIndex: -1
            };
          }
          
          return {
            ...state,
            graphHistories: newGraphHistories
          };
        });
      }
    })),
    {
      name: 'graph-editor-history', // Storage key name
      storage: createJSONStorage(() => localStorage),
      // ✅ Only persist the per-graph histories, not the current active state
      partialize: (state) => ({
        graphHistories: state.graphHistories
      }),
      // ✅ Custom merge function to handle loading persisted data
      merge: (persistedState: any, currentState) => {
        console.log('🔄 PERSIST MERGE called with:', { persistedState, currentState });
        const graphHistories = persistedState?.graphHistories || persistedState?.state?.graphHistories || {};
        console.log('🔄 MERGE extracting graphHistories:', graphHistories);
        return {
          ...currentState,
          graphHistories
        };
      }
    }
  )
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

// Simplified localStorage functions (now handled by persist middleware)
export const loadHistoryForGraph = (graphId: string) => useHistoryStore.getState().loadHistory(graphId);
export const saveHistoryToStorage = () => useHistoryStore.getState().saveHistory();
export const clearStoredHistoryForGraph = (graphId: string) => useHistoryStore.getState().clearStoredHistory(graphId); 