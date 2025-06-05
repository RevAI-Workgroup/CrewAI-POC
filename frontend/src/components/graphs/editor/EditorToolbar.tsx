import React from 'react';
import { Button } from '@/components/ui/button';
import { 
  Undo2, 
  Redo2, 
  Save, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Clock
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface EditorToolbarProps {
  // Undo/Redo
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  undoTooltip: string;
  redoTooltip: string;
  
  // Sync status
  isSyncing: boolean;
  lastSyncedAt: Date | null;
  syncError: string | null;
  pendingChanges: boolean;
  
  // Optional additional actions
  onSave?: () => void;
  className?: string;
}

const EditorToolbar: React.FC<EditorToolbarProps> = ({
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  undoTooltip,
  redoTooltip,
  isSyncing,
  lastSyncedAt,
  syncError,
  pendingChanges,
  onSave,
  className
}) => {
  const getSyncStatusIcon = () => {
    if (isSyncing) {
      return <Loader2 className="h-4 w-4 animate-spin" />;
    }
    if (syncError) {
      return <AlertCircle className="h-4 w-4 text-destructive" />;
    }
    if (pendingChanges) {
      return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
    return <CheckCircle className="h-4 w-4 text-green-600" />;
  };
  
  const getSyncStatusText = () => {
    if (isSyncing) return 'Saving...';
    if (syncError) return `Error: ${syncError}`;
    if (pendingChanges) return 'Pending changes';
    if (lastSyncedAt) {
      const timeDiff = Date.now() - lastSyncedAt.getTime();
      if (timeDiff < 60000) return 'Saved';
      if (timeDiff < 3600000) return `Saved ${Math.floor(timeDiff / 60000)}m ago`;
      return `Saved ${Math.floor(timeDiff / 3600000)}h ago`;
    }
    return 'Not saved';
  };
  
  return (
    <TooltipProvider>
      <div className={cn(
        "flex items-center gap-2 p-2 bg-background border rounded-md shadow-sm",
        className
      )}>
        {/* Undo/Redo controls */}
        <div className="flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={onUndo}
                disabled={!canUndo}
                className="h-8 w-8 p-0"
              >
                <Undo2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{undoTooltip}</p>
            </TooltipContent>
          </Tooltip>
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={onRedo}
                disabled={!canRedo}
                className="h-8 w-8 p-0"
              >
                <Redo2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{redoTooltip}</p>
            </TooltipContent>
          </Tooltip>
        </div>
        
        {/* Separator */}
        <div className="w-px h-4 bg-border" />
        
        {/* Sync status */}
        <div className="flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-1">
                {getSyncStatusIcon()}
                <span className="text-xs text-muted-foreground">
                  {getSyncStatusText()}
                </span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {isSyncing && 'Graph is being saved to server'}
                {syncError && `Sync failed: ${syncError}`}
                {pendingChanges && 'Changes will be saved automatically'}
                {!isSyncing && !syncError && !pendingChanges && lastSyncedAt && 
                  `Last saved at ${lastSyncedAt.toLocaleTimeString()}`}
                {!lastSyncedAt && !isSyncing && 'No changes to save'}
              </p>
            </TooltipContent>
          </Tooltip>
          
          {/* Manual save button if provided */}
          {onSave && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onSave}
                  disabled={isSyncing || (!pendingChanges && !syncError)}
                  className="h-8 w-8 p-0"
                >
                  <Save className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Save now</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
};

export default EditorToolbar; 