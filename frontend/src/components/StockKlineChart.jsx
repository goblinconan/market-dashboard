import ReactECharts from 'echarts-for-react'

export default function StockKlineChart({ data }) {
  if (!data || data.length === 0) return null

  // 截取最近 60 个交易日，并过滤掉无效数据
  const recent = data.filter(item => item && item.close).slice(-60)

  if (recent.length === 0) return null

  const dates = recent.map((item) => item.date)
  // 容错：如果后端没给 open/high/low，用 close 代替，保证图能画出来
  const values = recent.map((item) => [
    item.open != null ? item.open : item.close,
    item.close,
    item.low != null ? item.low : item.close,
    item.high != null ? item.high : item.close,
  ])
  
  const ma5 = recent.map((item) => item.ma5)
  const ma20 = recent.map((item) => item.ma20)
  const ma60 = recent.map((item) => item.ma60)
  
  const volumes = recent.map((item) => {
    return {
      value: item.volume,
      itemStyle: { color: item.close > (item.open || item.close) ? '#ef232a' : '#14b143' },
    }
  })

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
      data: ['日K', 'MA5', 'MA20', 'MA60'],
      textStyle: { color: '#9aa0a6' },
      top: 0,
    },
    grid: [
      { left: '10%', right: '8%', height: '55%', top: '10%' }, // K线区域
      { left: '10%', right: '8%', height: '15%', top: '75%' }, // 成交量区域
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        scale: true,
        axisLine: { lineStyle: { color: '#2a2e36' } },
        axisLabel: { color: '#9aa0a6' },
        splitLine: { show: false },
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        axisLine: { lineStyle: { color: '#2a2e36' } },
        axisLabel: { show: false },
        splitLine: { show: false },
      },
    ],
    yAxis: [
      {
        scale: true,
        splitArea: { show: false },
        axisLine: { lineStyle: { color: '#2a2e36' } },
        axisLabel: { color: '#9aa0a6' },
        splitLine: { lineStyle: { color: '#2a2e36', type: 'dashed' } },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { color: '#9aa0a6' },
        axisLine: { lineStyle: { color: '#2a2e36' } },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100,
      },
    ],
    series: [
      {
        name: '日K',
        type: 'candlestick',
        data: values,
        itemStyle: {
          color: '#ef232a', // 阳线
          color0: '#14b143', // 阴线
          borderColor: '#ef232a',
          borderColor0: '#14b143',
        },
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        smooth: true,
        showSymbol: false,
        lineStyle: { opacity: 0.8, width: 1, color: '#f4b400' },
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20,
        smooth: true,
        showSymbol: false,
        lineStyle: { opacity: 0.8, width: 1, color: '#4285f4' },
      },
      {
        name: 'MA60',
        type: 'line',
        data: ma60,
        smooth: true,
        showSymbol: false,
        lineStyle: { opacity: 0.8, width: 1, color: '#db4437' },
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
      <h3 style={{ fontSize: 14, color: '#9aa0a6', margin: '0 0 10px 8px' }}>近 60 日 K 线</h3>
      <div style={{ height: 400, width: '100%', borderRadius: 10, overflow: 'hidden' }}>
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
    </div>
  )
}