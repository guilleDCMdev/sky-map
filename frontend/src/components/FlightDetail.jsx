import { useEffect, useState } from 'react'

export default function FlightDetail({ flight, onClose }) {
  const [history, setHistory] = useState([])

  useEffect(() => {
    if (!flight) return
    setHistory([])
    fetch(`/api/flights/history/${flight.icao24}?hours=2`)
      .then(r => r.json())
      .then(d => setHistory(d.points || []))
      .catch(() => {})
  }, [flight])

  if (!flight) return null

  return (
    <div style={{
      position: 'absolute', bottom: 24, right: 24,
      background: 'rgba(5,15,35,0.95)',
      border: '0.5px solid rgba(100,200,255,0.3)',
      borderRadius: 12, padding: '16px 20px',
      width: 280, zIndex: 10
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: 18, fontWeight: 500, color: '#7ecfff' }}>
          {(flight.callsign || flight.icao24 || '?').trim()}
        </span>
        <button onClick={onClose} style={{
          background: 'none', border: 'none', color: '#4a7090',
          fontSize: 20, cursor: 'pointer', lineHeight: 1
        }}>x</button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {[
          ['Pais',      flight.origin_country],
          ['ICAO24',    flight.icao24],
          ['Altitud',   `${Math.round(flight.baro_altitude || 0).toLocaleString()} m`],
          ['Velocidad', `${Math.round((flight.velocity || 0) * 3.6)} km/h`],
          ['Rumbo',     `${Math.round(flight.true_track || 0)} deg`],
          ['Vrate',     `${flight.vertical_rate?.toFixed(1) || 0} m/s`],
          ['Estado',    flight.on_ground ? 'En tierra' : 'En vuelo'],
          ['Posicion',  `${flight.latitude?.toFixed(4)}, ${flight.longitude?.toFixed(4)}`],
        ].map(([k, v]) => (
          <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
            <span style={{ color: '#4a7090' }}>{k}</span>
            <span style={{ color: '#c8dff5' }}>{v}</span>
          </div>
        ))}
      </div>
      {history.length > 0 && (
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '0.5px solid rgba(100,180,255,0.15)' }}>
          <div style={{ fontSize: 11, color: '#2a4a6a', marginBottom: 4 }}>
            HISTORIAL — {history.length} puntos (2h)
          </div>
          <div style={{ fontSize: 12, color: '#4a7090' }}>
            {new Date(history[0].fetched_at).toLocaleTimeString()} a{' '}
            {new Date(history[history.length-1].fetched_at).toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  )
}
