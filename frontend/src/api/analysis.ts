import api from './client'
import type { WhyMovingResponse } from '../types/analysis'

export async function fetchWhyMoving(ticker: string): Promise<WhyMovingResponse> {
  const { data } = await api.get(`/analysis/why-moving/${ticker}`)
  return data
}
