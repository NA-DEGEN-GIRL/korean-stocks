import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Settings as SettingsIcon, Play, Clock, Database, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react'
import {
  fetchSystemStatus,
  fetchSchedulerStatus,
  runJob,
  triggerSyncStocks,
  triggerFetchPrices,
  triggerBackfill,
} from '../api/system'

export default function Settings() {
  const { data: status, isLoading: statusLoading, refetch: refetchStatus } = useQuery({
    queryKey: ['system-status'],
    queryFn: fetchSystemStatus,
    refetchInterval: 10000,
  })

  const { data: scheduler, isLoading: schedLoading } = useQuery({
    queryKey: ['scheduler-status'],
    queryFn: fetchSchedulerStatus,
  })

  const [backfillStart, setBackfillStart] = useState('2025-12-01')
  const [jobMsg, setJobMsg] = useState<string | null>(null)
  const [adminKey, setAdminKey] = useState(() => sessionStorage.getItem('adminKey') || '')
  const [authError, setAuthError] = useState(false)

  const saveAdminKey = (key: string) => {
    setAdminKey(key)
    setAuthError(false)
    sessionStorage.setItem('adminKey', key)
  }

  const onAuthError = () => { setAuthError(true); setJobMsg(null) }

  const jobMutation = useMutation({
    mutationFn: (jobName: string) => runJob(jobName, adminKey),
    onSuccess: (data) => {
      setJobMsg(`${data.job} 시작됨`)
      setTimeout(() => { setJobMsg(null); refetchStatus() }, 5000)
    },
    onError: onAuthError,
  })

  const syncMutation = useMutation({
    mutationFn: () => triggerSyncStocks(adminKey),
    onSuccess: () => {
      setJobMsg('종목 동기화 시작됨')
      setTimeout(() => { setJobMsg(null); refetchStatus() }, 5000)
    },
    onError: onAuthError,
  })

  const pricesMutation = useMutation({
    mutationFn: () => triggerFetchPrices(adminKey),
    onSuccess: () => {
      setJobMsg('가격 수집 시작됨')
      setTimeout(() => { setJobMsg(null); refetchStatus() }, 5000)
    },
    onError: onAuthError,
  })

  const backfillMutation = useMutation({
    mutationFn: () => triggerBackfill(backfillStart, adminKey),
    onSuccess: () => {
      setJobMsg('백필 시작됨 (시간이 걸릴 수 있습니다)')
      setTimeout(() => { setJobMsg(null); refetchStatus() }, 10000)
    },
    onError: onAuthError,
  })

  return (
    <div className="p-6">
      <div className="flex items-center gap-2 mb-6">
        <SettingsIcon className="w-6 h-6 text-gray-600" />
        <h1 className="text-2xl font-bold text-gray-900">설정</h1>
      </div>

      {/* 관리자 인증 */}
      <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600 whitespace-nowrap">관리자 키</label>
        <input
          type="password"
          value={adminKey}
          onChange={(e) => saveAdminKey(e.target.value)}
          placeholder="ADMIN_KEY 입력"
          className="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {authError && (
          <span className="text-xs text-red-500 whitespace-nowrap">키가 올바르지 않습니다</span>
        )}
      </div>

      {/* 알림 */}
      {jobMsg && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700 flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          {jobMsg}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 시스템 상태 */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <Database className="w-5 h-5 text-gray-500" />
              시스템 상태
            </h2>
            <button
              onClick={() => refetchStatus()}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <RefreshCw className="w-4 h-4 text-gray-400" />
            </button>
          </div>
          {statusLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse h-8 bg-gray-100 rounded" />
              ))}
            </div>
          ) : status ? (
            <div className="space-y-3">
              <StatusRow label="종목 수" value={status.data.stocks.toLocaleString()} />
              <StatusRow label="일별 가격 데이터" value={status.data.daily_prices.toLocaleString()} />
              <StatusRow label="펀더멘탈" value={status.data.fundamentals.toLocaleString()} />
              <StatusRow label="공시" value={status.data.disclosures.toLocaleString()} />
              <StatusRow label="뉴스" value={status.data.news_articles.toLocaleString()} />
              <div className="pt-2 border-t border-gray-100">
                <StatusRow
                  label="최근 가격 날짜"
                  value={status.latest_dates.prices || '-'}
                />
                <StatusRow
                  label="최근 펀더멘탈 날짜"
                  value={status.latest_dates.fundamentals || '-'}
                />
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-400">상태를 가져올 수 없습니다.</p>
          )}
        </div>

        {/* 스케줄러 상태 */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-gray-500" />
            스케줄러
          </h2>
          {schedLoading ? (
            <div className="animate-pulse h-20 bg-gray-100 rounded" />
          ) : scheduler ? (
            <>
              <div className="flex items-center gap-2 mb-3">
                <span
                  className={`w-2 h-2 rounded-full ${scheduler.running ? 'bg-green-500' : 'bg-red-500'}`}
                />
                <span className="text-sm text-gray-600">
                  {scheduler.running ? '실행 중' : '중지됨'}
                </span>
              </div>
              <div className="space-y-2">
                {scheduler.jobs.map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between p-2 rounded-lg bg-gray-50"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-700">{job.id}</p>
                      <p className="text-xs text-gray-400">
                        다음 실행: {job.next_run ? new Date(job.next_run).toLocaleString('ko-KR') : '-'}
                      </p>
                    </div>
                    <button
                      onClick={() => jobMutation.mutate(job.id)}
                      disabled={jobMutation.isPending}
                      className="p-1.5 rounded-lg hover:bg-white transition-colors border border-gray-200"
                      title="수동 실행"
                    >
                      <Play className="w-3.5 h-3.5 text-gray-500" />
                    </button>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-400">스케줄러 상태를 가져올 수 없습니다.</p>
          )}
        </div>

        {/* 수동 작업 */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-4">
            <Play className="w-5 h-5 text-gray-500" />
            수동 작업
          </h2>
          <div className="space-y-3">
            <button
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <div className="text-left">
                <p className="text-sm font-medium text-gray-700">종목 목록 동기화</p>
                <p className="text-xs text-gray-400">KOSPI/KOSDAQ 전체 종목 갱신</p>
              </div>
              <Play className="w-4 h-4 text-gray-400" />
            </button>

            <button
              onClick={() => pricesMutation.mutate()}
              disabled={pricesMutation.isPending}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <div className="text-left">
                <p className="text-sm font-medium text-gray-700">오늘 가격 수집</p>
                <p className="text-xs text-gray-400">오늘 OHLCV 데이터 수집</p>
              </div>
              <Play className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* 백필 */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-4">
            <AlertCircle className="w-5 h-5 text-gray-500" />
            과거 데이터 백필
          </h2>
          <p className="text-xs text-gray-400 mb-3">
            지정한 날짜부터 오늘까지 모든 종목의 가격 데이터를 수집합니다. 시간이 오래 걸릴 수 있습니다.
          </p>
          <div className="flex gap-2">
            <input
              type="date"
              value={backfillStart}
              onChange={(e) => setBackfillStart(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={() => backfillMutation.mutate()}
              disabled={backfillMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {backfillMutation.isPending ? '실행 중...' : '시작'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-800">{value}</span>
    </div>
  )
}
