import React from 'react';
import { Button } from '@/components/ui/button';
import { Keyboard } from 'lucide-react';
import { useKeyboardShortcuts } from '@/contexts/KeyboardShortcutsProvider';

const ShortcutsButton: React.FC = () => {
  const { setShowShortcuts } = useKeyboardShortcuts();

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={() => setShowShortcuts(true)}
      className="absolute top-4 left-4 z-10 flex items-center gap-2"
    >
      <Keyboard className="w-4 h-4" />
      Shortcuts
    </Button>
  );
};

export default ShortcutsButton; 