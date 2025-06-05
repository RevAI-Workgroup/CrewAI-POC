import { useEffect } from 'react';

interface UseKeyboardShortcutsOptions {
  onUndo?: () => void;
  onRedo?: () => void;
  canUndo?: boolean;
  canRedo?: boolean;
}

export function useKeyboardShortcuts({
  onUndo,
  onRedo,
  canUndo = false,
  canRedo = false
}: UseKeyboardShortcutsOptions) {
  
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

      // Undo: Ctrl+Z
      if (modKey && key === 'z' && !shiftKey) {
        if (canUndo && onUndo) {
          event.preventDefault();
          onUndo();
        }
      }
      // Redo: Ctrl+Y or Ctrl+Shift+Z
      else if ((modKey && key === 'y') || (modKey && shiftKey && key === 'z')) {
        if (canRedo && onRedo) {
          event.preventDefault();
          onRedo();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onUndo, onRedo, canUndo, canRedo]);
} 