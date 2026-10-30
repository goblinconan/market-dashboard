import MiniTrendChart from './MiniTrendChart'

export default function GlobalIndicesChart({ name, dataMap }) {
  const data = dataMap?.[name] || []
  if (!name) return null

  return (
    <div style={{ marginTop: 20 }}>
      <h3 style={{ fontSize: 14, color: '#9aa0a6', margin: '0 0 10px 8px' }}>
        {name} 近一年走势
      </h3>
      {data.length > 0 ? (
        <MiniTrendChart title="" data={data} color="#4285f4" />
      ) : (
        <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9aa0a6' }}>
          暂无历史数据
        </div>
      )}
    </div>
  )
}