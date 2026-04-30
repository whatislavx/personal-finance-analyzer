import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useApp } from '../context/AppContext';
import { motion } from 'motion/react';
import { TrendingUp, Shield, Zap, ArrowRight } from 'lucide-react';

export function Landing() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login, signup, isAuthenticated } = useApp();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isLogin) {
        await login(username || email, password);
      } else {
        await signup({
          username: username || email.split('@')[0],
          email,
          password,
        });
      }
      navigate('/app');
    } catch (e: any) {
      setError(e?.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-950 flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center p-12 text-white">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-7 h-7" />
            </div>
            <h1 className="text-3xl">FinFlow</h1>
          </div>

          <h2 className="text-5xl mb-6">
            Smart Financial<br />Analytics Platform
          </h2>

          <p className="text-xl text-slate-300 mb-12">
            Modernize expense tracking with live processing and clear financial insights
          </p>

          <div className="space-y-6">
            <motion.div
              className="flex items-start gap-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="w-10 h-10 bg-indigo-600/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <Zap className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h3 className="mb-1">Real-time Processing</h3>
                <p className="text-slate-400">Track analysis progress with live event streaming</p>
              </div>
            </motion.div>

            <motion.div
              className="flex items-start gap-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="w-10 h-10 bg-emerald-600/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <h3 className="mb-1">Smart Analytics</h3>
                <p className="text-slate-400">Automated expense categorization and insights</p>
              </div>
            </motion.div>

            <motion.div
              className="flex items-start gap-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              <div className="w-10 h-10 bg-purple-600/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <Shield className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h3 className="mb-1">Enterprise Ready</h3>
                <p className="text-slate-400">Secure, scalable infrastructure</p>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>

      {/* Right side - Auth Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800 rounded-2xl p-8 shadow-2xl">
            <div className="lg:hidden flex items-center gap-3 mb-8">
              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl text-white">FinFlow</h1>
            </div>

            <div className="flex gap-2 mb-8 bg-slate-800/50 rounded-lg p-1">
              <button
                onClick={() => setIsLogin(true)}
                className={`flex-1 py-2 px-4 rounded-md transition-all ${isLogin
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white'
                  }`}
              >
                Log in
              </button>
              <button
                onClick={() => setIsLogin(false)}
                className={`flex-1 py-2 px-4 rounded-md transition-all ${!isLogin
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-400 hover:text-white'
                  }`}
              >
                Sign up
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {!isLogin && (
                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Username
                  </label>
                  <div className="mb-2 text-xs text-slate-500">Example: johndoe</div>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all"
                    required={!isLogin}
                  />
                </div>
              )}

              <div>
                <label className="block text-sm text-slate-300 mb-2">
                  Email
                </label>
                <div className="mb-2 text-xs text-slate-500">Example: you@company.com</div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all"
                  required
                />
              </div>

              <div>
                <label className="block text-sm text-slate-300 mb-2">
                  Password
                </label>
                <div className="mb-2 text-xs text-slate-500">Example: at least 8 characters</div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all"
                  required
                />
              </div>

              {isLogin && (
                <div className="flex items-center justify-between text-sm">
                  <label className="flex items-center text-slate-400">
                    <input type="checkbox" className="mr-2 rounded" />
                    Remember me
                  </label>
                  <a href="#" className="text-indigo-400 hover:text-indigo-300 transition-colors">
                    Forgot password?
                  </a>
                </div>
              )}

              {error && (
                <div className="text-sm text-red-400 bg-red-900/20 border border-red-800/30 rounded-lg p-3">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white py-3 px-4 rounded-lg transition-all flex items-center justify-center gap-2 group"
              >
                {loading ? 'Please wait…' : isLogin ? 'Log in' : 'Create account'}
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
            </form>

            <p className="text-center text-sm text-slate-500 mt-6">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                {isLogin ? 'Sign up' : 'Log in'}
              </button>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
