export interface NewsItem {
  id: number
  ticker: string | null
  title: string | null
  summary: string | null
  source: string | null
  url: string
  published_at: string | null
}

export interface NewsListResponse {
  items: NewsItem[]
  total: number
}
