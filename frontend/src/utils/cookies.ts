import CryptoJS from 'crypto-js';

// Cookie utility functions for auth token management

interface CookieOptions {
  expires?: Date;
  maxAge?: number;
  path?: string;
  domain?: string;
  secure?: boolean;
  httpOnly?: boolean;
  sameSite?: 'strict' | 'lax' | 'none';
}

// Get encryption secret from environment or use default for development
const getEncryptionSecret = (): string => {
  return import.meta.env.VITE_AUTH_SECRET || 'revai-default-secret-key-change-in-production';
};

// Set a cookie with secure defaults for auth tokens
export const setCookie = (name: string, value: string, options: CookieOptions = {}) => {
  const defaultOptions: CookieOptions = {
    path: '/',
    secure: import.meta.env.PROD, // Use secure in production
    sameSite: 'lax', // CSRF protection
    ...options,
  };

  let cookieString = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;

  if (defaultOptions.expires) {
    cookieString += `; expires=${defaultOptions.expires.toUTCString()}`;
  }

  if (defaultOptions.maxAge) {
    cookieString += `; max-age=${defaultOptions.maxAge}`;
  }

  if (defaultOptions.path) {
    cookieString += `; path=${defaultOptions.path}`;
  }

  if (defaultOptions.domain) {
    cookieString += `; domain=${defaultOptions.domain}`;
  }

  if (defaultOptions.secure) {
    cookieString += '; secure';
  }

  if (defaultOptions.httpOnly) {
    cookieString += '; httpOnly';
  }

  if (defaultOptions.sameSite) {
    cookieString += `; samesite=${defaultOptions.sameSite}`;
  }

  document.cookie = cookieString;
};

// Get a cookie value by name
export const getCookie = (name: string): string | null => {
  const nameEQ = encodeURIComponent(name) + '=';
  const cookies = document.cookie.split(';');

  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.indexOf(nameEQ) === 0) {
      return decodeURIComponent(cookie.substring(nameEQ.length));
    }
  }

  return null;
};

// Remove a cookie by setting it to expire
export const removeCookie = (name: string, options: Omit<CookieOptions, 'expires' | 'maxAge'> = {}) => {
  setCookie(name, '', {
    ...options,
    expires: new Date(0), // Set to past date to remove
  });
};

// Auth data interface
interface AuthData {
  accessToken: string;
  refreshToken: string;
  tokenExpiresAt: string; // ISO string
  user: object;
}

// Single encrypted auth cookie name
const AUTH_COOKIE_NAME = 'revai_auth';

// Encrypt auth data
const encryptAuthData = (data: AuthData): string => {
  try {
    const secret = getEncryptionSecret();
    const jsonString = JSON.stringify(data);
    const encrypted = CryptoJS.AES.encrypt(jsonString, secret).toString();
    return encrypted;
  } catch (error) {
    console.error('Failed to encrypt auth data:', error);
    throw new Error('Encryption failed');
  }
};

// Decrypt auth data
const decryptAuthData = (encryptedData: string): AuthData | null => {
  try {
    const secret = getEncryptionSecret();
    const decryptedBytes = CryptoJS.AES.decrypt(encryptedData, secret);
    const decryptedString = decryptedBytes.toString(CryptoJS.enc.Utf8);
    
    if (!decryptedString) {
      console.error('Failed to decrypt auth data: empty result');
      return null;
    }
    
    return JSON.parse(decryptedString);
  } catch (error) {
    console.error('Failed to decrypt auth data:', error);
    return null;
  }
};

// Set encrypted auth cookie with all auth data
export const setAuthCookie = (
  accessToken: string,
  refreshToken: string,
  expiresAt: Date,
  user: object
) => {
  try {
    const authData: AuthData = {
      accessToken,
      refreshToken,
      tokenExpiresAt: expiresAt.toISOString(),
      user,
    };

    const encryptedData = encryptAuthData(authData);
    const maxAge = Math.floor((expiresAt.getTime() - Date.now()) / 1000); // Convert to seconds

    setCookie(AUTH_COOKIE_NAME, encryptedData, {
      maxAge,
      secure: import.meta.env.PROD,
      sameSite: 'lax',
    });
  } catch (error) {
    console.error('Failed to set auth cookie:', error);
    throw new Error('Failed to save authentication data');
  }
};

// Get decrypted auth data from cookie
export const getAuthCookie = () => {
  try {
    const encryptedData = getCookie(AUTH_COOKIE_NAME);
    
    if (!encryptedData) {
      return {
        accessToken: null,
        refreshToken: null,
        tokenExpiresAt: null,
        user: null,
      };
    }

    const authData = decryptAuthData(encryptedData);
    
    if (!authData) {
      // Corrupted or invalid cookie, remove it
      removeCookie(AUTH_COOKIE_NAME);
      return {
        accessToken: null,
        refreshToken: null,
        tokenExpiresAt: null,
        user: null,
      };
    }

    return {
      accessToken: authData.accessToken,
      refreshToken: authData.refreshToken,
      tokenExpiresAt: authData.tokenExpiresAt ? new Date(authData.tokenExpiresAt) : null,
      user: authData.user,
    };
  } catch (error) {
    console.error('Failed to get auth cookie:', error);
    // Remove corrupted cookie
    removeCookie(AUTH_COOKIE_NAME);
    return {
      accessToken: null,
      refreshToken: null,
      tokenExpiresAt: null,
      user: null,
    };
  }
};

// Clear the encrypted auth cookie
export const clearAuthCookie = () => {
  removeCookie(AUTH_COOKIE_NAME);
};

// Legacy function names for backward compatibility
export const setAuthCookies = setAuthCookie;
export const getAuthCookies = getAuthCookie;
export const clearAuthCookies = clearAuthCookie; 