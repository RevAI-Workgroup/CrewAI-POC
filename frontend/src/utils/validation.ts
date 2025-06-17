import { VALIDATION_RULES } from './constants';

// Email validation
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Pseudo validation
export const isValidPseudo = (pseudo: string): boolean => {
  return (
    pseudo.length >= VALIDATION_RULES.PSEUDO.MIN_LENGTH &&
    pseudo.length <= VALIDATION_RULES.PSEUDO.MAX_LENGTH
  );
};

// Passphrase validation
export const isValidPassphrase = (passphrase: string): boolean => {
  const words = passphrase.split(VALIDATION_RULES.PASSPHRASE.SEPARATOR);
  return words.length === VALIDATION_RULES.PASSPHRASE.WORD_COUNT;
};

// Graph name validation
export const isValidGraphName = (name: string): boolean => {
  return (
    name.trim().length >= VALIDATION_RULES.GRAPH_NAME.MIN_LENGTH &&
    name.trim().length <= VALIDATION_RULES.GRAPH_NAME.MAX_LENGTH
  );
};

// URL validation
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// Generic form validation
export const validateRequired = (value: any): boolean => {
  if (typeof value === 'string') {
    return value.trim().length > 0;
  }
  return value !== null && value !== undefined;
};

// Graph crew validation for chat functionality
export const countCrewNodes = (graphData: any): number => {
  if (!graphData) return 0;
  
  // Check both legacy format and new graph_data structure
  const nodes = graphData.nodes || graphData.graph_data?.nodes || [];
  return nodes.filter((node: any) => node.type === 'crew').length;
};

export const isGraphChatEligible = (graphData: any): boolean => {
  const crewCount = countCrewNodes(graphData);
  return crewCount === 1;
};

export const getGraphChatIneligibilityReason = (graphData: any): string | null => {
  const crewCount = countCrewNodes(graphData);
  
  if (crewCount === 0) {
    return "This graph has no crew nodes. At least one crew is required for chat functionality.";
  }
  
  if (crewCount > 1) {
    return "This graph has multiple crew nodes. Only graphs with exactly one crew can use chat functionality.";
  }
  
  return null; // Graph is eligible
};

// Chat message validation
export const isValidChatMessage = (message: string): boolean => {
  return (
    message.trim().length > 0 &&
    message.trim().length <= VALIDATION_RULES.CHAT_MESSAGE?.MAX_LENGTH || 2000
  );
};

export const getChatMessageValidationError = (message: string): string | null => {
  if (!message || message.trim().length === 0) {
    return "Message cannot be empty";
  }
  
  const maxLength = VALIDATION_RULES.CHAT_MESSAGE?.MAX_LENGTH || 2000;
  if (message.trim().length > maxLength) {
    return `Message is too long (${message.length}/${maxLength} characters)`;
  }
  
  return null;
};

// Thread name validation
export const isValidThreadName = (name: string): boolean => {
  return (
    name.trim().length >= 1 &&
    name.trim().length <= 200
  );
};

export const getThreadNameValidationError = (name: string): string | null => {
  if (!name || name.trim().length === 0) {
    return "Thread name cannot be empty";
  }
  
  if (name.trim().length > 200) {
    return `Thread name is too long (${name.length}/200 characters)`;
  }
  
  return null;
};

// Network connectivity validation
export const isOnline = (): boolean => {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
};

// Validation result type
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Comprehensive form validation
export const validateChatForm = (data: {
  message?: string;
  threadName?: string;
  graphId?: string;
}): ValidationResult => {
  const errors: string[] = [];
  
  if (data.message !== undefined) {
    const messageError = getChatMessageValidationError(data.message);
    if (messageError) errors.push(messageError);
  }
  
  if (data.threadName !== undefined) {
    const nameError = getThreadNameValidationError(data.threadName);
    if (nameError) errors.push(nameError);
  }
  
  if (data.graphId !== undefined && !data.graphId.trim()) {
    errors.push("Graph ID is required");
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
};
