import { useState } from 'react'

export default function FundWatchlist({ funds, selectedCode, onSelect, onSearch }) {
  const [inputValue, setInputValue] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!inputValue.trim()) return
    onSearch(inputValue.trim())
    setInputValue('')
  }

  return (
    <section style={{ marginTop: 32 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <h2 style={styles.sectionTitle}>基金 · 净值走势</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="输入基金代码，如 001050"
            style={styles.input}
          />
          <button type="submit" style={styles.button}>查询</button>
        </form>
      </div>

      <div style={styles.grid}>
        {(funds || []).map((item) => {
          const isSelected = selectedCode === item.code
          return (
            <div
              key={item.code}
              onClick={() => onSelect(item)}
              style={{
                ...styles.card,
                borderColor: isSelected ? '#4285f4' : '#2a2e36',
                boxShadow: isSelected ? '0 0 0 1px #4285f4' : 'none',
              }}
            >
              <div style={styles.cardHeader}>
                <span style={styles.name}>{item.name}</span>
              </div>
              <div style={styles.code}>{item.code}</div>
              <div style={styles.priceRow}>
                <span style={styles.price}>{item.price != null ? item.price.toFixed(4) : '—'}</span>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

const styles = {
  sectionTitle: { fontSize: 15, fontWeight: 500, color: '#9aa0a6', margin: 0, letterSpacing: 0.5 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 },
  card: { background: '#1a1d23', border: '1px solid #2a2e36', borderRadius: 10, padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 4, cursor: 'pointer', transition: 'border-color 0.15s' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  name: { fontSize: 14, fontWeight: 500, color: '#e8eaed' },
  code: { fontSize: 11, color: '#9aa0a6', fontFamily: 'monospace' },
  priceRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 4 },
  price: { fontSize: 18, fontWeight: 600, color: '#409eff' },
  input: { background: '#1a1d23', border: '1px solid #2a2e36', borderRadius: 6, color: '#e8eaed', padding: '6px 10px', fontSize: 13, width: 200, outline: 'none' },
  button: { background: '#4285f4', border: 'none', borderRadius: 6, color: '#fff', padding: '6px 14px', fontSize: 13, cursor: 'pointer' },
}