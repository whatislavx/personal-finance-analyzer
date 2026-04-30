import { Outlet, Link, useNavigate, useLocation } from 'react-router';
import { useApp } from '../context/AppContext';
import { TrendingUp, LayoutDashboard, Activity, LogOut, ChevronRight, User } from 'lucide-react';
import { Footer } from './Footer';
import { useEffect } from 'react';

export function Layout() {
  const { user, logout, isAuthenticated, authLoading } = useApp();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/');
    }
  }, [authLoading, isAuthenticated, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path: string) => {
    if (path === '/app') {
      return location.pathname === '/app';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Top Navigation */}
      <nav className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-800 sticky top-0 z-50">
        <div className="w-full px-4 py-4 sm:px-6 lg:px-8 xl:px-10 2xl:px-14">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <Link to="/app" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <span className="text-xl">FinFlow</span>
              </Link>

              <div className="hidden md:flex items-center gap-1">
                <Link
                  to="/app"
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${isActive('/app')
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  Dashboard
                </Link>
                <Link
                  to="/app/analyses"
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${isActive('/app/analyses')
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`}
                >
                  <Activity className="w-4 h-4" />
                  Analyses
                </Link>
                <Link
                  to="/app/profile"
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${isActive('/app/profile')
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`}
                >
                  <User className="w-4 h-4" />
                  Profile
                </Link>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden sm:block text-sm text-slate-400">
                {user?.username}
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Breadcrumb */}
      <div className="w-full px-4 py-4 sm:px-6 lg:px-8 xl:px-10 2xl:px-14">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Link to="/app" className="hover:text-white transition-colors">
            Dashboard
          </Link>
          {location.pathname !== '/app' && (
            <>
              <ChevronRight className="w-4 h-4" />
              <span className="text-white">
                {location.pathname.includes('analyses') && 'Analyses'}
                {location.pathname.includes('results') && 'Analysis Results'}
                {location.pathname.includes('profile') && 'Profile'}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Main Content */}
      <main className="w-full px-4 pb-12 sm:px-6 lg:px-8 xl:px-10 2xl:px-14 min-h-[calc(100vh-7rem)]">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}
