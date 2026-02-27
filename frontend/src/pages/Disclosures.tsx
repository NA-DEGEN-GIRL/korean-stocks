import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, ExternalLink, FileText } from 'lucide-react'
import { fetchDisclosures } from '../api/disclosures'

type ImpactFilter = '전체' | '긍정' | '부정' | '중립' | '미분석'
type DateRange = '1' | '7' | '30' | 'all'

const IMPACT_TABS: { key: ImpactFilter; label: string; color: string }[] = [
  { key: '전체', label: '전체', color: 'bg-gray-100 text-gray-700' },
  { key: '긍정', label: '긍정', color: 'bg-emerald-100 text-emerald-700' },
  { key: '부정', label: '부정', color: 'bg-red-100 text-red-700' },
  { key: '중립', label: '중립', color: 'bg-gray-100 text-gray-600' },
  { key: '미분석', label: '미분석', color: 'bg-yellow-100 text-yellow-700' },
]

const DATE_OPTIONS: { key: DateRange; label: string }[] = [
  { key: '1', label: '오늘' },
  { key: '7', label: '7일' },
  { key: '30', label: '30일' },
  { key: 'all', label: '전체' },
]

function getDateRange(range: DateRange): { start_date?: string; end_date?: string } {
  if (range === 'all') return {}
  const today = new Date()
  const end = today.toISOString().split('T')[0]
  const start = new Date(today)
  start.setDate(start.getDate() - (parseInt(range) - 1))
  return { start_date: start.toISOString().split('T')[0], end_date: end }
}

function impactBadge(impact: string | null) {
  if (!impact) {
    return <span className="inline-block w-2.5 h-2.5 rounded-full bg-gray-300" title="미분석" />
  }
  const colors: Record<string, string> = {
    '긍정': 'bg-emerald-500',
    '부정': 'bg-red-500',
    '중립': 'bg-gray-400',
  }
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${colors[impact] || 'bg-gray-300'}`} title={impact} />
}

export default function Disclosures() {
  const [impactFilter, setImpactFilter] = useState<ImpactFilter>('전체')
  const [dateRange, setDateRange] = useState<DateRange>('7')
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  const dateParams = useMemo(() => getDateRange(dateRange), [dateRange])

  const { data, isLoading, error } = useQuery({
    queryKey: ['disclosures', impactFilter, dateRange, search],
    queryFn: () =>
      fetchDisclosures({
        ai_impact: impactFilter === '전체' ? undefined : impactFilter,
        search: search || undefined,
        ...dateParams,
        limit: 200,
      }),
  })

  const sorted = useMemo(() => {
    if (!data?.items) return []
    return [...data.items].sort((a, b) => {
      // 긍정/부정 먼저, 중립/미분석 나중
      const priority = (impact: string | null) => {
        if (impact === '긍정' || impact === '부정') return 0
        if (impact === '중립') return 1
        return 2
      }
      const pa = priority(a.ai_impact)
      const pb = priority(b.ai_impact)
      if (pa !== pb) return pa - pb
      // 같은 우선순위면 날짜 최신순
      return (b.rcept_dt || '').localeCompare(a.rcept_dt || '')
    })
  }, [data])

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">공시</h1>
        <p className="text-gray-500 mt-1">DART 공시 및 AI 분석 결과</p>
      </div>

      {/* 필터 영역 */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-4">
        <div className="p-4 flex flex-wrap items-center gap-3">
          {/* AI 영향 탭 */}
          <div className="flex gap-1">
            {IMPACT_TABS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setImpactFilter(key)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  impactFilter === key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="w-px h-6 bg-gray-200 hidden sm:block" />

          {/* 기간 필터 */}
          <div className="flex gap-1">
            {DATE_OPTIONS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setDateRange(key)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  dateRange === key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="w-px h-6 bg-gray-200 hidden sm:block" />

          {/* 검색 */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="종목명 또는 코드 검색..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* 공시 목록 */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
            <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
            공시 데이터 로딩 중...
          </div>
        ) : error ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-red-500">
            데이터를 불러올 수 없습니다.
          </div>
        ) : sorted.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
            <FileText className="w-10 h-10 mx-auto mb-2 text-gray-300" />
            해당 조건의 공시가 없습니다.
          </div>
        ) : (
          <>
            <p className="text-sm text-gray-500 px-1">{sorted.length}건의 공시</p>
            {sorted.map((d) => (
              <DisclosureCard
                key={d.id}
                disclosure={d}
                onCorpClick={(ticker) => navigate(`/stocks/${ticker}`)}
              />
            ))}
          </>
        )}
      </div>
    </div>
  )
}

interface DisclosureCardProps {
  disclosure: {
    id: number
    ticker: string | null
    corp_name: string | null
    report_nm: string | null
    rcept_dt: string | null
    ai_summary: string | null
    ai_impact: string | null
    disclosure_url: string | null
  }
  onCorpClick: (ticker: string) => void
}

function DisclosureCard({ disclosure, onCorpClick }: DisclosureCardProps) {
  const { ticker, corp_name, report_nm, rcept_dt, ai_summary, ai_impact, disclosure_url } = disclosure

  const borderColor = ai_impact === '긍정'
    ? 'border-l-emerald-500'
    : ai_impact === '부정'
      ? 'border-l-red-500'
      : ai_impact === '중립'
        ? 'border-l-gray-400'
        : 'border-l-yellow-400'

  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm border-l-4 ${borderColor} p-4`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* 헤더: 영향 배지 + 기업명 + 날짜 */}
          <div className="flex items-center gap-2 mb-1.5">
            {impactBadge(ai_impact)}
            {ai_impact && (
              <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                ai_impact === '긍정' ? 'bg-emerald-100 text-emerald-700'
                : ai_impact === '부정' ? 'bg-red-100 text-red-700'
                : 'bg-gray-100 text-gray-600'
              }`}>
                {ai_impact}
              </span>
            )}
            {ticker ? (
              <button
                onClick={() => onCorpClick(ticker)}
                className="text-sm font-semibold text-gray-900 hover:text-blue-600 transition-colors"
              >
                {corp_name || ticker}
                <span className="text-gray-400 font-normal ml-1">({ticker})</span>
              </button>
            ) : (
              <span className="text-sm font-semibold text-gray-900">
                {corp_name || '(기업명 없음)'}
              </span>
            )}
            <span className="text-xs text-gray-400 ml-auto shrink-0">{rcept_dt}</span>
          </div>

          {/* AI 요약 */}
          {ai_summary ? (
            <p className="text-sm text-gray-700 mb-2 leading-relaxed">{ai_summary}</p>
          ) : (
            <p className="text-sm text-gray-400 italic mb-2">AI 분석 대기 중...</p>
          )}

          {/* 공시명 + DART 링크 */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 truncate">{report_nm}</span>
            {disclosure_url && (
              <a
                href={disclosure_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-0.5 shrink-0"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="w-3 h-3" />
                원문
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
