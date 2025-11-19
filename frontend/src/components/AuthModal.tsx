import { useState } from 'react';
import { X, Mail, Lock, User, Phone } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface AuthModalProps {
  type: 'login' | 'register';
  onClose: () => void;
}

export function AuthModal({ type, onClose }: AuthModalProps) {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(type === 'login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    loginIdentifier: '',  // email or phone for login
    email: '',  // optional email for registration
    password: '',
    fullName: '',
    phone: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(formData.loginIdentifier, formData.password);
      } else {
        // For registration, use email if provided, otherwise let backend generate placeholder
        await register(formData.email || formData.phone, formData.password, formData.fullName, 'passenger', formData.phone);
      }
      onClose();
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 hover:bg-[#F2F4F7] rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-2xl font-bold text-[#0A2239] mb-6">
          {isLogin ? 'Welcome Back' : 'Create Account'}
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <>
              <div>
                <label className="block text-sm font-medium text-[#0A2239] mb-2">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    required
                    value={formData.fullName}
                    onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                    placeholder="John Banda"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#0A2239] mb-2">
                  Phone Number *
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                    placeholder="+265 999 123 456"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[#0A2239] mb-2">
                  Email (optional)
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                    placeholder="you@example.com (optional)"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-[#0A2239] mb-2">
              {isLogin ? 'Email or Phone Number' : 'Password'}
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              {isLogin ? (
                <input
                  type="text"
                  required
                  value={formData.loginIdentifier}
                  onChange={(e) => setFormData({ ...formData, loginIdentifier: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                  placeholder="you@example.com or +265 999 123 456"
                />
              ) : (
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                  placeholder="••••••••"
                />
              )}
            </div>
          </div>

          {isLogin && (
            <div>
              <label className="block text-sm font-medium text-[#0A2239] mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>
          )}

          {!isLogin && (
            <div className="text-sm text-gray-600">
              Companies must be registered by an admin. To join as a company, ask an admin to create your account — you'll receive a password reset link.
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-[#FF7A00] text-white rounded-lg font-medium hover:bg-[#FF7A00]/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
          >
            {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-[#0057A4] hover:text-[#00B4A2] font-medium transition-colors"
          >
            {isLogin ? "Don't have an account? Sign Up" : 'Already have an account? Sign In'}
          </button>
        </div>
      </div>
    </div>
  );
}