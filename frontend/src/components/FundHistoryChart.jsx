import { useEffect, useState } from 'react'
import MiniTrendChart from './MiniTrendChart'

export default function FundHistoryChart({ code, name }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!code) return
    setLoading(true)
    fetch(`/api/fund/${code}`)
      .then((res) => res.json())
      .then((res) => setData(res || []))
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [code])

  return (
    <div style={{ marginTop: 20 }}>
      <h3 style={{ fontSize: 14, color: '#9aa0a6', margin: '0 0 10px 8px' }}>
        {name || code} 近一年净值走势
      </h3>
      {loading ? (
        <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9aa0a6' }}>加载中...</div>
      ) : (
        <MiniTrendChart title="" data={data} color="#14b143" />
      )}
    </div>
  )
}