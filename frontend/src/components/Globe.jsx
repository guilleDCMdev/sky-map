import { useEffect, useRef } from 'react'
import GlobeGL from 'globe.gl'

const ALT_COLOR = (f) => {
  if (f.on_ground) return '#ff6b35'
  const a = f.baro_altitude
  if (!a || a < 0)  return '#ff6b35'
  if (a < 3000)     return '#ffd700'
  if (a < 8000)     return '#00d4ff'
  return '#c084fc'
}

export default function Globe({ flights, onSelect }) {
  const mountRef = useRef(null)
  const globeRef = useRef(null)

  useEffect(() => {
    const globe = GlobeGL()(mountRef.current)
    globe
      .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
      .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
      .width(mountRef.current.clientWidth)
      .height(mountRef.current.clientHeight)
      .pointsData([])
      .pointLat('latitude')
      .pointLng('longitude')
      .pointAltitude(d => (d.baro_altitude || 0) / 1500000)
      .pointRadius(d => d.on_ground ? 0.15 : 0.2)
      .pointColor(ALT_COLOR)
      .pointLabel(d => `
        <div style="background:rgba(5,15,35,0.92);border:0.5px solid rgba(100,200,255,0.3);
          border-radius:8px;padding:10px 14px;font-family:system-ui;font-size:12px;color:#c8dff5">
          <div style="font-size:15px;font-weight:500;color:#7ecfff;margin-bottom:4px">
            ${(d.callsign || d.icao24 || '?').trim()}
          </div>
          <div>${d.origin_country}</div>
          <div>Alt: ${Math.round(d.baro_altitude || 0).toLocaleString()} m</div>
          <div>Vel: ${Math.round((d.velocity || 0) * 3.6)} km/h</div>
          <div>Rumbo: ${Math.round(d.true_track || 0)}deg</div>
        </div>
      `)
      .onPointClick(onSelect)

    globeRef.current = globe

    const handleResize = () => {
      globe.width(mountRef.current.clientWidth).height(mountRef.current.clientHeight)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    if (globeRef.current && flights.length > 0) {
      globeRef.current.pointsData(flights)
    }
  }, [flights])

  return <div ref={mountRef} style={{ width: '100%', height: '100%' }} />
}
