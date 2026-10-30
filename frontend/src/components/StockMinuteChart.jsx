import ReactECharts from 'echarts-for-react'
import { useEffect, useState } from 'react'

export default function StockMinuteChart({ symbol }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!symbol) return

    let isCancelled = false

    // 将请求封装成函数
    const fetchData = (isInitial = false) => {
      if (isInitial) setLoading(true)

      fetch(`/api/minute/${symbol}`)
        .then((res) => res.json())
        .then((res) => {
          if (!isCancelled) setData(res || [])
        })
        .catch(() => {
          if (!isCancelled && isInitial) setData([])
        })
        .finally(() => {
          if (!isCancelled && isInitial) setLoading(false)
        })
    }

    // 1. 首次加载
    fetchData(true)

    // 2. 开启 60 秒轮询（后续静默更新，不显示 loading 动画，避免图表闪烁）
    const timer = setInterval(() => fetchData(false), 60000)

    // 3. 组件卸载或切换股票时清理定时器，防止内存泄漏
    return () => {
      isCancelled = true
      clearInterval(timer)
    }
  }, [symbol])

  if (loading) {
    return (
      <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9aa0a6' }}>
        加载分时数据中...
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9aa0a6' }}>
        暂无当日分时数据（可能当前非交易时段）
      </div>
    )
  }

  const times = data.map((item) => item.time)
  const prices = data.map((item) => item.price)
  const avgPrices = data.map((item) => item.avg_price)
  const volumes = data.map((item) => {
    return {
      value: item.volume,
      itemStyle: { color: '#3a3f4b' }
    }
  })

  // 计算 Y 轴范围
  const maxPrice = Math.max(...prices, ...avgPrices)
  const minPrice = Math.min(...prices, ...avgPrices)
  const priceRange = maxPrice - minPrice

  const option = {
    backgroundColor: '#1a1d23',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(26, 29, 35, 0.9)',
      borderColor: '#2a2e36',
      textStyle: { color: '#e8eaed' },
    },
    legend: {
      data: ['价格', '均价'],
      textStyle: { color: '#9aa0a6' },
      top: 0,
    },
    grid: [
      { left: '10%', right: '8%', height: '60%', top: '10%' },
      { left: '10%', right: '8%', height: '20%', top: '75%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: times,
        axisLine: { lineStyle: { color: '#2a2e36' } },
        axisLabel: { color: '#9aa0a6' },
        splitLine: { show: false },
      },
      {
        type: 'category',
        gridIndex: 1,
        data: times,
        axisLine: { lineStyle: { color: '#2a2e36' } },
        axisLabel: { show: false },
        splitLine: { show: false },
      },
    ],
    yAxis: [
      {
        type: 'value',
        min: minPrice - (priceRange || 1) * 0.1,
        max: maxPrice + (priceRange || 1) * 0.1,
        axisLine: { lineStyle: { color: '#2a2e36' } },
        axisLabel: { color: '#9aa0a6' },
        splitLine: { lineStyle: { color: '#2a2e36', type: 'dashed' } },
      },
      {
        type: 'value',
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { color: '#9aa0a6' },
        axisLine: { lineStyle: { color: '#2a2e36' } },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '价格',
        type: 'line',
        data: prices,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#409eff' },
      },
      {
        name: '均价',
        type: 'line',
        data: avgPrices,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#e6a23c' },
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
      },
    ],
  }

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ fontSize: 14, color: '#9aa0a6', margin: '0 0 10px 8px' }}>当日分时线</h3>
      <div style={{ height: 320, width: '100%', borderRadius: 10, overflow: 'hidden' }}>
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
    </div>
  )
}