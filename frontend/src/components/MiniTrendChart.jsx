import ReactECharts from 'echarts-for-react'

export default function MiniTrendChart({ title, data, color = '#409eff', showXAxis = false, height = 220 }) {
  if (!data || data.length === 0) {
    return <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9aa0a6', fontSize: 12 }}>{title} 暂无数据</div>
  }

  const dates = data.map((item) => item.date)
  const values = data.map((item) => item.value)

  const option = {
    backgroundColor: 'transparent',
    title: { text: title, left: 'center', top: 0, textStyle: { color: '#9aa0a6', fontSize: 12, fontWeight: 500 } },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(26, 29, 35, 0.9)',
      borderColor: '#2a2e36',
      textStyle: { color: '#e8eaed', fontSize: 12 },
    },
    grid: { left: '5%', right: '5%', bottom: '5%', top: '20%', containLabel: true },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#2a2e36' } },
      axisLabel: {
        color: '#9aa0a6',
        fontSize: 10,
        interval: showXAxis ? Math.max(0, Math.floor(dates.length / 6) - 1) : 'auto',
      },
      show: showXAxis,   // ← 用 prop 控制
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLine: { show: false },
      axisLabel: { color: '#9aa0a6', fontSize: 10 },
      splitLine: { lineStyle: { color: '#2a2e36', type: 'dashed' } },
    },
    series: [
      {
        type: 'line',
        data: values,
        showSymbol: false,
        lineStyle: { width: 1.5, color },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: color + '40' }, { offset: 1, color: color + '00' }],
          },
        },
      },
    ],
  }

  return (
    <div style={{ width: '100%', height }}>
      <ReactECharts option={option} style={{ height: '100%', width: '100%' }} notMerge={true} />
    </div>
  )
}