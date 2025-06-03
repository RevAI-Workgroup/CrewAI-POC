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
