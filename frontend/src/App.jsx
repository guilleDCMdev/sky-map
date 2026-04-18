import { useState } from 'react'
import Globe from './components/Globe'
import StatsPanel from './components/StatsPanel'
import FlightDetail from './components/FlightDetail'
import { useFlights } from './hooks/useFlights'

export default function App() {
  const { flights, stats, connected, lastUpdate } = useFlights()
  const [selected, setSelected] = useState(null)

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', background: '#050d1a' }}>
      <Globe flights={flights} onSelect={setSelected} />
      <StatsPanel
        stats={stats}
        connected={connected}
        lastUpdate={lastUpdate}
        flightCount={flights.length}
      />
      <FlightDetail flight={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
