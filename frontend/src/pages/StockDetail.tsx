import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Building2, FileText, Newspaper, ExternalLink, RefreshCw, Lightbulb, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useStock, useStockPrices } from '../hooks/useStocks'
import { fetchDisclosures, triggerDisclosureFetch } from '../api/disclosures'
import { fetchNews, triggerNewsFetch } from '../api/news'
import { fetchWhyMoving } from '../api/analysis'
import PriceChart from '../components/charts/PriceChart'
import type { WhyMovingResponse } from '../types/analysis'

export default function StockDetail() {
  const { ticker } = useParams<{ ticker: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: stockData, isLoading: stockLoading } = useStock(ticker || '')
  const { data: prices, isLoading: pricesLoading } = useStockPrices(ticker || '')

  const { data: whyMoving, isLoading: whyLoading } = useQuery({
    queryKey: ['why-moving', ticker],
    queryFn: () => fetchWhyMoving(ticker!),
    enabled: !!ticker,
    retry: false,
  })

  const { data: disclosuresData, isLoading: discLoading } = useQuery({
    queryKey: ['disclosures', ticker],
    queryFn: () => fetchDisclosures({ ticker: ticker!, limit: 20 }),
    enabled: !!ticker,
  })

  const { data: newsData, isLoading: newsLoading } = useQuery({
    queryKey: ['news', ticker],
    queryFn: () => fetchNews({ ticker: ticker!, limit: 20 }),
    enabled: !!ticker,
  })

  const discFetchMutation = useMutation({
    mutationFn: () => triggerDisclosureFetch(ticker!),
    onSuccess: () => {
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['disclosures', ticker] }), 5000)
    },
  })

  const newsFetchMutation = useMutation({
    mutationFn: () => triggerNewsFetch(ticker!),
    onSuccess: () => {
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ['news', ticker] }), 8000)
    },
  })

  // Auto-fetch disclosures and news if empty
  useEffect(() => {
    if (ticker && disclosuresData && disclosuresData.items.length === 0 && !discFetchMutation.isPending) {
      discFetchMutation.mutate()
    }
  }, [ticker, disclosuresData])

  useEffect(() => {
    if (ticker && newsData && newsData.items.length === 0 && !newsFetchMutation.isPending) {
      newsFetchMutation.mutate()
    }
  }, [ticker, newsData])

  if (!ticker) return null

  const chartData = (prices || []).map((p) => ({
    time: p.date,
    open: p.open,
    high: p.high,
    low: p.low,
    close: p.close,
  }))

  const volumeData = (prices || []).map((p) => ({
    time: p.date,
    value: p.volume,
    color: p.change_pct != null && p.change_pct >= 0
      ? 'rgba(239, 68, 68, 0.3)'
      : 'rgba(59, 130, 246, 0.3)',
  }))

  const stock = stockData
  const fundamentals = stockData?.fundamentals

  return (
    <div className="p-6">
      {/* 헤더 */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div>
          {stockLoading ? (
            <div className="animate-pulse">
              <div className="h-7 w-40 bg-gray-200 rounded mb-1" />
              <div className="h-4 w-24 bg-gray-100 rounded" />
            </div>
          ) : stock ? (
            <>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900">{stock.name}</h1>
                <span className="text-lg text-gray-400 font-mono">{stock.ticker}</span>
                <span
                  className={`px-2 py-0.5 text-xs rounded-full ${
                    stock.market === 'KOSPI'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-purple-100 text-purple-700'
                  }`}
                >
                  {stock.market}
                </span>
              </div>
              {stock.sector && (
                <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                  <Building2 className="w-3.5 h-3.5" />
                  {stock.sector}
                </p>
              )}
            </>
          ) : (
            <p className="text-red-500">종목을 찾을 수 없습니다.</p>
          )}
        </div>
      </div>

      {/* 차트 */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-6">
        <h2 className="text-sm font-medium text-gray-500 mb-3">가격 차트</h2>
        {pricesLoading ? (
          <div className="flex items-center justify-center h-[400px]">
            <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
          </div>
        ) : (
          <PriceChart data={chartData} volumeData={volumeData} height={400} />
        )}
      </div>

      {/* 왜 오르나? 분석 */}
      {whyMoving && (whyMoving.price_change_pct !== null && Math.abs(whyMoving.price_change_pct) > 0) && (
        <WhyMovingPanel data={whyMoving} isLoading={whyLoading} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 투자 지표 */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <h2 className="text-sm font-medium text-gray-500 mb-3">투자 지표</h2>
          {stockLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse h-8 bg-gray-100 rounded" />
              ))}
            </div>
          ) : fundamentals ? (
            <div className="space-y-3">
              <FundamentalRow
                label="시가총액"
                value={
                  fundamentals.market_cap
                    ? formatMarketCap(fundamentals.market_cap)
                    : '-'
                }
              />
              <FundamentalRow
                label="PER"
                value={fundamentals.per ? fundamentals.per.toFixed(2) + '배' : '-'}
              />
              <FundamentalRow
                label="PBR"
                value={fundamentals.pbr ? fundamentals.pbr.toFixed(2) + '배' : '-'}
              />
              <FundamentalRow
                label="EPS"
                value={
                  fundamentals.eps
                    ? fundamentals.eps.toLocaleString('ko-KR') + '원'
                    : '-'
                }
              />
              <FundamentalRow
                label="배당수익률"
                value={
                  fundamentals.div_yield
                    ? fundamentals.div_yield.toFixed(2) + '%'
                    : '-'
                }
              />
            </div>
          ) : (
            <p className="text-sm text-gray-400">투자 지표 데이터가 없습니다.</p>
          )}
        </div>

        {/* 공시 */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-gray-500 flex items-center gap-1.5">
              <FileText className="w-4 h-4" />
              최근 공시
            </h2>
            <button
              onClick={() => discFetchMutation.mutate()}
              disabled={discFetchMutation.isPending}
              className="p-1 rounded hover:bg-gray-100 transition-colors"
              title="공시 새로고침"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-gray-400 ${discFetchMutation.isPending ? 'animate-spin' : ''}`} />
            </button>
          </div>
          {discLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse h-10 bg-gray-100 rounded" />
              ))}
            </div>
          ) : disclosuresData && disclosuresData.items.length > 0 ? (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {disclosuresData.items.map((d) => (
                <a
                  key={d.rcept_no}
                  href={d.disclosure_url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-2 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100"
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 truncate">{d.report_nm}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-gray-400">{d.rcept_dt}</span>
                        <span className="text-xs text-gray-400">{d.flr_nm}</span>
                      </div>
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-gray-300 shrink-0 mt-0.5" />
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">
              {discFetchMutation.isPending ? '공시 데이터를 가져오는 중...' : '공시 데이터가 없습니다.'}
            </p>
          )}
        </div>

        {/* 뉴스 */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-gray-500 flex items-center gap-1.5">
              <Newspaper className="w-4 h-4" />
              관련 뉴스
            </h2>
            <button
              onClick={() => newsFetchMutation.mutate()}
              disabled={newsFetchMutation.isPending}
              className="p-1 rounded hover:bg-gray-100 transition-colors"
              title="뉴스 새로고침"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-gray-400 ${newsFetchMutation.isPending ? 'animate-spin' : ''}`} />
            </button>
          </div>
          {newsLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse h-10 bg-gray-100 rounded" />
              ))}
            </div>
          ) : newsData && newsData.items.length > 0 ? (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {newsData.items.map((n) => (
                <a
                  key={n.id}
                  href={n.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-2 rounded-lg hover:bg-gray-50 transition-colors border border-gray-100"
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 truncate">{n.title}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-blue-500">{n.source}</span>
                        <span className="text-xs text-gray-400">
                          {n.published_at ? formatDate(n.published_at) : ''}
                        </span>
                      </div>
                    </div>
                    <ExternalLink className="w-3.5 h-3.5 text-gray-300 shrink-0 mt-0.5" />
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">
              {newsFetchMutation.isPending ? '뉴스를 가져오는 중...' : '뉴스 데이터가 없습니다.'}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function WhyMovingPanel({ data, isLoading }: { data: WhyMovingResponse; isLoading: boolean }) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 mb-6">
        <div className="animate-pulse h-20 bg-gray-100 rounded" />
      </div>
    )
  }

  const change = data.price_change_pct
  const isUp = change !== null && change > 0

  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-200 shadow-sm p-5 mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="w-5 h-5 text-amber-600" />
        <h2 className="text-base font-semibold text-amber-900">왜 {isUp ? '오르나' : '내리나'}?</h2>
      </div>

      {/* 요약 */}
      <p className="text-sm text-gray-800 mb-4 leading-relaxed">{data.summary}</p>

      {/* 핵심 지표 */}
      <div className="flex gap-3 flex-wrap mb-4">
        {change !== null && (
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg ${
            isUp ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'
          }`}>
            {isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span className="text-sm font-bold">{isUp ? '+' : ''}{change.toFixed(2)}%</span>
          </div>
        )}
        {data.volume_spike_ratio !== null && data.volume_spike_ratio > 1.5 && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-orange-100 text-orange-700">
            <BarChart3 className="w-4 h-4" />
            <span className="text-sm font-bold">거래량 {data.volume_spike_ratio.toFixed(1)}x</span>
          </div>
        )}
        {data.sector_comparison.is_sector_wide && (
          <div className="px-3 py-1.5 rounded-lg bg-purple-100 text-purple-700 text-sm font-medium">
            섹터 전체 상승 ({data.sector_comparison.sector})
          </div>
        )}
      </div>

      {/* 공시/뉴스 요약 */}
      {(data.disclosures.length > 0 || data.news.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.disclosures.length > 0 && (
            <div className="bg-white/60 rounded-lg p-3">
              <div className="text-xs font-medium text-gray-500 mb-1.5 flex items-center gap-1">
                <FileText className="w-3 h-3" /> 관련 공시 ({data.disclosures.length})
              </div>
              {data.disclosures.slice(0, 3).map((d, i) => (
                <a
                  key={i}
                  href={d.disclosure_url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-gray-700 truncate hover:text-blue-600 py-0.5"
                >
                  {d.report_nm}
                </a>
              ))}
            </div>
          )}
          {data.news.length > 0 && (
            <div className="bg-white/60 rounded-lg p-3">
              <div className="text-xs font-medium text-gray-500 mb-1.5 flex items-center gap-1">
                <Newspaper className="w-3 h-3" /> 관련 뉴스 ({data.news.length})
              </div>
              {data.news.slice(0, 3).map((n, i) => (
                <a
                  key={i}
                  href={n.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-xs text-gray-700 truncate hover:text-blue-600 py-0.5"
                >
                  {n.title}
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function FundamentalRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-gray-50">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900">{value}</span>
    </div>
  )
}

function formatMarketCap(value: number): string {
  const eok = value / 100_000_000
  if (eok >= 10000) {
    return (eok / 10000).toFixed(1) + '조원'
  }
  return Math.round(eok).toLocaleString('ko-KR') + '억원'
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${month}.${day} ${hours}:${minutes}`
}
