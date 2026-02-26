import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, Search, TrendingUp, BarChart3, Settings } from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '대시보드' },
  { to: '/screener', icon: Search, label: '종목 스크리너' },
  { to: '/weekly', icon: TrendingUp, label: '주간 발굴' },
  { to: '/settings', icon: Settings, label: '설정' },
]

export default function Layout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-60 bg-slate-900 text-white flex flex-col shrink-0">
        <div className="p-5 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-400" />
            <h1 className="text-lg font-bold">Stock Analyzer</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">KOSPI / KOSDAQ 분석</p>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-700">
          <p className="text-xs text-slate-500">v0.5.0</p>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
