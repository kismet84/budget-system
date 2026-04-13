import { BrowserRouter, Routes, Route } from 'react-router-dom'
import SearchPage from './pages/SearchPage'
import DetailPage from './pages/DetailPage'
import CartPage from './pages/CartPage'
import MinePage from './pages/MinePage'
import PricesPage from './pages/PricesPage'
import AdminPricePage from './pages/AdminPricePage'
import DataReportPage from './pages/DataReportPage'
import AdminQuotaPage from './pages/AdminQuotaPage'

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
      </Routes>
    </BrowserRouter>
  )
}
