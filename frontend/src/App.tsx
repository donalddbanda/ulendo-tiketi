import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { AuthModal } from './components/AuthModal';
import { HomePage } from './components/HomePage';
import { SearchResults } from './components/SearchResults';
import { BookingFlow } from './components/BookingFlow';
import { UserDashboard } from './components/UserDashboard';

// Fixed default imports
import CompanyDashboard from './components/CompanyDashboard';
import AdminDashboard from './components/AdminDashboard';
import ConductorDashboard from './components/ConductorDashboard';
import AccountsManagerDashboard from './components/AccountsManagerDashboard';
import ErrorBoundary from './components/ErrorBoundary';

function AppContent() {
  const { user } = useAuth();
  const [showAuth, setShowAuth] = useState<'login' | 'register' | null>(null);
  const [currentView, setCurrentView] = useState<
    'home' |
    'search' |
    'booking' |
    'dashboard' |
    'company' |
    'admin' |
    'conductor' |
    'accounts_manager'
  >('home');

  const [searchParams, setSearchParams] = useState({
    origin: '',
    destination: '',
    date: '',
  });

  const [selectedScheduleId, setSelectedScheduleId] = useState<string | null>(null);

  // Handle browser navigation
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      if (path === '/admin') setCurrentView('admin');
      else if (path === '/company') setCurrentView('company');
      else if (path === '/conductor') setCurrentView('conductor');
      else if (path === '/dashboard') setCurrentView('dashboard');
      else if (path.startsWith('/booking/')) setCurrentView('booking');
      else if (path === '/search') setCurrentView('search');
      else setCurrentView('home');
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleSearch = (origin: string, destination: string, date: string) => {
    setSearchParams({ origin, destination, date });
    setCurrentView('search');
    window.history.pushState({}, '', '/search/schedule');
  };

  const handleBook = (scheduleId: string) => {
    setSelectedScheduleId(scheduleId);
    setCurrentView('booking');
    window.history.pushState({}, '', `/booking/${scheduleId}`);
  };

  const navigateTo = (view: typeof currentView, path: string = '') => {
    setCurrentView(view);
    window.history.pushState({}, '', path || `/${view}`);
  };

  // Auto-redirect based on user role when accessing dashboard
  useEffect(() => {
    if (user && currentView === 'dashboard') {
      if (user.role === 'admin') navigateTo('admin', '/admin');
      else if (user.role === 'company') navigateTo('company', '/company');
      else if (user.role === 'conductor') navigateTo('conductor', '/conductor');
      else if (user.role === 'accounts_manager') navigateTo('accounts_manager', '/accounts_manager');
    }
  }, [user, currentView]);

  return (
    <div className="min-h-screen bg-[#F2F4F7] flex flex-col">
      <Navbar onShowAuth={(type) => setShowAuth(type)} />
      
      <main className="flex-1">
        <ErrorBoundary>
        {currentView === 'home' && <HomePage onSearch={handleSearch} />}
        {currentView === 'search' && (
          <SearchResults
            origin={searchParams.origin}
            destination={searchParams.destination}
            date={searchParams.date}
            onBack={() => navigateTo('home', '/')}
            onBook={handleBook}
            onShowAuth={() => setShowAuth('login')}
          />
        )}
        {currentView === 'booking' && selectedScheduleId && (
          <BookingFlow
            scheduleId={selectedScheduleId}
            onBack={() => navigateTo('search', '/search')}
            onComplete={() => {
              if (user?.role === 'admin') navigateTo('admin', '/admin');
              else if (user?.role === 'company') navigateTo('company', '/company');
              else if (user?.role === 'conductor') navigateTo('conductor', '/conductor');
              else if (user?.role === 'accounts_manager') navigateTo('accounts_manager', '/accounts_manager');
              else navigateTo('dashboard', '/dashboard');
            }}
          />
        )}
        {currentView === 'dashboard' && user && <UserDashboard />}
        {currentView === 'company' && user && <CompanyDashboard />}
        {currentView === 'admin' && user && <AdminDashboard />}
        {currentView === 'conductor' && user && <ConductorDashboard />}
        {currentView === 'accounts_manager' && user && <AccountsManagerDashboard />}
        </ErrorBoundary>
      </main>

      <Footer />

      {showAuth && <AuthModal type={showAuth} onClose={() => setShowAuth(null)} />}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
