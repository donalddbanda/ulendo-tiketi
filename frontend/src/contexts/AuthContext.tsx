import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiService, User } from '../services/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, role: 'passenger' | 'company', phone?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Try to hydrate current user from the backend session first
    (async () => {
      try {
        const resp = await apiService.whoami();
        const remoteUser: any = resp?.user;
        if (remoteUser) {
          const normalized: User = {
            id: String(remoteUser.id),
            email: remoteUser.email || '',
            full_name: remoteUser.full_name || remoteUser.name || '',
            role: (remoteUser.role || 'passenger') as User['role'],
            phone: remoteUser.phone || remoteUser.phone_number || undefined,
          };
          setUser(normalized);
          localStorage.setItem('user_data', JSON.stringify(normalized));
        } else {
          // fallback to localStorage if any
          const userData = localStorage.getItem('user_data');
          if (userData) setUser(JSON.parse(userData));
        }
      } catch (e) {
        // ignore and fallback to localStorage
        const userData = localStorage.getItem('user_data');
        if (userData) setUser(JSON.parse(userData));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const resp = await apiService.login(email, password);
      // Backend may return { user: { ... } } or { user: { full_name } }
      const rawUser: any = resp?.user || resp;
      const normalized: User = {
        id: String(rawUser.id),
        email: rawUser.email || '',
        full_name: rawUser.full_name || rawUser.name || '',
        role: (rawUser.role || 'passenger') as User['role'],
        phone: rawUser.phone || rawUser.phone_number || undefined,
      };

      setUser(normalized);
      // Backend uses session cookies; no token expected
      localStorage.setItem('user_data', JSON.stringify(normalized));
    } catch (error) {
      throw error;
    }
  };

  const register = async (email: string, password: string, fullName: string, role: 'passenger' | 'company', phone?: string) => {
    try {
      const resp = await apiService.register(email, password, fullName, role, phone);
      const rawUser: any = resp?.user || resp;
      const normalized: User = {
        id: String(rawUser.id),
        email: rawUser.email || '',
        full_name: rawUser.full_name || rawUser.name || '',
        role: (rawUser.role || 'passenger') as User['role'],
        phone: rawUser.phone || rawUser.phone_number || undefined,
      };

      setUser(normalized);
      localStorage.setItem('user_data', JSON.stringify(normalized));
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await apiService.logout();
    } catch (e) {
      // ignore server logout errors and continue clearing local state
    }
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}