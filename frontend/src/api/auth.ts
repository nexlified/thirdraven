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

export interface UserPreferencesPublic {
  default_country: string;
  default_timezone: string;
  default_relationship_nature: "" | "personal" | "professional" | "mixed";
  default_visibility: "private" | "household";
  default_closeness_level: number | null;
  default_languages: string[];
}

export type UserPreferencesUpdate = Partial<UserPreferencesPublic>;

export interface ForgotPasswordResponse {
  message: string;
  reset_token: string | null;
}

export interface MessageResponse {
  message: string;
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

export function getMyPreferences(): Promise<UserPreferencesPublic> {
  return api.get<UserPreferencesPublic>("/auth/me/preferences");
}

export function updateMyPreferences(payload: UserPreferencesUpdate): Promise<UserPreferencesPublic> {
  return api.patch<UserPreferencesPublic>("/auth/me/preferences", payload);
}

export function forgotPassword(email: string): Promise<ForgotPasswordResponse> {
  return api.post<ForgotPasswordResponse>("/auth/forgot-password", { email });
}

export function resetPassword(reset_token: string, new_password: string): Promise<MessageResponse> {
  return api.post<MessageResponse>("/auth/reset-password", {
    reset_token,
    new_password,
  });
}

