import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, TrendingUp, TrendingDown, BarChart3, ArrowRight, ChevronUp, ChevronDown } from 'lucide-react'
import { useStocks } from '../hooks/useStocks'
import { fetchTopGainers, fetchTopLosers, fetchVolumeSpikes } from '../api/screener'

type SortKey = 'ticker' | 'name' | 'latest_price' | 'change_pct' | 'trading_value'
type SortDir = 'asc' | 'desc'

export default function Dashboard() {
  const [search, setSearch] = useState('')
  const [market, setMarket] = useState<string>('ALL')
  const [sortKey, setSortKey] = useState<SortKey>('change_pct')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const navigate = useNavigate()

  const { data, isLoading, error } = useStocks({
    search: search || undefined,
    market: market === 'ALL' ? undefined : market,
    page: 1,
    per_page: 30,
  })

  const { data: gainers } = useQuery({
    queryKey: ['dashboard-gainers'],
    queryFn: () => fetchTopGainers({ limit: 5 }),
  })

  const { data: losers } = useQuery({
    queryKey: ['dashboard-losers'],
    queryFn: () => fetchTopLosers({ limit: 5 }),
  })

  const { data: volumeSpikes } = useQuery({
    queryKey: ['dashboard-volume'],
    queryFn: () => fetchVolumeSpikes({ limit: 5 }),
  })

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
        <p className="text-gray-500 mt-1">KOSPI / KOSDAQ 종목 분석</p>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* 급등주 카드 */}
        <div
          onClick={() => navigate('/screener')}
          className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm cursor-pointer hover:border-red-200 transition-colors"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-red-50 rounded-lg">
                <TrendingUp className="w-5 h-5 text-red-500" />
              </div>
              <p className="text-sm font-medium text-gray-700">오늘의 급등주</p>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300" />
          </div>
          {gainers && gainers.items.length > 0 ? (
            <div className="space-y-1.5">
              {gainers.items.slice(0, 3).map((item) => (
                <div key={item.ticker} className="flex items-center justify-between">
                  <span className="text-sm text-gray-800 truncate flex-1">{item.name}</span>
                  <span className="text-sm font-bold text-red-600 ml-2">
                    +{item.change_pct.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">데이터 없음</p>
          )}
        </div>

        {/* 급락주 카드 */}
        <div
          onClick={() => navigate('/screener')}
          className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm cursor-pointer hover:border-blue-200 transition-colors"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-blue-50 rounded-lg">
                <TrendingDown className="w-5 h-5 text-blue-500" />
              </div>
              <p className="text-sm font-medium text-gray-700">오늘의 급락주</p>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300" />
          </div>
          {losers && losers.items.length > 0 ? (
            <div className="space-y-1.5">
              {losers.items.slice(0, 3).map((item) => (
                <div key={item.ticker} className="flex items-center justify-between">
                  <span className="text-sm text-gray-800 truncate flex-1">{item.name}</span>
                  <span className="text-sm font-bold text-blue-600 ml-2">
                    {item.change_pct.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">데이터 없음</p>
          )}
        </div>

        {/* 거래량 급증 카드 */}
        <div
          onClick={() => navigate('/screener')}
          className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm cursor-pointer hover:border-orange-200 transition-colors"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-orange-50 rounded-lg">
                <BarChart3 className="w-5 h-5 text-orange-500" />
              </div>
              <p className="text-sm font-medium text-gray-700">거래량 급증</p>
            </div>
            <ArrowRight className="w-4 h-4 text-gray-300" />
          </div>
          {volumeSpikes && volumeSpikes.items.length > 0 ? (
            <div className="space-y-1.5">
              {volumeSpikes.items.slice(0, 3).map((item) => (
                <div key={item.ticker} className="flex items-center justify-between">
                  <span className="text-sm text-gray-800 truncate flex-1">{item.name}</span>
                  <span className="text-sm font-bold text-orange-600 ml-2">
                    {item.volume_ratio ? `${item.volume_ratio.toFixed(1)}x` : '-'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">데이터 없음</p>
          )}
        </div>
      </div>

      {/* 검색 & 필터 */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-4 border-b border-gray-100 flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="종목명 또는 코드 검색..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex gap-1">
            {['ALL', 'KOSPI', 'KOSDAQ'].map((m) => (
              <button
                key={m}
                onClick={() => setMarket(m)}
                className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                  market === m
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {m === 'ALL' ? '전체' : m}
              </button>
            ))}
          </div>
        </div>

        {/* 종목 리스트 */}
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-8 text-center text-gray-400">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
              종목 데이터 로딩 중...
            </div>
          ) : error ? (
            <div className="p-8 text-center text-red-500">
              데이터를 불러올 수 없습니다. 백엔드 서버를 확인해주세요.
            </div>
          ) : !data || data.items.length === 0 ? (
            <div className="p-8 text-center text-gray-400">
              {search ? '검색 결과가 없습니다.' : '종목 데이터가 없습니다. 먼저 데이터를 수집해주세요.'}
            </div>
          ) : (
            <SortableTable
              items={data.items}
              sortKey={sortKey}
              sortDir={sortDir}
              onSort={(key) => {
                if (key === sortKey) {
                  setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
                } else {
                  setSortKey(key)
                  setSortDir(key === 'ticker' || key === 'name' ? 'asc' : 'desc')
                }
              }}
              onRowClick={(ticker) => navigate(`/stocks/${ticker}`)}
            />
          )}
        </div>

        {data && data.total > 0 && (
          <div className="p-4 border-t border-gray-100 text-sm text-gray-500">
            총 {data.total.toLocaleString()}개 종목
          </div>
        )}
      </div>
    </div>
  )
}

function formatTradingValue(v: number | null | undefined): string {
  if (v == null) return '-'
  if (v >= 1_000_000_000_000) return (v / 1_000_000_000_000).toFixed(1) + '조'
  if (v >= 100_000_000) return (v / 100_000_000).toFixed(0) + '억'
  if (v >= 10_000) return (v / 10_000).toFixed(0) + '만'
  return v.toLocaleString() + '원'
}

interface SortableTableProps {
  items: Array<{
    ticker: string
    name: string
    market: string
    latest_price: number | null
    change_pct: number | null
    trading_value?: number | null
  }>
  sortKey: SortKey
  sortDir: SortDir
  onSort: (key: SortKey) => void
  onRowClick: (ticker: string) => void
}

function SortableTable({ items, sortKey, sortDir, onSort, onRowClick }: SortableTableProps) {
  const sorted = useMemo(() => {
    return [...items].sort((a, b) => {
      const av = a[sortKey] ?? (sortDir === 'asc' ? Infinity : -Infinity)
      const bv = b[sortKey] ?? (sortDir === 'asc' ? Infinity : -Infinity)
      if (typeof av === 'string' && typeof bv === 'string') {
        return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
      }
      return sortDir === 'asc' ? (av as number) - (bv as number) : (bv as number) - (av as number)
    })
  }, [items, sortKey, sortDir])

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (col !== sortKey) return null
    return sortDir === 'asc' ? (
      <ChevronUp className="w-3 h-3 inline ml-0.5" />
    ) : (
      <ChevronDown className="w-3 h-3 inline ml-0.5" />
    )
  }

  const thClass = 'px-4 py-3 font-medium cursor-pointer hover:text-blue-600 select-none'

  return (
    <table className="w-full">
      <thead>
        <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
          <th className={thClass} onClick={() => onSort('ticker')}>
            종목코드<SortIcon col="ticker" />
          </th>
          <th className={thClass} onClick={() => onSort('name')}>
            종목명<SortIcon col="name" />
          </th>
          <th className="px-4 py-3 font-medium">시장</th>
          <th className={`${thClass} text-right`} onClick={() => onSort('latest_price')}>
            현재가<SortIcon col="latest_price" />
          </th>
          <th className={`${thClass} text-right`} onClick={() => onSort('change_pct')}>
            등락률<SortIcon col="change_pct" />
          </th>
          <th className={`${thClass} text-right`} onClick={() => onSort('trading_value')}>
            거래대금<SortIcon col="trading_value" />
          </th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((stock) => (
          <tr
            key={stock.ticker}
            onClick={() => onRowClick(stock.ticker)}
            className="border-b border-gray-50 hover:bg-blue-50 cursor-pointer transition-colors"
          >
            <td className="px-4 py-3 text-sm font-mono text-gray-600">{stock.ticker}</td>
            <td className="px-4 py-3 text-sm font-medium text-gray-900">{stock.name}</td>
            <td className="px-4 py-3">
              <span
                className={`inline-block px-2 py-0.5 text-xs rounded-full ${
                  stock.market === 'KOSPI'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-purple-100 text-purple-700'
                }`}
              >
                {stock.market}
              </span>
            </td>
            <td className="px-4 py-3 text-sm text-right font-mono">
              {stock.latest_price ? stock.latest_price.toLocaleString('ko-KR') + '원' : '-'}
            </td>
            <td className="px-4 py-3 text-sm text-right font-mono">
              {stock.change_pct != null ? (
                <span
                  className={
                    stock.change_pct > 0
                      ? 'text-red-600'
                      : stock.change_pct < 0
                        ? 'text-blue-600'
                        : 'text-gray-500'
                  }
                >
                  {stock.change_pct > 0 ? '+' : ''}
                  {stock.change_pct.toFixed(2)}%
                </span>
              ) : (
                '-'
              )}
            </td>
            <td className="px-4 py-3 text-sm text-right font-mono text-gray-600">
              {formatTradingValue(stock.trading_value)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
