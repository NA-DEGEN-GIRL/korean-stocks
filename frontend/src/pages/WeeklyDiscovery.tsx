import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, BarChart3, Award, Zap } from 'lucide-react'
import { fetchTopGainers, fetchTopLosers, fetchVolumeSpikes, fetchNewHighs, fetchMomentum } from '../api/screener'

export default function WeeklyDiscovery() {
  const navigate = useNavigate()

  const { data: gainers } = useQuery({
    queryKey: ['discovery-gainers'],
    queryFn: () => fetchTopGainers({ period: '1w', limit: 10 }),
  })

  const { data: losers } = useQuery({
    queryKey: ['discovery-losers'],
    queryFn: () => fetchTopLosers({ period: '1w', limit: 10 }),
  })

  const { data: volume } = useQuery({
    queryKey: ['discovery-volume'],
    queryFn: () => fetchVolumeSpikes({ limit: 10 }),
  })

  const { data: highs } = useQuery({
    queryKey: ['discovery-highs'],
    queryFn: () => fetchNewHighs({ limit: 10 }),
  })

  const { data: momentum } = useQuery({
    queryKey: ['discovery-momentum'],
    queryFn: () => fetchMomentum({ min_score: 50, limit: 10 }),
  })

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">주간 기업 발굴</h1>
      <p className="text-gray-500 mb-6">이번 주 눈에 띄는 종목들을 한눈에 확인하세요</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 주간 급등주 */}
        <DiscoveryCard
          title="주간 급등주"
          icon={<TrendingUp className="w-5 h-5 text-red-500" />}
          items={gainers?.items}
          renderValue={(item) => (
            <span className="text-sm font-bold text-red-600">
              +{item.change_pct.toFixed(1)}%
            </span>
          )}
          onItemClick={(ticker) => navigate(`/stocks/${ticker}`)}
          emptyText="주간 데이터가 부족합니다. 백필을 실행해주세요."
        />

        {/* 주간 급락주 */}
        <DiscoveryCard
          title="주간 급락주"
          icon={<TrendingDown className="w-5 h-5 text-blue-500" />}
          items={losers?.items}
          renderValue={(item) => (
            <span className="text-sm font-bold text-blue-600">
              {item.change_pct.toFixed(1)}%
            </span>
          )}
          onItemClick={(ticker) => navigate(`/stocks/${ticker}`)}
          emptyText="주간 데이터가 부족합니다."
        />

        {/* 거래량 급증 */}
        <DiscoveryCard
          title="거래량 급증"
          icon={<BarChart3 className="w-5 h-5 text-orange-500" />}
          items={volume?.items}
          renderValue={(item) => (
            <span className="text-sm font-bold text-orange-600">
              {item.volume_ratio ? `${item.volume_ratio.toFixed(1)}x` : '-'}
            </span>
          )}
          onItemClick={(ticker) => navigate(`/stocks/${ticker}`)}
          emptyText="거래량 급증 종목이 없습니다."
        />

        {/* 52주 신고가 */}
        <DiscoveryCard
          title="52주 신고가"
          icon={<Award className="w-5 h-5 text-yellow-500" />}
          items={highs?.items}
          renderValue={(item) => (
            <span className="text-sm font-bold text-red-600">
              +{item.change_pct.toFixed(1)}%
            </span>
          )}
          onItemClick={(ticker) => navigate(`/stocks/${ticker}`)}
          emptyText="신고가 종목이 없습니다."
        />

        {/* 모멘텀 */}
        <DiscoveryCard
          title="모멘텀 상위"
          icon={<Zap className="w-5 h-5 text-purple-500" />}
          items={momentum?.items}
          renderValue={(item) => (
            <span className={`text-sm font-bold px-2 py-0.5 rounded-full ${
              (item.momentum_score ?? 0) >= 70
                ? 'bg-red-100 text-red-700'
                : 'bg-orange-100 text-orange-700'
            }`}>
              {item.momentum_score?.toFixed(0) ?? '-'}
            </span>
          )}
          onItemClick={(ticker) => navigate(`/stocks/${ticker}`)}
          emptyText="모멘텀 데이터가 부족합니다. 백필을 실행해주세요."
        />
      </div>
    </div>
  )
}

interface DiscoveryCardProps {
  title: string
  icon: React.ReactNode
  items?: { ticker: string; name: string; market: string; change_pct: number; volume_ratio: number | null; momentum_score: number | null }[]
  renderValue: (item: { change_pct: number; volume_ratio: number | null; momentum_score: number | null }) => React.ReactNode
  onItemClick: (ticker: string) => void
  emptyText: string
}

function DiscoveryCard({ title, icon, items, renderValue, onItemClick, emptyText }: DiscoveryCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-gray-100">
        {icon}
        <h2 className="text-base font-semibold text-gray-800">{title}</h2>
        {items && items.length > 0 && (
          <span className="ml-auto text-xs text-gray-400">{items.length}개</span>
        )}
      </div>
      {items && items.length > 0 ? (
        <div className="divide-y divide-gray-50">
          {items.map((item, idx) => (
            <div
              key={item.ticker}
              onClick={() => onItemClick(item.ticker)}
              className="flex items-center px-5 py-3 hover:bg-blue-50 cursor-pointer transition-colors"
            >
              <span className="text-xs text-gray-400 w-6">{idx + 1}</span>
              <div className="flex-1 min-w-0">
                <span className="text-sm font-medium text-gray-900">{item.name}</span>
                <span className="text-xs text-gray-400 ml-2 font-mono">{item.ticker}</span>
              </div>
              <span className={`text-xs px-1.5 py-0.5 rounded ${
                item.market === 'KOSPI' ? 'bg-blue-50 text-blue-600' : 'bg-purple-50 text-purple-600'
              } mr-3`}>
                {item.market}
              </span>
              {renderValue(item)}
            </div>
          ))}
        </div>
      ) : (
        <div className="px-5 py-8 text-center text-sm text-gray-400">{emptyText}</div>
      )}
    </div>
  )
}
