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

export async function runJob(jobName: string): Promise<{ status: string; job: string }> {
  const { data } = await api.post(`/system/run-job/${jobName}`)
  return data
}

export async function triggerSyncStocks(): Promise<void> {
  await api.post('/system/sync-stocks')
}

export async function triggerFetchPrices(): Promise<void> {
  await api.post('/system/fetch-prices')
}

export async function triggerBackfill(startDate: string, endDate?: string): Promise<void> {
  await api.post('/system/backfill', null, {
    params: { start_date: startDate, end_date: endDate },
  })
}
