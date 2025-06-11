import type { Node } from '@xyflow/react';
import type { NodeDefinitions, FieldDefinition } from '@/types';

/**
 * Determine if a field represents a node reference based on its definition
 */
export function isNodeReferenceField(field: FieldDefinition): boolean {
  if (!field.filter) return false;
  
  // Fields with type or category filters are node references
  return !!(field.filter.type || field.filter.category);
}

/**
 * Convert form data to storage format, replacing node IDs with "node/ID" format
 */
export function convertFormDataForStorage(
  formData: Record<string, any>,
  nodeType: string,
  nodeDef: NodeDefinitions | null
): Record<string, any> {
  if (!nodeDef?.node_types[nodeType]) {
    //console.debug(`⚠️ No node definition found for type: ${nodeType}`);
    return formData;
  }

  const nodeDefinition = nodeDef.node_types[nodeType];
  const convertedData: Record<string, any> = {};

  //console.debug(`🔄 Converting form data for ${nodeType}:`, formData);

  Object.entries(formData).forEach(([fieldName, value]) => {
    const field = nodeDefinition.fields[fieldName];
    
    if (field && isNodeReferenceField(field)) {
      //console.debug(`🔗 Converting node reference field '${fieldName}':`, value, 'field def:', field);
      
      // Convert node references to "node/ID" format
      if (Array.isArray(value)) {
        // Handle array of node references
        convertedData[fieldName] = value.map(id => 
          id && typeof id === 'string' ? `node/${id}` : id
        ).filter(v => v != null); // Remove null/undefined values
        //console.debug(`🔗 Array conversion result:`, convertedData[fieldName]);
      } else if (value && typeof value === 'string') {
        // Handle single node reference
        convertedData[fieldName] = `node/${value}`;
        //console.debug(`🔗 Single conversion result:`, convertedData[fieldName]);
      } else {
        // Handle null/empty values
        convertedData[fieldName] = value;
        //console.debug(`🔗 Null/empty value preserved:`, convertedData[fieldName]);
      }
    } else {
      // Regular field, no conversion needed
      convertedData[fieldName] = value;
      if (field) {
        //console.debug(`📝 Regular field '${fieldName}':`, value);
      } else {
        //console.debug(`❓ Unknown field '${fieldName}':`, value);
      }
    }
  });

  //console.debug(`✅ Final converted data for ${nodeType}:`, convertedData);
  return convertedData;
}

/**
 * Convert storage format back to form data, replacing "node/ID" with just IDs
 */
export function convertFormDataFromStorage(
  storedData: Record<string, any>,
  allNodes: Node[]
): Record<string, any> {
  const formData: Record<string, any> = {};
  
  //console.debug(`🔄 Converting from storage format:`, storedData);
  
  Object.entries(storedData).forEach(([fieldName, value]) => {
    if (typeof value === 'string' && value.startsWith('node/')) {
      // Handle single node reference
      const nodeId = value.substring(5); // Remove 'node/' prefix
      const referencedNode = allNodes.find(n => n.id === nodeId);
      
      if (referencedNode) {
        formData[fieldName] = nodeId;
        //console.debug(`🔗 Restored single reference '${fieldName}': ${value} -> ${nodeId}`);
      } else {
        //console.warn(`Referenced node ${nodeId} not found for field ${fieldName}`);
        formData[fieldName] = null; // Reference to missing node
      }
    } else if (Array.isArray(value)) {
      // Handle array that might contain node references
      formData[fieldName] = value.map(v => {
        if (typeof v === 'string' && v.startsWith('node/')) {
          const nodeId = v.substring(5);
          const referencedNode = allNodes.find(n => n.id === nodeId);
          
          if (referencedNode) {
            //console.debug(`🔗 Restored array reference '${fieldName}': ${v} -> ${nodeId}`);
            return nodeId;
          } else {
            //console.warn(`Referenced node ${nodeId} not found in array field ${fieldName}`);
            return null;
          }
        }
        return v;
      }).filter(v => v != null); // Remove missing node references from arrays
      //console.debug(`🔗 Restored array field '${fieldName}':`, formData[fieldName]);
    } else {
      // Regular field, no conversion needed
      formData[fieldName] = value;
      //console.debug(`📝 Regular field '${fieldName}':`, value);
    }
  });

  //console.debug(`✅ Final restored form data:`, formData);
  return formData;
}

/**
 * Validate that all node references in form data point to existing nodes
 */
export function validateNodeReferences(
  formData: Record<string, any>,
  nodeType: string,
  nodeDef: NodeDefinitions | null,
  allNodes: Node[]
): { isValid: boolean; errors: string[] } {
  if (!nodeDef?.node_types[nodeType]) {
    return { isValid: true, errors: [] };
  }

  const nodeDefinition = nodeDef.node_types[nodeType];
  const errors: string[] = [];

  Object.entries(formData).forEach(([fieldName, value]) => {
    const field = nodeDefinition.fields[fieldName];
    
    if (field && isNodeReferenceField(field)) {
      if (Array.isArray(value)) {
        // Validate array of node references
        value.forEach(id => {
          if (id && typeof id === 'string' && !allNodes.find(n => n.id === id)) {
            errors.push(`Field '${fieldName}' references missing node: ${id}`);
          }
        });
      } else if (value && typeof value === 'string') {
        // Validate single node reference
        if (!allNodes.find(n => n.id === value)) {
          errors.push(`Field '${fieldName}' references missing node: ${value}`);
        }
      }
    }
  });

  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Debug utility to show the conversion between form data and storage format
 */
export function debugNodeReferenceConversion(
  formData: Record<string, any>,
  nodeType: string,
  nodeDef: NodeDefinitions | null,
  allNodes: Node[]
) {
  console.group(`🔍 Debug Node Reference Conversion for ${nodeType}`);
  
  console.debug('Original form data:', formData);
  
  const storageData = convertFormDataForStorage(formData, nodeType, nodeDef);
  console.debug('Storage format:', storageData);
  
  const restoredData = convertFormDataFromStorage(storageData, allNodes);
  console.debug('Restored form data:', restoredData);
  
  const validation = validateNodeReferences(formData, nodeType, nodeDef, allNodes);
  console.debug('Validation result:', validation);
  
  console.groupEnd();
  
  return {
    original: formData,
    storage: storageData,
    restored: restoredData,
    validation
  };
} 