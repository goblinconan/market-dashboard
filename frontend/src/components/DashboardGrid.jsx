import DashboardCard from './DashboardCard.jsx'

export default function DashboardGrid({ sections }) {
  return (
    <div style={{ display: 'grid', gap: 20 }}>
      {sections.map((section) => (
        <section key={section.id}>
          <h2 style={styles.sectionTitle}>{section.title}</h2>
          <div style={styles.grid}>
            {Object.entries(section.items).map(([label, value]) => (
              <DashboardCard key={label} label={label} value={value} />
            ))}
          </div>
        </section>
      ))}
    </div>
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
    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: 12,
  },
}