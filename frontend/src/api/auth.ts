import { api } from "./client";

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name?: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserPublic {
  id: string;
  username: string;
  email: string;
  created_at: string;
  person_id: string | null;
}

export function register(payload: RegisterPayload): Promise<UserPublic> {
  return api.post<UserPublic>("/auth/register", payload);
}

export function login(payload: LoginPayload): Promise<TokenResponse> {
  return api.postForm<TokenResponse>("/auth/login", {
    username: payload.username,
    password: payload.password,
  });
}

export function getMe(): Promise<UserPublic> {
  return api.get<UserPublic>("/auth/me");
}
