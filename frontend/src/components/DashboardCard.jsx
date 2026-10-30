export default function DashboardCard({ label, value }) {
  const display =
    value === null || value === undefined
      ? '—'
      : typeof value === 'number'
      ? value.toLocaleString('zh-CN', { maximumFractionDigits: 4 })
      : value

  return (
    <div style={styles.card}>
      <div style={styles.label}>{label}</div>
      <div style={styles.value}>{display}</div>
    </div>
  )
}

const styles = {
  card: {
    background: '#1a1d23',
    border: '1px solid #2a2e36',
    borderRadius: 10,
    padding: '14px 16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  label: { fontSize: 12, color: '#9aa0a6' },
  value: { fontSize: 20, fontWeight: 600, color: '#e8eaed' },
}