import { useState } from 'react';
import { Menu, X, User, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Logo } from './Logo';

interface NavbarProps {
  onShowAuth: (type: 'login' | 'register') => void;
}

export function Navbar({ onShowAuth }: NavbarProps) {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const navigateTo = (path: string) => {
    window.history.pushState({}, '', path);
    window.dispatchEvent(new PopStateEvent('popstate'));
    setMobileMenuOpen(false);
    setUserMenuOpen(false);
  };

  const handleSignOut = async () => {
    try {
      await logout();
      setUserMenuOpen(false);
      navigateTo('/');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const getDashboardPath = () => {
    if (!user) return '/';
    switch (user.role) {
      case 'admin':
        return '/admin';
      case 'company':
        return '/company';
      default:
        return '/dashboard';
    }
  };

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div 
            className="flex items-center gap-2 cursor-pointer" 
            onClick={() => navigateTo('/')}
          >
            <Logo />
          </div>

          <div className="hidden md:flex items-center gap-6">
            <button 
              onClick={() => navigateTo('/')}
              className="text-[#0A2239] hover:text-[#0057A4] font-medium transition-colors"
            >
              Home
            </button>
            <button 
              onClick={() => navigateTo('/search')}
              className="text-[#0A2239] hover:text-[#0057A4] font-medium transition-colors"
            >
              Search Buses
            </button>

            {user ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#F2F4F7] hover:bg-[#0057A4] hover:text-white transition-all"
                >
                  <User className="w-5 h-5" />
                  <span className="font-medium">{user.full_name || 'User'}</span>
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 border border-gray-100">
                    <button
                      onClick={() => navigateTo(getDashboardPath())}
                      className="w-full text-left px-4 py-2 text-[#0A2239] hover:bg-[#F2F4F7] transition-colors"
                    >
                      {user.role === 'admin' ? 'Admin Dashboard' : 'Dashboard'}
                    </button>
                    <button
                      onClick={handleSignOut}
                      className="w-full text-left px-4 py-2 text-[#0A2239] hover:bg-[#F2F4F7] transition-colors flex items-center gap-2"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => onShowAuth('login')}
                  className="px-4 py-2 text-[#0057A4] hover:text-[#00B4A2] font-medium transition-colors"
                >
                  Login
                </button>
                <button
                  onClick={() => onShowAuth('register')}
                  className="px-6 py-2 bg-[#FF7A00] text-white rounded-lg font-medium hover:bg-[#FF7A00]/90 transition-all shadow-sm hover:shadow-md"
                >
                  Sign Up
                </button>
              </div>
            )}
          </div>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-[#F2F4F7] transition-colors"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-100">
          <div className="px-4 py-3 space-y-3">
            <button 
              onClick={() => navigateTo('/')}
              className="block w-full text-left py-2 text-[#0A2239] hover:text-[#0057A4] font-medium"
            >
              Home
            </button>
            <button 
              onClick={() => navigateTo('/search')}
              className="block w-full text-left py-2 text-[#0A2239] hover:text-[#0057A4] font-medium"
            >
              Search Buses
            </button>

            {user ? (
              <>
                <button
                  onClick={() => navigateTo(getDashboardPath())}
                  className="block w-full text-left py-2 text-[#0A2239] hover:text-[#0057A4] font-medium"
                >
                  {user.role === 'admin' ? 'Admin Dashboard' : 'Dashboard'}
                </button>
                <button
                  onClick={handleSignOut}
                  className="block w-full text-left py-2 text-[#0A2239] hover:text-[#0057A4] font-medium flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => {
                    onShowAuth('login');
                    setMobileMenuOpen(false);
                  }}
                  className="block w-full text-left py-2 text-[#0A2239] hover:text-[#0057A4] font-medium"
                >
                  Login
                </button>
                <button
                  onClick={() => {
                    onShowAuth('register');
                    setMobileMenuOpen(false);
                  }}
                  className="block w-full px-6 py-2 bg-[#FF7A00] text-white rounded-lg font-medium hover:bg-[#FF7A00]/90 transition-all"
                >
                  Sign Up
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}