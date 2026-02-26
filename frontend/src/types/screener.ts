export interface ScreenerItem {
  ticker: string
  name: string
  market: string
  close: number
  change_pct: number
  volume: number
  volume_ratio: number | null
  momentum_score: number | null
  market_cap: number | null
}

export interface ScreenerResponse {
  items: ScreenerItem[]
  total: number
}

export type ScreenerTab = 'gainers' | 'losers' | 'volume' | 'highs' | 'momentum'
