import React, { useState } from 'react';
import type { DragEvent } from 'react';
import { ChevronDown, ChevronRight, Bot, Wrench, Cpu, Loader2 } from 'lucide-react';
import { useDnD } from '@/contexts/DnDContext';
import { useTools } from '@/hooks/useTools';
import type { NodeType } from '@/contexts/DnDContext';
import type { Tool } from '@/types';

interface AccordionSectionProps {
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  icon: React.ReactNode;
  count?: number;
}

const AccordionSection: React.FC<AccordionSectionProps> = ({ title, isOpen, onToggle, children, icon, count }) => {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium text-gray-900 dark:text-gray-100">{title}</span>
          {count !== undefined && (
            <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-full">
              {count}
            </span>
          )}
        </div>
        {isOpen ? (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className="p-3 bg-white dark:bg-gray-900">
          {children}
        </div>
      )}
    </div>
  );
};

interface DraggableNodeItemProps {
  id: string;
  label: string;
  description: string;
  className: string;
  icon: React.ReactNode;
  onDragStart: (event: DragEvent<HTMLDivElement>, nodeType: NodeType) => void;
}

const DraggableNodeItem: React.FC<DraggableNodeItemProps> = ({
  id,
  label,
  description,
  className,
  icon,
  onDragStart
}) => {
  return (
    <div
      className={`
        relative h-16 p-3 border-2 border-dashed rounded-lg cursor-grab
        flex items-center gap-3 text-left
        transition-all duration-200 ease-in-out
        active:cursor-grabbing active:scale-95
        ${className}
      `}
      onDragStart={(event) => onDragStart(event, id as NodeType)}
      draggable
    >
      <div className="flex-shrink-0">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm mb-1 truncate">
          {label}
        </div>
        <div className="text-xs opacity-70 truncate">
          {description}
        </div>
      </div>
    </div>
  );
};

interface ToolItemProps {
  tool: Tool;
  onDragStart: (event: DragEvent<HTMLDivElement>, nodeType: NodeType) => void;
}

const ToolItem: React.FC<ToolItemProps> = ({ tool, onDragStart }) => {
  return (
    <div
      className="
        relative h-16 p-3 border border-purple-200 dark:border-purple-800 rounded-lg cursor-grab
        flex items-center gap-3 text-left
        bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30
        transition-all duration-200 ease-in-out
        active:cursor-grabbing active:scale-95
      "
      onDragStart={(event) => onDragStart(event, 'tool')}
      draggable
      title={tool.description}
    >
      <div className="flex-shrink-0">
        <Wrench className="w-4 h-4 text-purple-600 dark:text-purple-400" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm mb-1 truncate text-purple-900 dark:text-purple-100">
          {tool.name}
        </div>
        <div className="text-xs opacity-70 truncate text-purple-700 dark:text-purple-300">
          {tool.category} • {tool.is_active ? 'Active' : 'Inactive'}
        </div>
      </div>
      {!tool.is_active && (
        <div className="w-2 h-2 bg-gray-400 rounded-full" title="Inactive" />
      )}
    </div>
  );
};

export const EditorSidebar: React.FC = () => {
  const { setType } = useDnD();
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    agents: true,
    tools: true,
    llm: false,
  });
  
  // Fetch tools from the backend
  const { data: toolsResponse, isLoading: toolsLoading, error: toolsError } = useTools({
    is_active: true, // Only fetch active tools for the sidebar
    limit: 50, // Reasonable limit for sidebar display
  });

  const tools = toolsResponse?.data || [];

  const toggleSection = (section: string) => {
    setOpenSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const onDragStart = (event: DragEvent<HTMLDivElement>, nodeType: NodeType) => {
    setType(nodeType);
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', nodeType || '');
  };

  return (
    <aside className="w-64 min-w-64 border-t border-r border-muted p-4 bg-background h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Node Library
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Drag these nodes to the canvas to build your crew workflow.
        </p>
      </div>

      {/* Node Categories */}
      <div className="space-y-4">
        {/* Agent Nodes Section */}
        <AccordionSection
          title="Agent Nodes"
          isOpen={openSections.agents}
          onToggle={() => toggleSection('agents')}
          icon={<Bot className="w-4 h-4 text-green-600 dark:text-green-400" />}
          count={1}
        >
          <div className="space-y-3">
            <DraggableNodeItem
              id="agent"
              label="Agent"
              description="AI agent with specific role"
              className="border-green-500 bg-green-50 hover:bg-green-100 dark:bg-green-900/20 dark:hover:bg-green-900/30"
              icon={<Bot className="w-4 h-4 text-green-600 dark:text-green-400" />}
              onDragStart={onDragStart}
            />
          </div>
        </AccordionSection>

        {/* Tools Section */}
        <AccordionSection
          title="Tools"
          isOpen={openSections.tools}
          onToggle={() => toggleSection('tools')}
          icon={<Wrench className="w-4 h-4 text-purple-600 dark:text-purple-400" />}
          count={tools.length}
        >
          <div className="space-y-3">
            {toolsLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                <span className="ml-2 text-sm text-gray-500">Loading tools...</span>
              </div>
            ) : toolsError ? (
              <div className="text-center py-4">
                <p className="text-sm text-red-500 mb-2">Failed to load tools</p>
                <button
                  onClick={() => window.location.reload()}
                  className="text-xs text-blue-500 hover:text-blue-600 underline"
                >
                  Retry
                </button>
              </div>
            ) : tools.length === 0 ? (
              <div className="text-center py-4">
                <Wrench className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500 mb-2">No tools available</p>
                <p className="text-xs text-gray-400">Tools will appear here when added to the system</p>
              </div>
            ) : (
              tools.map((tool) => (
                <ToolItem
                  key={tool.id}
                  tool={tool}
                  onDragStart={onDragStart}
                />
              ))
            )}
          </div>
        </AccordionSection>

        {/* LLM Providers Section (placeholder for future implementation) */}
        <AccordionSection
          title="LLM Providers"
          isOpen={openSections.llm}
          onToggle={() => toggleSection('llm')}
          icon={<Cpu className="w-4 h-4 text-orange-600 dark:text-orange-400" />}
          count={0}
        >
          <div className="space-y-3">
            <div className="text-center py-4">
              <Cpu className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500 mb-2">Coming Soon</p>
              <p className="text-xs text-gray-400">LLM provider nodes will be available in a future update</p>
            </div>
          </div>
        </AccordionSection>
      </div>

      {/* Instructions */}
      <div className="mt-8 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
          How to use:
        </h4>
        <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
          <li>• Drag nodes to the canvas</li>
          <li>• Connect nodes with edges</li>
          <li>• Configure node properties</li>
          <li>• Save your workflow</li>
        </ul>
      </div>
    </aside>
  );
};