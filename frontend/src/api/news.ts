import api from './client'
import type { NewsListResponse } from '../types/news'

export async function fetchNews(params?: {
  ticker?: string
  limit?: number
}): Promise<NewsListResponse> {
  const { data } = await api.get('/news', { params })
  return data
}

export async function triggerNewsFetch(ticker: string): Promise<void> {
  await api.post(`/news/fetch/${ticker}`)
}
