import type { NodeDefinitions, FieldDefinition } from '@/types';

/**
 * Initialize default form data and field visibility for a node type
 */
export function initializeNodeDefaults(
  nodeType: string,
  nodeDef: NodeDefinitions | null
): { formData: Record<string, any>; fieldVisibility: Record<string, boolean> } {
  if (!nodeDef?.node_types[nodeType]) {
    return { formData: {}, fieldVisibility: {} };
  }

  const nodeDefinition = nodeDef.node_types[nodeType];
  const formData: Record<string, any> = {};
  const fieldVisibility: Record<string, boolean> = {};

  // Initialize each field with its default value and visibility
  Object.entries(nodeDefinition.fields).forEach(([fieldName, field]: [string, FieldDefinition]) => {
    // Set field visibility based on show_by_default
    fieldVisibility[fieldName] = field.show_by_default;

    // Set default value if defined or calculate appropriate default
    if (field.default !== undefined) {
      formData[fieldName] = field.default;
    } else {
      // Calculate appropriate default based on field type
      switch (field.type) {
        case 'select':
          formData[fieldName] = field.options?.[0]?.value || '';
          break;
        case 'multi_select':
          formData[fieldName] = [];
          break;
        case 'boolean':
          formData[fieldName] = false;
          break;
        case 'number':
        case 'slider':
          formData[fieldName] = field.validation?.min || 0;
          break;
        case 'json':
          formData[fieldName] = {};
          break;
        default:
          formData[fieldName] = '';
      }
    }
  });

  return { formData, fieldVisibility };
}

/**
 * Initialize missing default values for an existing node
 * Only adds defaults for fields that don't already have values
 */
export function initializeMissingDefaults(
  nodeType: string,
  nodeDef: NodeDefinitions | null,
  existingFormData?: Record<string, any>,
  existingFieldVisibility?: Record<string, boolean>
): { defaultFormData: Record<string, any>; defaultFieldVisibility: Record<string, boolean> } {
  if (!nodeDef?.node_types[nodeType]) {
    return { defaultFormData: {}, defaultFieldVisibility: {} };
  }

  const nodeDefinition = nodeDef.node_types[nodeType];
  const defaultFormData: Record<string, any> = {};
  const defaultFieldVisibility: Record<string, boolean> = {};

  // Initialize defaults for each field in the node definition
  Object.entries(nodeDefinition.fields).forEach(([fieldName, field]: [string, FieldDefinition]) => {
    // Set field visibility based on show_by_default if not already set
    if (existingFieldVisibility?.[fieldName] === undefined) {
      defaultFieldVisibility[fieldName] = field.show_by_default;
    }

    // Set default value if not already set and field has a default
    if (existingFormData?.[fieldName] === undefined) {
      if (field.default !== undefined) {
        defaultFormData[fieldName] = field.default;
      } else {
        // Calculate appropriate default based on field type
        switch (field.type) {
          case 'select':
            defaultFormData[fieldName] = field.options?.[0]?.value || '';
            break;
          case 'multi_select':
            defaultFormData[fieldName] = [];
            break;
          case 'boolean':
            defaultFormData[fieldName] = false;
            break;
          case 'number':
          case 'slider':
            defaultFormData[fieldName] = field.validation?.min || 0;
            break;
          case 'json':
            defaultFormData[fieldName] = {};
            break;
          default:
            defaultFormData[fieldName] = '';
        }
      }
    }
  });

  return { defaultFormData, defaultFieldVisibility };
} 