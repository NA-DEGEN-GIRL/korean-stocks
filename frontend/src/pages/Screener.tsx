import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, BarChart3, Award, Zap } from 'lucide-react'
import {
  fetchTopGainers,
  fetchTopLosers,
  fetchVolumeSpikes,
  fetchNewHighs,
  fetchMomentum,
} from '../api/screener'
import type { ScreenerTab, ScreenerItem } from '../types/screener'

const TABS: { key: ScreenerTab; label: string; icon: typeof TrendingUp }[] = [
  { key: 'gainers', label: '급등주', icon: TrendingUp },
  { key: 'losers', label: '급락주', icon: TrendingDown },
  { key: 'volume', label: '거래량 급증', icon: BarChart3 },
  { key: 'highs', label: '신고가', icon: Award },
  { key: 'momentum', label: '모멘텀', icon: Zap },
]

export default function Screener() {
  const [tab, setTab] = useState<ScreenerTab>('gainers')
  const [market, setMarket] = useState<string>('ALL')
  const [period, setPeriod] = useState<string>('1d')
  const navigate = useNavigate()

  const marketParam = market === 'ALL' ? undefined : market

  const { data, isLoading, error } = useQuery({
    queryKey: ['screener', tab, marketParam, period],
    queryFn: () => {
      switch (tab) {
        case 'gainers':
          return fetchTopGainers({ market: marketParam, period, limit: 30 })
        case 'losers':
          return fetchTopLosers({ market: marketParam, period, limit: 30 })
        case 'volume':
          return fetchVolumeSpikes({ market: marketParam, limit: 30 })
        case 'highs':
          return fetchNewHighs({ market: marketParam, limit: 30 })
        case 'momentum':
          return fetchMomentum({ market: marketParam, min_score: 50, limit: 30 })
      }
    },
  })

  const showPeriod = tab === 'gainers' || tab === 'losers'

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">종목 스크리너</h1>
      <p className="text-gray-500 mb-6">조건에 맞는 종목을 발굴하세요</p>

      {/* 탭 */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === key
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* 필터 */}
      <div className="flex gap-2 mb-4">
        <div className="flex gap-1">
          {['ALL', 'KOSPI', 'KOSDAQ'].map((m) => (
            <button
              key={m}
              onClick={() => setMarket(m)}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                market === m
                  ? 'bg-slate-800 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {m === 'ALL' ? '전체' : m}
            </button>
          ))}
        </div>
        {showPeriod && (
          <div className="flex gap-1 ml-2">
            {[
              { value: '1d', label: '일간' },
              { value: '1w', label: '주간' },
              { value: '1m', label: '월간' },
            ].map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                  period === p.value
                    ? 'bg-slate-800 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 테이블 */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
            <p className="text-gray-400 text-sm">
              {tab === 'momentum' ? '모멘텀 점수 계산 중 (시간이 걸릴 수 있음)...' : '데이터 로딩 중...'}
            </p>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-500 text-sm">
            데이터를 불러올 수 없습니다. 백엔드를 확인해주세요.
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">
            조건에 맞는 종목이 없습니다. 데이터가 충분히 수집되었는지 확인하세요.
          </div>
        ) : (
          <>
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-gray-100 bg-gray-50">
                  <th className="px-4 py-3 font-medium w-8">#</th>
                  <th className="px-4 py-3 font-medium">종목</th>
                  <th className="px-4 py-3 font-medium">시장</th>
                  <th className="px-4 py-3 font-medium text-right">현재가</th>
                  <th className="px-4 py-3 font-medium text-right">등락률</th>
                  <th className="px-4 py-3 font-medium text-right">거래량</th>
                  {tab === 'volume' && (
                    <th className="px-4 py-3 font-medium text-right">거래량 배율</th>
                  )}
                  {tab === 'momentum' && (
                    <th className="px-4 py-3 font-medium text-right">모멘텀</th>
                  )}
                  <th className="px-4 py-3 font-medium text-right">시가총액</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item: ScreenerItem, idx: number) => (
                  <tr
                    key={item.ticker}
                    onClick={() => navigate(`/stocks/${item.ticker}`)}
                    className="border-b border-gray-50 hover:bg-blue-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 text-xs text-gray-400">{idx + 1}</td>
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-gray-900">{item.name}</div>
                      <div className="text-xs text-gray-400 font-mono">{item.ticker}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 text-xs rounded-full ${
                          item.market === 'KOSPI'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-purple-100 text-purple-700'
                        }`}
                      >
                        {item.market}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-mono">
                      {item.close?.toLocaleString('ko-KR')}원
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-mono font-medium">
                      <span
                        className={
                          item.change_pct > 0
                            ? 'text-red-600'
                            : item.change_pct < 0
                              ? 'text-blue-600'
                              : 'text-gray-500'
                        }
                      >
                        {item.change_pct > 0 ? '+' : ''}
                        {item.change_pct.toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-600">
                      {item.volume ? formatVolume(item.volume) : '-'}
                    </td>
                    {tab === 'volume' && (
                      <td className="px-4 py-3 text-right">
                        {item.volume_ratio ? (
                          <span className="inline-block px-2 py-0.5 text-xs font-bold rounded-full bg-orange-100 text-orange-700">
                            {item.volume_ratio.toFixed(1)}x
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                    )}
                    {tab === 'momentum' && (
                      <td className="px-4 py-3 text-right">
                        {item.momentum_score != null ? (
                          <MomentumBadge score={item.momentum_score} />
                        ) : (
                          '-'
                        )}
                      </td>
                    )}
                    <td className="px-4 py-3 text-sm text-right font-mono text-gray-500">
                      {item.market_cap ? formatMarketCap(item.market_cap) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="px-4 py-3 border-t border-gray-100 text-sm text-gray-500">
              총 {data.total}개 종목
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function MomentumBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? 'bg-red-100 text-red-700'
      : score >= 60
        ? 'bg-orange-100 text-orange-700'
        : score >= 40
          ? 'bg-yellow-100 text-yellow-700'
          : 'bg-gray-100 text-gray-600'

  return (
    <span className={`inline-block px-2 py-0.5 text-xs font-bold rounded-full ${color}`}>
      {score.toFixed(0)}
    </span>
  )
}

function formatVolume(vol: number): string {
  if (vol >= 1_000_000) return (vol / 1_000_000).toFixed(1) + 'M'
  if (vol >= 1_000) return (vol / 1_000).toFixed(0) + 'K'
  return vol.toString()
}

function formatMarketCap(value: number): string {
  const eok = value / 100_000_000
  if (eok >= 10000) return (eok / 10000).toFixed(1) + '조'
  if (eok >= 1) return Math.round(eok).toLocaleString('ko-KR') + '억'
  return '-'
}
