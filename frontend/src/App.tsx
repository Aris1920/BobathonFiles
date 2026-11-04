import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ProfilePage from './pages/ProfilePage'
import ResultsPage from './pages/ResultsPage'

function HomePage() {
  const { isAuthenticated } = useAuth()
  if (isAuthenticated) return <Navigate to="/profile" replace />
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Career &amp; Debt Planner</h1>
          <nav className="flex gap-6 text-sm font-medium text-gray-600">
            <Link to="/login" className="hover:text-blue-600 transition-colors">Log In</Link>
            <Link to="/register" className="hover:text-blue-600 transition-colors">Register</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-20 text-center">
        <h2 className="text-4xl font-extrabold text-gray-900 mb-4">
          Find jobs. See your payoff date.
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-8">
          Enter your profile, upload your resume, and we'll match you to US job opportunities
          while projecting exactly how long it'll take to pay off your student loans at each
          salary tier.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            to="/register"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Get Started
          </Link>
          <Link
            to="/login"
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:border-gray-400 transition-colors"
          >
            Log In
          </Link>
        </div>
      </main>

      <section className="max-w-5xl mx-auto px-6 pb-20 grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { title: 'Profile & Loans', desc: 'Enter your major, skills, and student loan details.' },
          { title: 'Job Matching', desc: 'We search LinkedIn, Handshake, Indeed, and USAJobs.' },
          { title: 'Payoff Projection', desc: 'See months to debt-free at High, Mid, and Low salary tiers.' },
        ].map((card) => (
          <div key={card.title} className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-2">{card.title}</h3>
            <p className="text-sm text-gray-500">{card.desc}</p>
          </div>
        ))}
      </section>
    </div>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/results" element={<ResultsPage />} />
      </Route>
      {/* Catch-all: redirect unknown paths to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
