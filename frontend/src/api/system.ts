import api from './client'

export interface SystemStatus {
  status: string
  data: {
    stocks: number
    daily_prices: number
    fundamentals: number
    disclosures: number
    news_articles: number
  }
  latest_dates: {
    prices: string | null
    fundamentals: string | null
  }
}

export interface SchedulerStatus {
  running: boolean
  jobs: {
    id: string
    next_run: string | null
    trigger: string
  }[]
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const { data } = await api.get('/system/status')
  return data
}

export async function fetchSchedulerStatus(): Promise<SchedulerStatus> {
  const { data } = await api.get('/system/scheduler')
  return data
}

function adminHeaders(key: string) {
  return { headers: { 'X-Admin-Key': key } }
}

export async function runJob(jobName: string, adminKey: string): Promise<{ status: string; job: string }> {
  const { data } = await api.post(`/system/run-job/${jobName}`, null, adminHeaders(adminKey))
  return data
}

export async function triggerSyncStocks(adminKey: string): Promise<void> {
  await api.post('/system/sync-stocks', null, adminHeaders(adminKey))
}

export async function triggerFetchPrices(adminKey: string): Promise<void> {
  await api.post('/system/fetch-prices', null, adminHeaders(adminKey))
}

export async function triggerBackfill(startDate: string, adminKey: string, endDate?: string): Promise<void> {
  await api.post('/system/backfill', null, {
    params: { start_date: startDate, end_date: endDate },
    ...adminHeaders(adminKey),
  })
}
