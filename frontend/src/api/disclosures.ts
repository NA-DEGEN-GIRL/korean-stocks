import api from './client'
import type { DisclosureListResponse } from '../types/disclosure'

export async function fetchDisclosures(params?: {
  ticker?: string
  start_date?: string
  end_date?: string
  ai_impact?: string
  search?: string
  limit?: number
}): Promise<DisclosureListResponse> {
  const { data } = await api.get('/disclosures', { params })
  return data
}

export async function triggerDisclosureFetch(ticker: string): Promise<void> {
  await api.post(`/disclosures/fetch/${ticker}`)
}
