import { createContext, useContext, useState, useEffect } from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const normalizeUser = (data) => {
    if (!data) return null;
    const normalized = { ...data };
    if (normalized.role) {
      let r = String(normalized.role).toLowerCase();
      if (r === 'manager') r = 'organizer';
      normalized.role = r;
    }
    return normalized;
  };

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      authAPI.getMe()
        .then(data => setUser(normalizeUser(data)))
        .catch(() => {
          localStorage.removeItem("access_token");
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async ({ email, password }) => {
    const data = await authAPI.login({ email, password });
    localStorage.setItem("access_token", data.access_token);
    const userData = await authAPI.getMe();
    setUser(normalizeUser(userData));
  };

  const register = async (userData) => {
    // Map organizer back to MANAGER for backend
    const payload = { ...userData };
    if (payload.role === 'organizer') payload.role = 'MANAGER';
    if (payload.role === 'student') payload.role = 'STUDENT';
    
    await authAPI.register(payload);
    await login({ email: userData.email, password: userData.password });
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
