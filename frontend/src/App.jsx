import { useCallback, useEffect, useRef, useState } from 'react'
import DashboardGrid from './components/DashboardGrid.jsx'
import FundHistoryChart from './components/FundHistoryChart.jsx'
import FundWatchlist from './components/FundWatchlist.jsx'
import MiniTrendChart from './components/MiniTrendChart.jsx'
import StockHistoryChart from './components/StockHistoryChart.jsx'
import StockWatchlist from './components/StockWatchlist.jsx'

const WS_URL = window.location.protocol === 'https:'
  ? `wss://${window.location.host}/ws`
  : `ws://${window.location.host}/ws`

function GlobalIndicesSection({ indices }) {
  const [selected, setSelected] = useState('道琼斯')
  const [chartData, setChartData] = useState([])
  const [loadingChart, setLoadingChart] = useState(false)

  useEffect(() => {
    if (!selected) return
    setLoadingChart(true)
    // 动态请求当前选中的指数历史数据
    fetch(`/api/global_indices/history?name=${encodeURIComponent(selected)}`)
      .then(res => res.json())
      .then(data => {
        setChartData(Array.isArray(data) ? data : [])
      })
      .catch(() => setChartData([]))
      .finally(() => setLoadingChart(false))
  }, [selected])

  if (!indices || indices.length === 0) return null

  return (
    <section style={{ marginTop: 32 }}>
      <h2 style={{ fontSize: 15, fontWeight: 500, color: '#9aa0a6', margin: '0 0 10px 0', letterSpacing: 0.5 }}>全球主要股市指数</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10 }}>
        {indices.map(item => {
          const isUp = item.change_pct > 0
          const isDown = item.change_pct < 0
          const color = isUp ? '#0f9d58' : isDown ? '#db4437' : '#9aa0a6'
          const isSelected = selected === item.name
          return (
            <div key={item.name} onClick={() => setSelected(item.name)}
                 style={{
                   background: '#1a1d23', border: `1px solid ${isSelected ? '#4285f4' : '#2a2e36'}`, 
                   borderRadius: 10, padding: '12px 14px', cursor: 'pointer',
                   boxShadow: isSelected ? '0 0 0 1px #4285f4' : 'none'
                 }}>
              <div style={{ fontSize: 14, fontWeight: 500, color: '#e8eaed', marginBottom: 6 }}>{item.name}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: 18, fontWeight: 600, color }}>
                  {item.price != null ? item.price.toLocaleString('zh-CN', { maximumFractionDigits: 2 }) : '—'}
                </span>
                <span style={{ fontSize: 12, fontWeight: 500, color }}>
                  {item.change_pct != null ? `${item.change_pct > 0 ? '+' : ''}${item.change_pct.toFixed(2)}%` : '—'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
      
      {loadingChart ? (
        <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9aa0a6', marginTop: 10 }}>正在加载 {selected} 历史走势...</div>
      ) : chartData.length > 0 ? (
        <div style={{ marginTop: 10 }}>
          <MiniTrendChart title={`${selected} 近一年走势`} data={chartData} color="#4285f4" />
        </div>
      ) : (
        <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9aa0a6', marginTop: 10 }}>{selected} 暂无历史数据</div>
      )}
    </section>
  )
}

export default function App() {
  const [data, setData] = useState(null)
  const [macroHistory, setMacroHistory] = useState(null)
  const [fundSelected, setFundSelected] = useState({ code: '481017', name: '工银物流产业股票A' })
  const [status, setStatus] = useState('connecting')
  const [selectedStock, setSelectedStock] = useState({ code: 'sh600188', name: '兖矿能源' })
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = () => {
    setStatus('connecting')
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => setStatus('online')
    ws.onmessage = (event) => {
      try { setData(JSON.parse(event.data)) } catch {}
    }
    ws.onclose = () => {
      setStatus('offline')
      reconnectTimer.current = setTimeout(connect, 3000)
    }
    ws.onerror = () => ws.close()
    wsRef.current = ws
  }

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [])

  useEffect(() => {
    fetch('/api/macro/history')
      .then((res) => res.json())
      .then((res) => setMacroHistory(res))
      .catch(() => console.error('宏观历史获取失败'))
  }, [])

  const handleSelect = (item) => setSelectedStock({ code: item.full_code, name: item.name })
  const handleQuery = (codeInput) => {
    const s = String(codeInput).trim().toLowerCase()
    const found = (data?.watchlist || []).find((w) => w.pure_code === s || w.full_code === s)
    setSelectedStock({ code: s, name: found ? found.name : null })
  }
  const handleNameResolved = useCallback((resolvedName) => {
    setSelectedStock(prev => ({ ...prev, name: resolvedName }))
  }, [])

  const handleFundSelect = (item) => setFundSelected({ code: item.code, name: item.name })
  const handleFundSearch = (codeInput) => {
    const found = (data?.funds || []).find((f) => f.code === codeInput)
    setFundSelected({ code: codeInput, name: found ? found.name : codeInput })
  }

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>市场看板</h1>
        <div style={styles.meta}>
          <span style={{ ...styles.badge, background: status === 'online' ? '#0f9d58' : status === 'connecting' ? '#f4b400' : '#db4437' }}>
            {status === 'online' ? '实时' : status === 'connecting' ? '连接中' : '已断开'}
          </span>
          {data?.updated_at && <span style={styles.time}>最后更新：{data.updated_at}</span>}
        </div>
      </header>

      {!data ? (
        <p style={{ color: '#888' }}>正在等待数据...</p>
      ) : (
        <>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
            <div>
              <DashboardGrid sections={data.sections.filter((s) => s.id === 'oil')} />
              {macroHistory && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10 }}>
                  <MiniTrendChart title="布伦特原油走势" data={macroHistory.brent} color="#f4b400" />
                  <MiniTrendChart title="全国95号汽油走势" data={macroHistory.oil95} color="#db4437" />
                </div>
              )}
            </div>
            <div>
              <DashboardGrid sections={data.sections.filter((s) => s.id === 'fx')} />
              {macroHistory && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10 }}>
                  <MiniTrendChart title="离岸人民币走势" data={macroHistory.forex} color="#4285f4" />
                  <MiniTrendChart title="美元指数走势" data={macroHistory.dxy} color="#db4437" />
                </div>
              )}
            </div>
            <div>
              <DashboardGrid sections={data.sections.filter((s) => s.id === 'gold')} />
              {macroHistory && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10 }}>
                  <MiniTrendChart title="国际金价走势" data={macroHistory.gold_intl} color="#f4b400" />
                  <MiniTrendChart title="国内金价走势" data={macroHistory.gold_domestic} color="#0f9d58" />
                </div>
              )}
            </div>
            <div>
              <DashboardGrid sections={data.sections.filter((s) => s.id === 'treasury')} />
              {macroHistory && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10 }}>
                  <MiniTrendChart title="美债5年收益率" data={macroHistory.us_bond_5y} color="#4285f4" />
                  <MiniTrendChart title="美债10年收益率" data={macroHistory.us_bond_10y} color="#db4437" />
                </div>
              )}
            </div>
          </div>

          <StockWatchlist watchlist={data.watchlist || []} onSelect={handleSelect} selectedCode={selectedStock.code} />
          <StockHistoryChart symbol={selectedStock.code} name={selectedStock.name} onQuery={handleQuery} onNameResolved={handleNameResolved} />

          <FundWatchlist funds={data.funds || []} selectedCode={fundSelected.code} onSelect={handleFundSelect} onSearch={handleFundSearch} />
          <FundHistoryChart code={fundSelected.code} name={fundSelected.name} />

          <GlobalIndicesSection indices={data.global_indices || []} />
        </>
      )}
    </div>
  )
}

const styles = {
  page: { fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', maxWidth: 1200, margin: '0 auto', padding: '24px 16px 48px', background: '#0f1115', minHeight: '100vh', color: '#e8eaed' },
  header: { display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 },
  title: { fontSize: 24, margin: 0, fontWeight: 600 },
  meta: { display: 'flex', alignItems: 'center', gap: 12, fontSize: 13 },
  badge: { padding: '2px 8px', borderRadius: 999, color: '#fff', fontSize: 12 },
  time: { color: '#9aa0a6' },
}