import { useQuery } from '@tanstack/react-query'
import { fetchStocks, fetchStock, fetchStockPrices } from '../api/stocks'

export function useStocks(params: {
  market?: string
  search?: string
  page?: number
  per_page?: number
}) {
  return useQuery({
    queryKey: ['stocks', params],
    queryFn: () => fetchStocks(params),
  })
}

export function useStock(ticker: string) {
  return useQuery({
    queryKey: ['stock', ticker],
    queryFn: () => fetchStock(ticker),
    enabled: !!ticker,
  })
}

export function useStockPrices(
  ticker: string,
  params?: { start?: string; end?: string }
) {
  return useQuery({
    queryKey: ['stockPrices', ticker, params],
    queryFn: () => fetchStockPrices(ticker, params),
    enabled: !!ticker,
  })
}
