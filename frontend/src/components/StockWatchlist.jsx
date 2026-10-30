export default function StockWatchlist({ watchlist, onSelect, selectedCode }) {
  if (!watchlist || watchlist.length === 0) {
    return <p style={{ color: '#9aa0a6' }}>加载股票行情...</p>
  }

  return (
    <section style={{ marginTop: 32 }}>
      <h2 style={styles.sectionTitle}>关注列表 · 实时行情</h2>
      <div style={styles.grid}>
        {watchlist.map((item) => {
          const isUp = item.change_pct != null && item.change_pct > 0
          const isDown = item.change_pct != null && item.change_pct < 0
          const color = isUp ? '#0f9d58' : isDown ? '#db4437' : '#9aa0a6'
          const isSelected = selectedCode === item.full_code

          return (
            <div
              key={item.full_code}
              onClick={() => onSelect(item)}
              style={{
                ...styles.card,
                borderColor: isSelected ? '#4285f4' : '#2a2e36',
                boxShadow: isSelected ? '0 0 0 1px #4285f4' : 'none',
              }}
            >
              <div style={styles.cardHeader}>
                <span style={styles.name}>{item.name}</span>
                <span style={styles.type}>{item.type}</span>
              </div>
              <div style={styles.code}>{item.pure_code}</div>
              <div style={styles.priceRow}>
                <span style={{ ...styles.price, color }}>
                  {item.price != null ? item.price.toFixed(2) : '—'}
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
  sectionTitle: {
    fontSize: 15,
    fontWeight: 500,
    color: '#9aa0a6',
    margin: '0 0 10px 0',
    letterSpacing: 0.5,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
    gap: 10,
  },
  card: {
    background: '#1a1d23',
    border: '1px solid #2a2e36',
    borderRadius: 10,
    padding: '12px 14px',
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
    cursor: 'pointer',
    transition: 'border-color 0.15s, box-shadow 0.15s',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 6,
  },
  name: { fontSize: 14, fontWeight: 500, color: '#e8eaed' },
  type: {
    fontSize: 10,
    padding: '1px 5px',
    borderRadius: 4,
    background: '#2a2e36',
    color: '#9aa0a6',
  },
  code: { fontSize: 11, color: '#9aa0a6', fontFamily: 'monospace' },
  priceRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginTop: 4,
  },
  price: { fontSize: 18, fontWeight: 600 },
  change: { fontSize: 12, fontWeight: 500 },
}