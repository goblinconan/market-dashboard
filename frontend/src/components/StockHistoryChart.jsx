import { useEffect, useState } from 'react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis, YAxis,
} from 'recharts';
import StockMinuteChart from './StockMinuteChart.jsx'; // 引入分时图组件

export default function StockHistoryChart({ symbol, name, onQuery, onNameResolved }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [inputValue, setInputValue] = useState('')

  useEffect(() => {
    if (!symbol) return
    let cancelled = false
    setLoading(true)
    setError(null)

    fetch(`/api/history/${symbol}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((res) => {
        if (!cancelled) {
          if (Array.isArray(res)) {
            setData(res)
          } else {
            setData(res.data || [])
            if (res.name && !res.name.startsWith('sh') && !res.name.startsWith('sz') && res.name !== symbol && onNameResolved) {
              onNameResolved(res.name)
            }
          }
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e.message)
          setData([])
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [symbol, onNameResolved])

  const handleSubmit = (e) => {
    e.preventDefault()
    const v = inputValue.trim()
    if (!v) return
    onQuery(v)
    setInputValue('')
  }

  let displayName = name
  if (!displayName || displayName === symbol || displayName === `sh${symbol}` || displayName === `sz${symbol}`) {
    displayName = symbol
  }
  const titleText = displayName !== symbol ? `${displayName}（${symbol}）` : symbol

  return (
    <section style={{ marginTop: 32 }}>
      <div style={styles.headerRow}>
        <h2 style={styles.sectionTitle}>{titleText} 历史走势</h2>
        <form onSubmit={handleSubmit} style={styles.form}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="输入代码，如 000651 或 sh600188"
            style={styles.input}
          />
          <button type="submit" style={styles.button}>查询</button>
        </form>
      </div>

      {loading && <p style={{ color: '#9aa0a6' }}>加载中...</p>}
      {error && <p style={{ color: '#db4437' }}>加载失败：{error}</p>}
      
      {/* 只有在没有错误的情况下才渲染图表组件 */}
      {!error && (
        <>
          {/* 上方：新增的当日分时线 */}
          <StockMinuteChart symbol={symbol} />

          {/* 下方：原有的一年走势线 */}
          {!loading && data.length > 0 && (
            <>
              <h3 style={{ fontSize: 14, color: '#9aa0a6', margin: '20px 0 10px 8px' }}>近一年前复权走势</h3>
              <div style={styles.chartWrap}>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={data} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
                    <CartesianGrid stroke="#2a2e36" strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: '#9aa0a6', fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: '#2a2e36' }}
                      minTickGap={40}
                    />
                    <YAxis
                      yAxisId="price"
                      orientation="left"
                      tick={{ fill: '#9aa0a6', fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: '#2a2e36' }}
                      domain={['auto', 'auto']}
                      label={{ value: '价格 (元)', angle: -90, position: 'insideLeft', fill: '#9aa0a6', fontSize: 11 }}
                    />
                    <YAxis
                      yAxisId="volume"
                      orientation="right"
                      tick={{ fill: '#9aa0a6', fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: '#2a2e36' }}
                      tickFormatter={(v) => `${(v / 10000).toFixed(0)}万`}
                      label={{ value: '成交量 (手)', angle: 90, position: 'insideRight', fill: '#9aa0a6', fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{ background: '#1a1d23', border: '1px solid #2a2e36', borderRadius: 8, color: '#e8eaed' }}
                      labelStyle={{ color: '#9aa0a6' }}
                    />
                    <Legend wrapperStyle={{ color: '#9aa0a6', fontSize: 12 }} />

                    <Bar yAxisId="volume" dataKey="volume" name="成交量" fill="#3a3f4b" barSize={4} />

                    <Line yAxisId="price" type="monotone" dataKey="close" name="收盘价" stroke="#e8eaed" dot={false} strokeWidth={1.6} />
                    <Line yAxisId="price" type="monotone" dataKey="ma5" name="MA5" stroke="#f4b400" dot={false} strokeWidth={1.2} connectNulls />
                    <Line yAxisId="price" type="monotone" dataKey="ma20" name="MA20" stroke="#4285f4" dot={false} strokeWidth={1.2} connectNulls />
                    <Line yAxisId="price" type="monotone" dataKey="ma60" name="MA60" stroke="#db4437" dot={false} strokeWidth={1.2} connectNulls />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </>
      )}
    </section>
  )
}

const styles = {
  headerRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 10 },
  sectionTitle: { fontSize: 15, fontWeight: 500, color: '#9aa0a6', margin: 0, letterSpacing: 0.5 },
  form: { display: 'flex', gap: 8, alignItems: 'center' },
  input: { background: '#1a1d23', border: '1px solid #2a2e36', borderRadius: 6, color: '#e8eaed', padding: '6px 10px', fontSize: 13, width: 220, outline: 'none' },
  button: { background: '#4285f4', border: 'none', borderRadius: 6, color: '#fff', padding: '6px 14px', fontSize: 13, cursor: 'pointer' },
  chartWrap: { width: '100%', height: 440, background: '#1a1d23', borderRadius: 10, padding: '8px 8px 0' },
}