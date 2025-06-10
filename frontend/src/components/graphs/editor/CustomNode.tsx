import React, { useCallback, useEffect, useMemo, useState, useRef } from 'react';
import { useReactFlow, type NodeProps } from '@xyflow/react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { DynamicIcon } from '@/components/DynamicIcon';
import { useForm } from 'react-hook-form';
import { useGraphStore } from '@/stores';
import { useDebounce } from '@/hooks/useDebounce';
import { useHandleSelection, type HandleInfo } from '@/contexts/HandleSelectionProvider';
import { cn } from '@/lib/utils';
import type { NodeTypeDefinition, FieldDefinition } from '@/types';
import { v4 as uuidv4 } from 'uuid';
import { initializeMissingDefaults } from '@/utils/nodeDefaults';

// Import new components
import NodeForm from './NodeForm';
import NodeSettingsPanel from './NodeSettingsPanel';
import { InputHandle, OutputHandle } from './NodeHandles';
import ToolbarNode from './CustomToolbar';

interface CustomNodeData {
  label: string;
  type: string;
  formData?: Record<string, any>;
  fieldVisibility?: Record<string, boolean>;
  [key: string]: unknown;
}

interface CustomNodeProps extends NodeProps {
  data: CustomNodeData;
}

const CustomNode: React.FC<CustomNodeProps> = ({ data, selected, id }) => {
  const { nodeDef } = useGraphStore();
  const { setNodes, getNodes, deleteElements } = useReactFlow();
  const { 
    selectedHandle,
    selectHandle, 
    clearSelection, 
    tryCreateConnection, 
    getHandleCompatibleTypes
  } = useHandleSelection();
  
  const [localFormData, setLocalFormData] = useState<Record<string, any>>(
    data.formData || {}
  );
  const [showSettings, setShowSettings] = useState(false);

  // Get node definition
  const nodeDefinition = useMemo((): NodeTypeDefinition | null => {
    return nodeDef?.node_types[data.type] || null;
  }, [nodeDef, data.type]);

  // Initialize form
  const form = useForm({
    defaultValues: localFormData,
  });

  // Debounced save function - now just updates node data directly
  const debouncedFormData = useDebounce(localFormData, 500);

  // Update node data (which will trigger sync via FlowEditor)
  useEffect(() => {
    if (debouncedFormData && Object.keys(debouncedFormData).length > 0) {
      // Update node data directly - sync handled by parent
      setNodes((nodes) =>
        nodes.map((node) =>
          node.id === id
            ? { 
                ...node, 
                data: { 
                  ...node.data, 
                  formData: debouncedFormData,
                  // Remove autoInit flag when user makes real changes
                  autoInit: undefined
                } 
              }
            : node
        )
      );
    }
  }, [debouncedFormData, id, setNodes]);

  // Track if we've already initialized defaults for this node
  const initializedRef = useRef(false);

  // Initialize form data from node data (not localStorage)
  useEffect(() => {
    console.log(`🔄 CustomNode ${id} data changed:`, data);
    
    // Only run default initialization once when the node is first loaded or when nodeDefinition changes
    if (!initializedRef.current && nodeDefinition && nodeDef) {
      console.log(`🚀 First load for node ${id}, checking for missing defaults`);
      
      const { defaultFormData, defaultFieldVisibility } = initializeMissingDefaults(
        data.type,
        nodeDef,
        data.formData,
        data.fieldVisibility
      );
      
      // Only update if there are actually missing defaults
      const hasNewDefaults = Object.keys(defaultFormData || {}).length > 0;
      const hasNewVisibility = Object.keys(defaultFieldVisibility || {}).length > 0;
      
      if (hasNewDefaults || hasNewVisibility) {
        console.log(`🔧 Initializing missing defaults for node ${id}:`, { 
          addedFormData: defaultFormData, 
          addedFieldVisibility: defaultFieldVisibility 
        });
        
        // Merge existing data with defaults
        const mergedFormData = { ...defaultFormData, ...(data.formData || {}) };
        const mergedFieldVisibility = { ...defaultFieldVisibility, ...(data.fieldVisibility || {}) };
        
        // Update the node with the merged data
        setNodes((nodes) =>
          nodes.map((node) =>
            node.id === id
              ? { 
                  ...node, 
                  data: { 
                    ...node.data, 
                    formData: mergedFormData,
                    fieldVisibility: mergedFieldVisibility,
                    // Mark as automatic initialization to prevent sync loop
                    autoInit: true
                  } 
                }
              : node
          )
        );
      }
      
      initializedRef.current = true;
    }
    
    // Always update the local form state with current data
    const currentFormData = data.formData || {};
    if (Object.keys(currentFormData).length > 0) {
      console.log(`📋 Loading form data for node ${id}:`, currentFormData);
      setLocalFormData(currentFormData);
      form.reset(currentFormData);
    } else {
      console.log(`⚠️ No form data found for node ${id}, initializing empty`);
      setLocalFormData({});
      form.reset({});
    }
  }, [data.formData, data.fieldVisibility, form, id, nodeDefinition, nodeDef, setNodes, data]);

  // Reset initialization flag when node type changes
  useEffect(() => {
    initializedRef.current = false;
  }, [data.type]);

  // Handle background click to clear selection
  const handleBackgroundClick = useCallback((e: React.MouseEvent) => {
    // Only clear if clicking directly on the card background, not on inputs or handles
    if (e.target === e.currentTarget) {
      clearSelection();
    }
  }, [clearSelection]);

  // Handle form changes
  const handleFormChange = useCallback((fieldName: string, value: any) => {
    if (fieldName === 'fieldVisibility') {
      // Handle field visibility changes separately - update node data directly
      setNodes((nodes) =>
        nodes.map((node) =>
          node.id === id
            ? { 
                ...node, 
                data: { 
                  ...node.data, 
                  fieldVisibility: value,
                  // Remove autoInit flag when user makes changes
                  autoInit: undefined
                } 
              }
            : node
        )
      );
    } else {
      // Handle regular form data changes
      setLocalFormData((prev) => ({
        ...prev,
        [fieldName]: value,
      }));
    }
  }, [id, setNodes]);

  // Check if field needs a handle
  const fieldNeedsHandle = useCallback((field: FieldDefinition): boolean => {
    if (!field.filter) return false;
    return 'type' in field.filter || 'category' in field.filter;
  }, []);

  // Handle input handle click
  const handleInputHandleClick = useCallback((e: React.MouseEvent, fieldName: string) => {
    e.stopPropagation();
    
    const handleInfo: HandleInfo = {
      nodeId: id,
      nodeType: data.type,
      fieldName,
      handleType: 'target',
      handleId: `input-${id}-${fieldName}`
    };

    if (selectedHandle && selectedHandle.handleId !== handleInfo.handleId) {
      tryCreateConnection(handleInfo);
    } else {
      selectHandle(handleInfo);
    }
  }, [id, data.type, selectedHandle, selectHandle, tryCreateConnection]);

  // Handle output handle click
  const handleOutputHandleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    
    const handleInfo: HandleInfo = {
      nodeId: id,
      nodeType: data.type,
      handleType: 'source',
      handleId: `output-${id}`
    };

    if (selectedHandle && selectedHandle.handleId !== handleInfo.handleId) {
      tryCreateConnection(handleInfo);
    } else {
      selectHandle(handleInfo);
    }
  }, [id, data.type, selectedHandle, selectHandle, tryCreateConnection]);

  // Render input handle for fields that need them
  const renderInputHandle = useCallback((fieldName: string, field: FieldDefinition) => {
    return (
      <InputHandle
        key={fieldName}
        nodeId={id}
        nodeType={data.type}
        fieldName={fieldName}
        field={field}
        onHandleClick={(e) => handleInputHandleClick(e, fieldName)}
        getHandleCompatibleTypes={getHandleCompatibleTypes}
      />
    );
  }, [id, data.type, handleInputHandleClick, getHandleCompatibleTypes]);

  // Toolbar action handlers
  const handleCopyNode = useCallback(() => {
    const nodes = getNodes();
    const currentNode = nodes.find((n) => n.id === id);
    if (!currentNode) return;

    // Copy to clipboard
    const clipboardData = {
      nodes: [{
        ...currentNode,
        selected: false,
      }],
      edges: []
    };

    localStorage.setItem('reactflow-clipboard', JSON.stringify(clipboardData));
  }, [getNodes, id]);

  const handleDuplicate = useCallback(() => {
    const nodes = getNodes();
    const currentNode = nodes.find((n) => n.id === id);
    if (!currentNode) return;

    const newNode = {
      ...currentNode,
      id: uuidv4(),
      position: {
        x: currentNode.position.x + 50,
        y: currentNode.position.y + 50,
      },
      data: {
        ...currentNode.data,
        label: `${currentNode.data.label} (Copy)`,
      },
      selected: false,
    };

    setNodes((nodes) => [...nodes, newNode]);
  }, [getNodes, setNodes, id]);

  const handleDelete = useCallback(() => {
    deleteElements({ nodes: [{ id }] });
    // Node data is now handled by backend sync, no localStorage cleanup needed
  }, [deleteElements, id]);

  const handleSettings = useCallback(() => {
    setShowSettings(!showSettings);
  }, [showSettings]);

  // Check if only this node is selected (for toolbar visibility)
  const isOnlyNodeSelected = useMemo(() => {
    const allNodes = getNodes();
    const selectedNodes = allNodes.filter(node => node.selected);
    return selectedNodes.length === 1 && selected;
  }, [getNodes, selected]);

  if (!nodeDefinition) {
    return (
      <Card className="w-64 border-red-500">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Unknown Node</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-red-500">Node type "{data.type}" not found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="relative">
      {/* Node Card */}
      <Card 
        className={cn(
          "w-80 shadow-lg transition-all duration-200 cursor-default gap-0",
          selected && "ring-2 ring-primary"
        )}
        onClick={handleBackgroundClick}
      >
        <CardHeader className="pb-3 cursor-move " data-drag-handle>
          <CardTitle className="flex items-center gap-2 text-sm">
            <DynamicIcon 
              name={nodeDefinition.icon} 
              className="w-4 h-4 text-muted-foreground" 
            />
            {nodeDefinition.name}
          </CardTitle>
          {nodeDefinition.description && (
            <p className="text-xs text-muted-foreground">{nodeDefinition.description}</p>
          )}
        </CardHeader>
        
        <CardContent className="space-y-4 px-0 cursor-default border-y border-muted py-2" data-drag-handle={false}>
          <NodeForm
            nodeDefinition={nodeDefinition}
            localFormData={localFormData}
            onFormChange={handleFormChange}
            form={form}
            fieldNeedsHandle={fieldNeedsHandle}
            renderInputHandle={renderInputHandle}
            fieldVisibility={data.fieldVisibility}
          />
        </CardContent>

        {/* Footer with Output */}
        <CardFooter className="flex justify-end items-center pt-2 pb-3 relative cursor-default" data-drag-handle={false}>
          <OutputHandle
            nodeId={id}
            nodeType={data.type}
            onHandleClick={handleOutputHandleClick}
            getHandleCompatibleTypes={getHandleCompatibleTypes}
          />
        </CardFooter>
      </Card>

      {/* Toolbar */}
      <ToolbarNode
        selected={isOnlyNodeSelected}
        onCopy={handleCopyNode}
        onDuplicate={handleDuplicate}
        onSettings={handleSettings}
        onDelete={handleDelete}
      />

      {/* Settings Panel */}
      {showSettings && (
        <NodeSettingsPanel
          nodeData={data}
          nodeDefinition={nodeDefinition}
          onFormChange={handleFormChange}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
};

export default CustomNode; 