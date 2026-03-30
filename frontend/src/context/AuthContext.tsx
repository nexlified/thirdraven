import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { getMe, login, register, type LoginPayload, type RegisterPayload, type UserPublic } from "../api/auth";

interface AuthState {
  user: UserPublic | null;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  signIn: (payload: LoginPayload) => Promise<void>;
  signUp: (payload: RegisterPayload) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, loading: true });

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setState({ user: null, loading: false });
      return;
    }
    try {
      const user = await getMe();
      setState({ user, loading: false });
    } catch {
      localStorage.removeItem("access_token");
      setState({ user: null, loading: false });
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const signIn = useCallback(async (payload: LoginPayload) => {
    const { access_token } = await login(payload);
    localStorage.setItem("access_token", access_token);
    await loadUser();
  }, [loadUser]);

  const signUp = useCallback(async (payload: RegisterPayload) => {
    await register(payload);
    await signIn({ username: payload.username, password: payload.password });
  }, [signIn]);

  const signOut = useCallback(() => {
    localStorage.removeItem("access_token");
    setState({ user: null, loading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
