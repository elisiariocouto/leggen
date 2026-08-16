import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { apiClient } from "../lib/api";
import {
  clearToken,
  getToken,
  getTokenUsername,
  hasValidSession,
  setToken,
} from "../lib/authToken";

interface AuthContextType {
  isAuthenticated: boolean;
  username: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Read synchronously on first render. The token is already in
  // localStorage, so there is nothing to wait for — resolving it in an
  // effect meant a loading flash on every load, and left the router's
  // guard and this context briefly disagreeing.
  const [isAuthenticated, setIsAuthenticated] = useState(hasValidSession);
  const [username, setUsername] = useState<string | null>(() => {
    const token = getToken();
    return token ? getTokenUsername(token) : null;
  });

  const login = useCallback(async (user: string, password: string) => {
    const response = await apiClient.login(user, password);
    setToken(response.access_token);
    setIsAuthenticated(true);
    setUsername(user);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setIsAuthenticated(false);
    setUsername(null);
  }, []);

  const value = useMemo(
    () => ({ isAuthenticated, username, login, logout }),
    [isAuthenticated, username, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
