export interface RegisterRequest {
  pseudo: string;
}

export interface RegisterResponse {
  id: string;
  pseudo: string;
  role: 'user' | 'admin';
  passphrase: string;
  created_at: string;
  updated_at: string;
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface LoginRequest {
  passphrase: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: {
    id: string;
    pseudo: string;
    role: 'user' | 'admin';
    created_at: string;
    updated_at: string;
    last_login?: string;
  };
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface AuthState {
  user: LoginResponse['user'] | null;
  tokens: {
    access_token: string;
    refresh_token: string;
    expires_in: number;
  } | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
