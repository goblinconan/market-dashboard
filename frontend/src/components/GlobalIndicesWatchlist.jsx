export default function GlobalIndicesWatchlist({ indices, selectedName, onSelect }) {
  if (!indices || indices.length === 0) {
    return <p style={{ color: '#9aa0a6' }}>加载全球指数...</p>
  }

  return (
    <section style={{ marginTop: 32 }}>
      <h2 style={styles.sectionTitle}>全球主要股市指数</h2>
      <div style={styles.grid}>
        {indices.map((item) => {
          const isUp = item.change_pct != null && item.change_pct > 0
          const isDown = item.change_pct != null && item.change_pct < 0
          const color = isUp ? '#0f9d58' : isDown ? '#db4437' : '#9aa0a6'
          const isSelected = selectedName === item.name

          return (
            <div
              key={item.sina_code}
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
              <div style={styles.priceRow}>
                <span style={{ ...styles.price, color }}>
                  {item.price != null ? item.price.toLocaleString('zh-CN', { maximumFractionDigits: 2 }) : '—'}
                </span>
                <span style={{ ...styles.change, color }}>
                  {item.change_pct != null
                    ? `${item.change_pct > 0 ? '+' : ''}${item.change_pct.toFixed(2)}%`
                    : '—'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

const styles = {
  sectionTitle: { fontSize: 15, fontWeight: 500, color: '#9aa0a6', margin: '0 0 10px 0', letterSpacing: 0.5 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10 },
  card: { background: '#1a1d23', border: '1px solid #2a2e36', borderRadius: 10, padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 4, cursor: 'pointer', transition: 'border-color 0.15s' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  name: { fontSize: 14, fontWeight: 500, color: '#e8eaed' },
  priceRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 4 },
  price: { fontSize: 18, fontWeight: 600 },
  change: { fontSize: 12, fontWeight: 500 },
}