import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import SearchPage from './pages/SearchPage'
import DetailPage from './pages/DetailPage'
import CartPage from './pages/CartPage'
import MinePage from './pages/MinePage'
import PricesPage from './pages/PricesPage'
import AdminPricePage from './pages/AdminPricePage'
import DataReportPage from './pages/DataReportPage'
import AdminQuotaPage from './pages/AdminQuotaPage'
import ProjectsPage from './pages/ProjectsPage'
import DevLogPage from './pages/DevLogPage'
import LoginPage from './pages/LoginPage'

function NotFoundPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center gap-4">
      <AlertTriangle size={48} className="text-amber-400" />
      <h1 className="text-white text-2xl font-bold">404</h1>
      <p className="text-slate-400">页面不存在</p>
    </div>
  )
}

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: string
}

function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  // 从 localStorage 获取登录信息
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')

  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (requiredRole && role !== requiredRole) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/detail/:quota_id" element={<DetailPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/prices" element={<PricesPage />} />
        <Route path="/mine" element={<MinePage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/admin/report" element={<ProtectedRoute requiredRole="admin"><DataReportPage /></ProtectedRoute>} />
        <Route path="/admin/quota" element={<ProtectedRoute requiredRole="admin"><AdminQuotaPage /></ProtectedRoute>} />
        <Route path="/admin/price" element={<ProtectedRoute requiredRole="admin"><AdminPricePage /></ProtectedRoute>} />
        <Route path="/devlog" element={<DevLogPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
