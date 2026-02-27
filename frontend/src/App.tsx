import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import StockDetail from './pages/StockDetail'
import Screener from './pages/Screener'
import WeeklyDiscovery from './pages/WeeklyDiscovery'
import Disclosures from './pages/Disclosures'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/stocks/:ticker" element={<StockDetail />} />
        <Route path="/screener" element={<Screener />} />
        <Route path="/weekly" element={<WeeklyDiscovery />} />
        <Route path="/disclosures" element={<Disclosures />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}
