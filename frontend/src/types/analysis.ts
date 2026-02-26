export interface WhyMovingResponse {
  ticker: string
  name: string
  date: string
  price_change_pct: number | null
  volume_spike_ratio: number | null
  disclosures: WhyMovingDisclosure[]
  news: WhyMovingNews[]
  sector_comparison: SectorComparison
  summary: string
}

export interface WhyMovingDisclosure {
  report_nm: string | null
  rcept_dt: string | null
  disclosure_url: string | null
  flr_nm: string | null
}

export interface WhyMovingNews {
  title: string | null
  source: string | null
  url: string | null
  published_at: string | null
}

export interface SectorComparison {
  sector: string | null
  sector_avg_change: number | null
  sector_stock_count?: number
  sector_positive_ratio?: number
  is_sector_wide: boolean | null
}
