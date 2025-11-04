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
    // Check if user is logged in on app start
    const userData = localStorage.getItem('user_data');
    
    if (userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    // Mock admin user for testing - remove this when backend is ready
    if (email === 'admin@ulendotiketi.mw' && password === 'admin123') {
      const adminUser: User = {
        id: 'admin-1',
        email: 'admin@ulendotiketi.mw',
        full_name: 'System Administrator',
        role: 'admin',
      };
      setUser(adminUser);
      localStorage.setItem('user_data', JSON.stringify(adminUser));
      return;
    }

    try {
      const { user: userData, token } = await apiService.login(email, password);
      setUser(userData);
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_data', JSON.stringify(userData));
    } catch (error) {
      throw error;
    }
  };

  const register = async (email: string, password: string, fullName: string, role: 'passenger' | 'company', phone?: string) => {
    try {
      const { user: userData, token } = await apiService.register({
        email,
        password,
        full_name: fullName,
        role,
        phone,
      });
      setUser(userData);
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_data', JSON.stringify(userData));
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
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