import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import SearchPage from './pages/SearchPage'
import DetailPage from './pages/DetailPage'
import CartPage from './pages/CartPage'
import MinePage from './pages/MinePage'
import PricesPage from './pages/PricesPage'
import AdminPricePage from './pages/AdminPricePage'
import DataReportPage from './pages/DataReportPage'
import AdminQuotaPage from './pages/AdminQuotaPage'

function NotFoundPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center gap-4">
      <AlertTriangle size={48} className="text-amber-400" />
      <h1 className="text-white text-2xl font-bold">404</h1>
      <p className="text-slate-400">页面不存在</p>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/detail/:quota_id" element={<DetailPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/prices" element={<PricesPage />} />
        <Route path="/mine" element={<MinePage />} />
        <Route path="/admin/report" element={<DataReportPage />} />
        <Route path="/admin/quota" element={<AdminQuotaPage />} />
        <Route path="/admin/price" element={<AdminPricePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}
