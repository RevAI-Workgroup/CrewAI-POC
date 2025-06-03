import { format as formatDate, parseISO, isValid } from 'date-fns';

// Date formatting utilities
export const formatDateTime = (date: string | Date): string => {
  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date;
    return isValid(parsedDate)
      ? formatDate(parsedDate, 'MMM dd, yyyy HH:mm')
      : 'Invalid date';
  } catch {
    return 'Invalid date';
  }
};

export const formatDateOnly = (date: string | Date): string => {
  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date;
    return isValid(parsedDate)
      ? formatDate(parsedDate, 'MMM dd, yyyy')
      : 'Invalid date';
  } catch {
    return 'Invalid date';
  }
};

export const formatTimeOnly = (date: string | Date): string => {
  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date;
    return isValid(parsedDate)
      ? formatDate(parsedDate, 'HH:mm')
      : 'Invalid time';
  } catch {
    return 'Invalid time';
  }
};

// String formatting utilities
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

export const capitalizeWords = (str: string): string => {
  return str.split(' ').map(capitalize).join(' ');
};

export const truncate = (str: string, maxLength: number): string => {
  return str.length > maxLength ? `${str.slice(0, maxLength)}...` : str;
};

// Number formatting utilities
export const formatFileSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${Math.round((bytes / Math.pow(1024, i)) * 100) / 100} ${sizes[i]}`;
};

export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num);
};

// URL formatting utilities
export const sanitizeUrl = (url: string): string => {
  return url.replace(/[^a-zA-Z0-9-._~:/?#[\]@!$&'()*+,;=]/g, '');
};

export const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase())
    .join('')
    .slice(0, 2);
};
