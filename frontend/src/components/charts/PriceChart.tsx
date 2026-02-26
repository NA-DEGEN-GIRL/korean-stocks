import { useEffect, useRef } from 'react'
import {
  createChart,
  type IChartApi,
  ColorType,
  CandlestickSeries,
  HistogramSeries,
} from 'lightweight-charts'

interface CandleData {
  time: string
  open: number
  high: number
  low: number
  close: number
}

interface VolumeData {
  time: string
  value: number
  color: string
}

interface PriceChartProps {
  data: CandleData[]
  volumeData?: VolumeData[]
  height?: number
}

export default function PriceChart({
  data,
  volumeData,
  height = 400,
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: '#e0e0e0',
      },
      timeScale: {
        borderColor: '#e0e0e0',
        timeVisible: false,
      },
      localization: {
        priceFormatter: (price: number) =>
          price.toLocaleString('ko-KR') + '원',
      },
    })

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#ef4444',
      downColor: '#3b82f6',
      borderDownColor: '#3b82f6',
      borderUpColor: '#ef4444',
      wickDownColor: '#3b82f6',
      wickUpColor: '#ef4444',
    })
    candleSeries.setData(data)

    if (volumeData && volumeData.length > 0) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      })
      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      })
      volumeSeries.setData(volumeData)
    }

    chart.timeScale().fitContent()
    chartRef.current = chart

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
      chartRef.current = null
    }
  }, [data, volumeData, height])

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg"
        style={{ height }}
      >
        <p className="text-gray-400">차트 데이터가 없습니다</p>
      </div>
    )
  }

  return <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />
}
