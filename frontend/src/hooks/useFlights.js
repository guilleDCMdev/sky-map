import { useState, useEffect, useRef, useCallback } from 'react'

const WS_URL = `ws://${window.location.hostname}:8000/ws/flights`

export function useFlights() {
  const [flights, setFlights]       = useState([])
  const [stats, setStats]           = useState(null)
  const [connected, setConnected]   = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const wsRef = useRef(null)

  const fetchStats = useCallback(async () => {
    try {
      const r = await fetch('/api/stats/summary')
      const data = await r.json()
      setStats(data)
    } catch (e) {
      console.error('Error fetching stats:', e)
    }
  }, [])

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 15000)
    return () => clearInterval(interval)
  }, [fetchStats])

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws
      ws.onopen  = () => { setConnected(true) }
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data)
        if (msg.type === 'flights_update') {
          setFlights(msg.flights)
          setLastUpdate(new Date().toLocaleTimeString())
        }
      }
      ws.onclose = () => { setConnected(false); setTimeout(connect, 3000) }
      ws.onerror = () => ws.close()
    }
    connect()
    return () => wsRef.current?.close()
  }, [])

  return { flights, stats, connected, lastUpdate }
}
