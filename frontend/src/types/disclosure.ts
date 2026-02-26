export interface DisclosureItem {
  id: number
  ticker: string | null
  corp_name: string | null
  report_nm: string | null
  rcept_no: string
  flr_nm: string | null
  rcept_dt: string | null
  report_type: string | null
  disclosure_url: string | null
  ai_summary: string | null
  ai_impact: string | null
  ai_analyzed_at: string | null
}

export interface DisclosureListResponse {
  items: DisclosureItem[]
  total: number
}
