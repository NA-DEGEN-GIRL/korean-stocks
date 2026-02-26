import api from './client'
import type { StockListResponse, StockDetailResponse, DailyPriceResponse } from '../types/stock'

export async function fetchStocks(params: {
  market?: string
  search?: string
  page?: number
  per_page?: number
}): Promise<StockListResponse> {
  const { data } = await api.get('/stocks', { params })
  return data
}

export async function fetchStock(ticker: string): Promise<StockDetailResponse> {
  const { data } = await api.get(`/stocks/${ticker}`)
  return data
}

export async function fetchStockPrices(
  ticker: string,
  params?: { start?: string; end?: string }
): Promise<DailyPriceResponse[]> {
  const { data } = await api.get(`/stocks/${ticker}/prices`, { params })
  return data
}
