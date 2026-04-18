export default function StatsPanel({ stats, connected, lastUpdate, flightCount }) {
  const dot = connected ? '#22c55e' : '#ef4444'
  return (
    <div style={{
      position: 'absolute', top: 20, left: 20,
      display: 'flex', flexDirection: 'column', gap: 10,
      zIndex: 10, pointerEvents: 'none'
    }}>
      <div style={{
        background: 'rgba(5,15,35,0.85)',
        border: '0.5px solid rgba(100,180,255,0.2)',
        borderRadius: 10, padding: '10px 16px',
        display: 'flex', alignItems: 'center', gap: 8
      }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: dot }}/>
        <span style={{ fontSize: 13, color: '#7ecfff', fontWeight: 500 }}>SKYMAP</span>
        <span style={{ fontSize: 11, color: '#4a7090', marginLeft: 4 }}>
          {connected ? `Live · ${lastUpdate || '...'}` : 'Reconectando...'}
        </span>
      </div>
      {stats && (
        <>
          <StatCard label="Vuelos visibles"  value={flightCount.toLocaleString()} />
          <StatCard label="En vuelo"         value={stats.en_vuelo?.toLocaleString()} />
          <StatCard label="En tierra"        value={stats.en_tierra?.toLocaleString()} />
          <StatCard label="Vel. media"       value={`${stats.vel_media_kmh} km/h`} />
          <StatCard label="Alt. media"       value={`${stats.alt_media_m?.toLocaleString()} m`} />
          <StatCard label="Vel. maxima"      value={`${stats.vel_max_kmh} km/h`} accent />
          <StatCard label="Alt. maxima"      value={`${stats.alt_max_m?.toLocaleString()} m`} accent />
        </>
      )}
      <div style={{ marginTop: 4 }}>
        <div style={{ fontSize: 10, color: '#2a4a6a', marginBottom: 6 }}>ALTITUD</div>
        {[
          { color: '#ff6b35', label: 'En tierra' },
          { color: '#ffd700', label: '< 3.000 m' },
          { color: '#00d4ff', label: '3.000 - 8.000 m' },
          { color: '#c084fc', label: '> 8.000 m' },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
            <span style={{ fontSize: 11, color: '#4a7090' }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function StatCard({ label, value, accent }) {
  return (
    <div style={{
      background: 'rgba(5,15,35,0.82)',
      border: `0.5px solid ${accent ? 'rgba(192,132,252,0.3)' : 'rgba(100,180,255,0.15)'}`,
      borderRadius: 8, padding: '7px 12px', minWidth: 160
    }}>
      <div style={{ fontSize: 10, color: '#2a4a6a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: 20, fontWeight: 500, color: accent ? '#c084fc' : '#7ecfff', lineHeight: 1.3 }}>
        {value ?? '?'}
      </div>
    </div>
  )
}
