import React, { createContext, useContext, useEffect, useCallback, useMemo } from 'react';
import type { ReactNode } from 'react';
import { useReactFlow, useNodes, useEdges } from '@xyflow/react';
import { v4 as uuidv4 } from 'uuid';
import { toast } from 'sonner';

interface KeyboardShortcut {
  key: string;
  description: string;
  action: () => void;
}

interface KeyboardShortcutsContextType {
  shortcuts: KeyboardShortcut[];
  showShortcuts: boolean;
  setShowShortcuts: (show: boolean) => void;
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextType | undefined>(undefined);

interface KeyboardShortcutsProviderProps {
  children: ReactNode;
}

export const KeyboardShortcutsProvider = ({ children }: KeyboardShortcutsProviderProps) => {
  const [showShortcuts, setShowShortcuts] = React.useState(false);
  const {
    setNodes,
    setEdges,
    deleteElements,
    fitView,
    zoomIn,
    zoomOut,
    setCenter
  } = useReactFlow();
  const nodes = useNodes();
  const edges = useEdges();
  
  // Import history hooks for undo/redo
  const historyStore = React.useMemo(() => {
    try {
      return require('@/stores/historyStore').default();
    } catch {
      return null;
    }
  }, []);

  // Memoize selected nodes and edges to prevent infinite re-renders
  const selectedNodes = useMemo(() => nodes.filter(node => node.selected), [nodes]);
  const selectedEdges = useMemo(() => edges.filter(edge => edge.selected), [edges]);

  // Copy selected nodes to clipboard
  const copySelection = useCallback(() => {
    if (selectedNodes.length === 0) {
      toast.info('No nodes selected to copy');
      return;
    }

    const clipboardData = {
      nodes: selectedNodes.map(node => ({
        ...node,
        selected: false, // Don't copy selection state
      })),
      edges: edges.filter(edge => 
        selectedNodes.some(node => node.id === edge.source) &&
        selectedNodes.some(node => node.id === edge.target)
      ).map(edge => ({
        ...edge,
        selected: false,
      }))
    };

    localStorage.setItem('reactflow-clipboard', JSON.stringify(clipboardData));
    toast.success(`Copied ${selectedNodes.length} node(s)`);
  }, [selectedNodes, edges]);

  // Paste nodes from clipboard
  const pasteSelection = useCallback(() => {
    const clipboardData = localStorage.getItem('reactflow-clipboard');
    if (!clipboardData) {
      toast.info('Nothing to paste');
      return;
    }

    try {
      const { nodes: clipboardNodes, edges: clipboardEdges } = JSON.parse(clipboardData);
      
      if (!clipboardNodes || clipboardNodes.length === 0) {
        toast.info('Nothing to paste');
        return;
      }

      // Create new IDs for pasted nodes and update edges
      const nodeIdMap = new Map();
      const newNodes = clipboardNodes.map((node: any) => {
        const newId = uuidv4();
        nodeIdMap.set(node.id, newId);
        return {
          ...node,
          id: newId,
          position: {
            x: node.position.x + 50,
            y: node.position.y + 50,
          },
          selected: true, // Select pasted nodes
        };
      });

      const newEdges = clipboardEdges.map((edge: any) => ({
        ...edge,
        id: uuidv4(),
        source: nodeIdMap.get(edge.source),
        target: nodeIdMap.get(edge.target),
      })).filter((edge: any) => edge.source && edge.target);

      // Deselect existing nodes
      setNodes(nodes => nodes.map(node => ({ ...node, selected: false })));

      // Add new nodes and edges
      setNodes(nodes => [...nodes, ...newNodes]);
      setEdges(edges => [...edges, ...newEdges]);

      toast.success(`Pasted ${newNodes.length} node(s)`);
    } catch (error: unknown) {
      console.error(error);
      toast.error('Failed to paste');
    }
  }, [setNodes, setEdges]);

  // Delete selected elements
  const deleteSelection = useCallback(() => {
    if (selectedNodes.length === 0 && selectedEdges.length === 0) {
      toast.info('Nothing selected to delete');
      return;
    }

    deleteElements({ 
      nodes: selectedNodes.map(node => ({ id: node.id })),
      edges: selectedEdges.map(edge => ({ id: edge.id }))
    });

    // Clean up localStorage for deleted nodes
    selectedNodes.forEach(node => {
      const storageKey = `node_${node.id}_data`;
      localStorage.removeItem(storageKey);
    });

    toast.success(`Deleted ${selectedNodes.length} node(s) and ${selectedEdges.length} edge(s)`);
  }, [selectedNodes, selectedEdges, deleteElements]);

  // Select all nodes
  const selectAll = useCallback(() => {
    setNodes(nodes => nodes.map(node => ({ ...node, selected: true })));
    toast.info(`Selected ${nodes.length} node(s)`);
  }, [setNodes, nodes.length]);

  // Deselect all
  const deselectAll = useCallback(() => {
    setNodes(nodes => nodes.map(node => ({ ...node, selected: false })));
    setEdges(edges => edges.map(edge => ({ ...edge, selected: false })));
  }, [setNodes, setEdges]);

  // Duplicate selected nodes
  const duplicateSelection = useCallback(() => {
    copySelection();
    setTimeout(pasteSelection, 100); // Small delay to ensure copy completes
  }, [copySelection, pasteSelection]);

  // Fit view to all nodes
  const fitToView = useCallback(() => {
    fitView({ padding: 0.2 });
    toast.info('Fit to view');
  }, [fitView]);

  // Center view
  const centerView = useCallback(() => {
    if (nodes.length === 0) return;
    
    const centerX = nodes.reduce((sum, node) => sum + node.position.x, 0) / nodes.length;
    const centerY = nodes.reduce((sum, node) => sum + node.position.y, 0) / nodes.length;
    
    setCenter(centerX, centerY, { zoom: 1 });
    toast.info('Centered view');
  }, [nodes, setCenter]);

  // Memoize shortcuts array to prevent recreation
  const shortcuts: KeyboardShortcut[] = useMemo(() => [
    {
      key: 'Ctrl+C',
      description: 'Copy selected nodes',
      action: copySelection,
    },
    {
      key: 'Ctrl+V',
      description: 'Paste copied nodes',
      action: pasteSelection,
    },
    {
      key: 'Ctrl+D',
      description: 'Duplicate selected nodes',
      action: duplicateSelection,
    },
    {
      key: 'Delete',
      description: 'Delete selected elements',
      action: deleteSelection,
    },
    {
      key: 'Ctrl+A',
      description: 'Select all nodes',
      action: selectAll,
    },
    {
      key: 'Escape',
      description: 'Deselect all',
      action: deselectAll,
    },
    {
      key: 'F',
      description: 'Fit view to all nodes',
      action: fitToView,
    },
    {
      key: 'Ctrl+0',
      description: 'Center view',
      action: centerView,
    },
    {
      key: 'Ctrl+=',
      description: 'Zoom in',
      action: zoomIn,
    },
    {
      key: 'Ctrl+-',
      description: 'Zoom out',
      action: zoomOut,
    },
    {
      key: 'Ctrl+?',
      description: 'Show keyboard shortcuts',
      action: () => setShowShortcuts(true),
    },
  ], [
    copySelection,
    pasteSelection,
    duplicateSelection,
    deleteSelection,
    selectAll,
    deselectAll,
    fitToView,
    centerView,
    zoomIn,
    zoomOut,
  ]);

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts if typing in an input
      if (event.target instanceof HTMLInputElement || 
          event.target instanceof HTMLTextAreaElement ||
          event.target instanceof HTMLSelectElement) {
        return;
      }

      const { key, ctrlKey, metaKey, shiftKey } = event;
      const modKey = ctrlKey || metaKey;

      // Match shortcuts
      if (modKey && key === 'c') {
        event.preventDefault();
        copySelection();
      } else if (modKey && key === 'v') {
        event.preventDefault();
        pasteSelection();
      } else if (modKey && key === 'd') {
        event.preventDefault();
        duplicateSelection();
      } else if (key === 'Delete' || key === 'Backspace') {
        event.preventDefault();
        deleteSelection();
      } else if (modKey && key === 'a') {
        event.preventDefault();
        selectAll();
      } else if (key === 'Escape') {
        event.preventDefault();
        deselectAll();
      } else if (key === 'f' && !modKey) {
        event.preventDefault();
        fitToView();
      } else if (modKey && key === '0') {
        event.preventDefault();
        centerView();
      } else if (modKey && (key === '=' || key === '+')) {
        event.preventDefault();
        zoomIn();
      } else if (modKey && key === '-') {
        event.preventDefault();
        zoomOut();
      } else if (modKey && shiftKey && key === '?') {
        event.preventDefault();
        setShowShortcuts(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [
    copySelection,
    pasteSelection,
    duplicateSelection,
    deleteSelection,
    selectAll,
    deselectAll,
    fitToView,
    centerView,
    zoomIn,
    zoomOut,
  ]);

  const value: KeyboardShortcutsContextType = useMemo(() => ({
    shortcuts,
    showShortcuts,
    setShowShortcuts,
  }), [shortcuts, showShortcuts]);

  return (
    <KeyboardShortcutsContext.Provider value={value}>
      {children}
    </KeyboardShortcutsContext.Provider>
  );
};

export const useKeyboardShortcuts = (): KeyboardShortcutsContextType => {
  const context = useContext(KeyboardShortcutsContext);
  if (context === undefined) {
    throw new Error('useKeyboardShortcuts must be used within a KeyboardShortcutsProvider');
  }
  return context;
}; 