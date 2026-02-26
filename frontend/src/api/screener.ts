import api from './client'
import type { ScreenerResponse } from '../types/screener'

export async function fetchTopGainers(params?: {
  market?: string
  period?: string
  limit?: number
}): Promise<ScreenerResponse> {
  const { data } = await api.get('/screener/top-gainers', { params })
  return data
}

export async function fetchTopLosers(params?: {
  market?: string
  period?: string
  limit?: number
}): Promise<ScreenerResponse> {
  const { data } = await api.get('/screener/top-losers', { params })
  return data
}

export async function fetchVolumeSpikes(params?: {
  market?: string
  min_ratio?: number
  limit?: number
}): Promise<ScreenerResponse> {
  const { data } = await api.get('/screener/volume-spikes', { params })
  return data
}

export async function fetchNewHighs(params?: {
  market?: string
  limit?: number
}): Promise<ScreenerResponse> {
  const { data } = await api.get('/screener/new-highs', { params })
  return data
}

export async function fetchMomentum(params?: {
  market?: string
  min_score?: number
  limit?: number
}): Promise<ScreenerResponse> {
  const { data } = await api.get('/screener/momentum', { params })
  return data
}
