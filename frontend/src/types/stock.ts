export interface Stock {
  ticker: string
  name: string
  market: string
  sector: string | null
  is_active: boolean
  latest_price: number | null
  change_pct: number | null
}

export interface StockListResponse {
  items: Stock[]
  total: number
  page: number
  per_page: number
}

export interface Fundamentals {
  market_cap: number | null
  per: number | null
  pbr: number | null
  eps: number | null
  div_yield: number | null
}

export interface StockDetailResponse extends Stock {
  fundamentals: Fundamentals | null
}

export interface DailyPriceResponse {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  trading_value: number | null
  change_pct: number | null
}
