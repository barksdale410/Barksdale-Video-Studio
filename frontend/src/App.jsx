import React, { useState, useEffect } from 'react'
import { Film, Library, User, Settings, LogOut, Menu, X, Moon, Sun, Play, ChevronRight, Sparkles } from 'lucide-react'
import DirectorLibrary from './pages/DirectorLibrary'
import Generator from './pages/Generator'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Toast from './components/Toast'
import { AuthProvider, useAuth } from './contexts/AuthContext'

function AppContent() {
  const [currentPage, setCurrentPage] = useState('generator')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [darkMode, setDarkMode] = useState(true)
  const { user, logout } = useAuth()

  useEffect(() => {
    const saved = localStorage.getItem('darkMode')
    if (saved !== null) {
      setDarkMode(saved === 'true')
    }
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    localStorage.setItem('darkMode', darkMode)
  }, [darkMode])

  const navItems = [
    { id: 'generator', label: 'Generator', icon: Play },
    { id: 'library', label: 'Director Library', icon: Library },
    ...(user ? [{ id: 'dashboard', label: 'Dashboard', icon: User }] : [])
  ]

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div 
              className="flex items-center space-x-3 cursor-pointer"
              onClick={() => setCurrentPage('generator')}
            >
              <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
                <Film className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold gradient-text">BARKSDALE</h1>
                <p className="text-xs text-gray-500">VIDEO STUDIO</p>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-1">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all ${
                    currentPage === item.id
                      ? 'bg-orange-500/20 text-orange-400'
                      : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>

            {/* Right side */}
            <div className="flex items-center space-x-3">
              {/* Dark mode toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-xl hover:bg-gray-800 transition-colors"
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>

              {/* User menu */}
              {user ? (
                <div className="flex items-center space-x-3">
                  <div className="hidden sm:block text-right">
                    <p className="text-sm font-medium">{user.full_name || user.email}</p>
                    <p className="text-xs text-gray-500">{user.is_premium ? 'Premium' : 'Free'}</p>
                  </div>
                  <button
                    onClick={logout}
                    className="p-2 rounded-xl hover:bg-gray-800 transition-colors text-gray-400"
                  >
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setCurrentPage('auth')}
                  className="btn-primary !py-2 !px-4 text-sm"
                >
                  Sign In
                </button>
              )}

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-xl hover:bg-gray-800"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-800">
            <div className="px-4 py-4 space-y-2">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    setCurrentPage(item.id)
                    setMobileMenuOpen(false)
                  }}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                    currentPage === item.id
                      ? 'bg-orange-500/20 text-orange-400'
                      : 'text-gray-400 hover:bg-gray-800'
                  }`}
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* Main content */}
      <main className="pt-20 pb-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {currentPage === 'generator' && <Generator />}
        {currentPage === 'library' && <DirectorLibrary />}
        {currentPage === 'auth' && <Auth onSuccess={() => setCurrentPage('dashboard')} />}
        {currentPage === 'dashboard' && user && <Dashboard />}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8 px-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-gray-500 text-sm">
            © 2024 Barksdale Video Studio. AI-powered video generation.
          </p>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>Powered by OpenAI & Replicate</span>
            <span>•</span>
            <a href="#" className="hover:text-gray-300">Privacy</a>
            <span>•</span>
            <a href="#" className="hover:text-gray-300">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
