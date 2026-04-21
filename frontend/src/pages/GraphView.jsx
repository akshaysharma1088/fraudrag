import React, { useState, useEffect, useRef } from 'react'
import api from '../utils/api'

const MOCK_GRAPH = {
  nodes: [
    { id: 'demo-001', label: 'Alice Johnson', type: 'Customer', risk: 0.1, group: 'customer' },
    { id: 'demo-002', label: 'Bob Williams', type: 'Customer', risk: 0.72, group: 'customer-risky' },
    { id: 'inst-001', label: 'First National Bank', type: 'Institution', group: 'institution' },
    { id: 'inst-002', label: 'Metro Credit Union', type: 'Institution', group: 'institution' },
    { id: 'stmt-001', label: 'Statement Jan 2025', type: 'Statement', group: 'statement' },
    { id: 'stmt-002', label: 'Statement Mar 2025', type: 'Statement', flagged: true, group: 'statement-fraud' },
    { id: 'pattern-001', label: 'Balance Rounding', type: 'FraudPattern', group: 'pattern' },
    { id: 'pattern-002', label: 'Digit Substitution', type: 'FraudPattern', group: 'pattern' },
  ],
  edges: [
    { from: 'demo-001', to: 'stmt-001', label: 'FILED' },
    { from: 'demo-002', to: 'stmt-002', label: 'FILED' },
    { from: 'stmt-001', to: 'inst-001', label: 'ISSUED_BY' },
    { from: 'stmt-002', to: 'inst-001', label: 'ISSUED_BY' },
    { from: 'demo-002', to: 'pattern-002', label: 'MATCHES_PATTERN' },
    { from: 'stmt-002', to: 'pattern-001', label: 'DETECTED_IN' },
    { from: 'demo-001', to: 'inst-002', label: 'HAS_ACCOUNT' },
    { from: 'demo-002', to: 'inst-002', label: 'HAS_ACCOUNT' },
  ],
}

const GROUP_COLORS = {
  'customer': '#00e5ff',
  'customer-risky': '#f97316',
  'institution': '#a78bfa',
  'statement': '#4ade80',
  'statement-fraud': '#ef4444',
  'pattern': '#facc15',
}

const GROUP_SHAPES = {
  'customer': '●', 'customer-risky': '◆',
  'institution': '■', 'statement': '▲',
  'statement-fraud': '▲', 'pattern': '★',
}

export default function GraphView() {
  const [customerId, setCustomerId] = useState('demo-001')
  const [graphData, setGraphData] = useState(MOCK_GRAPH)
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState('')

  const canvasRef = useRef(null)
  const positions = useRef({})
  const animRef = useRef(null)
  const velocities = useRef({})

  // Initialize positions
  useEffect(() => {
    const nodes = graphData.nodes
    const cx = 420, cy = 280, r = 200
    nodes.forEach((n, i) => {
      if (!positions.current[n.id]) {
        const angle = (i / nodes.length) * Math.PI * 2
        positions.current[n.id] = { x: cx + Math.cos(angle) * r * (0.5 + Math.random() * 0.5), y: cy + Math.sin(angle) * r * (0.5 + Math.random() * 0.5) }
        velocities.current[n.id] = { x: 0, y: 0 }
      }
    })
    startAnimation()
    return () => cancelAnimationFrame(animRef.current)
  }, [graphData])

  function startAnimation() {
    function tick() {
      runForceLayout()
      draw()
      animRef.current = requestAnimationFrame(tick)
    }
    tick()
  }

  function runForceLayout() {
    const nodes = graphData.nodes
    const edges = graphData.edges
    const k = 0.02, repulsion = 8000, damping = 0.85

    // Repulsion
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = positions.current[nodes[i].id]
        const b = positions.current[nodes[j].id]
        if (!a || !b) continue
        const dx = a.x - b.x, dy = a.y - b.y
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1)
        const force = repulsion / (dist * dist)
        velocities.current[nodes[i].id].x += (dx / dist) * force
        velocities.current[nodes[i].id].y += (dy / dist) * force
        velocities.current[nodes[j].id].x -= (dx / dist) * force
        velocities.current[nodes[j].id].y -= (dy / dist) * force
      }
    }

    // Attraction along edges
    edges.forEach(e => {
      const a = positions.current[e.from], b = positions.current[e.to]
      if (!a || !b) return
      const dx = b.x - a.x, dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      const force = (dist - 120) * k
      velocities.current[e.from].x += (dx / dist) * force
      velocities.current[e.from].y += (dy / dist) * force
      velocities.current[e.to].x -= (dx / dist) * force
      velocities.current[e.to].y -= (dy / dist) * force
    })

    // Center gravity
    nodes.forEach(n => {
      const p = positions.current[n.id]
      if (!p) return
      velocities.current[n.id].x += (420 - p.x) * 0.001
      velocities.current[n.id].y += (280 - p.y) * 0.001
      velocities.current[n.id].x *= damping
      velocities.current[n.id].y *= damping
      p.x += velocities.current[n.id].x
      p.y += velocities.current[n.id].y
    })
  }

  function draw() {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const { width, height } = canvas

    ctx.clearRect(0, 0, width, height)
    ctx.fillStyle = '#0a0b0e'
    ctx.fillRect(0, 0, width, height)

    // Grid
    ctx.strokeStyle = '#1e2235'
    ctx.lineWidth = 0.5
    for (let x = 0; x < width; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke() }
    for (let y = 0; y < height; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke() }

    // Edges
    graphData.edges.forEach(e => {
      const a = positions.current[e.from], b = positions.current[e.to]
      if (!a || !b) return
      const isSelected = selected?.id === e.from || selected?.id === e.to
      ctx.strokeStyle = isSelected ? '#00e5ff' : '#2a3050'
      ctx.lineWidth = isSelected ? 1.5 : 0.8
      ctx.setLineDash(isSelected ? [] : [3, 3])
      ctx.beginPath()
      ctx.moveTo(a.x, a.y)
      ctx.lineTo(b.x, b.y)
      ctx.stroke()
      ctx.setLineDash([])

      // Edge label
      if (isSelected) {
        const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2
        ctx.fillStyle = '#3d4468'
        ctx.font = '9px DM Mono'
        ctx.textAlign = 'center'
        ctx.fillText(e.label, mx, my - 4)
      }
    })

    // Nodes
    graphData.nodes.forEach(n => {
      const p = positions.current[n.id]
      if (!p) return
      const color = GROUP_COLORS[n.group] || '#4ade80'
      const isSelected = selected?.id === n.id
      const r = isSelected ? 18 : 13

      // Glow
      const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 2)
      grd.addColorStop(0, color + '44')
      grd.addColorStop(1, 'transparent')
      ctx.fillStyle = grd
      ctx.beginPath()
      ctx.arc(p.x, p.y, r * 2, 0, Math.PI * 2)
      ctx.fill()

      // Node circle
      ctx.fillStyle = isSelected ? color : color + 'cc'
      ctx.strokeStyle = color
      ctx.lineWidth = isSelected ? 2 : 1
      ctx.beginPath()
      ctx.arc(p.x, p.y, r, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()

      // Label
      ctx.fillStyle = isSelected ? '#ffffff' : '#e8eaf2'
      ctx.font = `${isSelected ? '11px' : '10px'} DM Sans`
      ctx.textAlign = 'center'
      ctx.fillText(n.label, p.x, p.y + r + 14)

      // Type tag
      ctx.fillStyle = '#3d4468'
      ctx.font = '9px DM Mono'
      ctx.fillText(n.type, p.x, p.y + r + 24)
    })
  }

  function handleCanvasClick(e) {
    const rect = canvasRef.current.getBoundingClientRect()
    const mx = e.clientX - rect.left, my = e.clientY - rect.top
    let hit = null
    graphData.nodes.forEach(n => {
      const p = positions.current[n.id]
      if (!p) return
      const dist = Math.sqrt((p.x - mx) ** 2 + (p.y - my) ** 2)
      if (dist < 18) hit = n
    })
    setSelected(hit)
  }

  async function loadCustomerGraph() {
    setLoading(true)
    try {
      const res = await api.get(`/graph/customer/${customerId}`)
      const { subgraph, rag_context } = res.data
      if (subgraph?.nodes?.length) {
        // Transform API response to our format
        const nodes = subgraph.nodes.map(n => ({
          id: n.id,
          label: n.properties?.name || n.id,
          type: n.labels?.[0] || 'Node',
          group: n.labels?.[0]?.toLowerCase() === 'customer' ? (n.properties?.risk_score > 0.5 ? 'customer-risky' : 'customer') : n.labels?.[0]?.toLowerCase() === 'institution' ? 'institution' : n.labels?.[0]?.toLowerCase() === 'statement' ? (n.properties?.fraud_flagged ? 'statement-fraud' : 'statement') : 'pattern',
        }))
        const edges = subgraph.relationships.map(r => ({ from: r.source, to: r.target, label: r.type }))
        positions.current = {}
        velocities.current = {}
        setGraphData({ nodes, edges })
      }
      if (rag_context) setContext(rag_context)
    } catch { /* use demo data */ }
    setLoading(false)
  }

  const legendItems = Object.entries(GROUP_COLORS)

  return (
    <div className="page fade-up">
      <div className="page-header">
        <h1>Knowledge Graph</h1>
        <p>Customer entity relationships, fraud patterns, and risk propagation</p>
      </div>

      <div className="grid-2 mb-4" style={{ alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', gap: 10 }}>
          <input className="input" value={customerId} onChange={e => setCustomerId(e.target.value)}
            placeholder="Customer ID" style={{ maxWidth: 200 }} />
          <button className="btn btn-primary" onClick={loadCustomerGraph} disabled={loading}>
            {loading ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Loading…</> : '⬡ Load Graph'}
          </button>
          <button className="btn btn-ghost" onClick={() => { setGraphData(MOCK_GRAPH); setSelected(null); positions.current = {}; velocities.current = {} }}>
            Reset Demo
          </button>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          {legendItems.map(([group, color]) => (
            <div key={group} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)' }}>{group}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid-2" style={{ gap: 16, alignItems: 'flex-start' }}>
        {/* Canvas */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <canvas ref={canvasRef} width={840} height={560} onClick={handleCanvasClick}
            style={{ display: 'block', cursor: 'pointer', width: '100%' }} />
        </div>

        {/* Details panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {selected ? (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Node Details</span>
                <span style={{ fontSize: 20, color: GROUP_COLORS[selected.group] }}>{GROUP_SHAPES[selected.group]}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700 }}>{selected.label}</div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <span className="risk-badge minimal" style={{ borderColor: GROUP_COLORS[selected.group], color: GROUP_COLORS[selected.group] }}>{selected.type}</span>
                  {selected.risk !== undefined && (
                    <span className={`risk-badge ${selected.risk > 0.5 ? 'high' : 'minimal'}`}>Risk: {selected.risk.toFixed(2)}</span>
                  )}
                  {selected.flagged && <span className="risk-badge critical">Flagged</span>}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>ID: {selected.id}</div>
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 6 }}>Connected To</div>
                  {graphData.edges
                    .filter(e => e.from === selected.id || e.to === selected.id)
                    .map((e, i) => {
                      const otherId = e.from === selected.id ? e.to : e.from
                      const other = graphData.nodes.find(n => n.id === otherId)
                      return (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', borderBottom: '1px solid var(--border)' }}
                          onClick={() => setSelected(other)} style={{ cursor: 'pointer', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
                          <div style={{ width: 6, height: 6, borderRadius: '50%', background: GROUP_COLORS[other?.group], flexShrink: 0 }} />
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', flex: 1 }}>{e.label}</span>
                          <span style={{ fontSize: 12, color: 'var(--text-primary)' }}>{other?.label || otherId}</span>
                        </div>
                      )
                    })}
                </div>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>Select a Node</div>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                Click any node in the graph to inspect its properties, relationships, and fraud connections.
              </p>
              <div style={{ marginTop: 16, padding: 12, background: 'var(--bg-elevated)', borderRadius: 8, border: '1px solid var(--border)' }}>
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                  {graphData.nodes.length} nodes · {graphData.edges.length} edges
                </p>
              </div>
            </div>
          )}

          {context && (
            <div className="card">
              <div className="card-header"><span className="card-title">RAG Context</span></div>
              <div className="mono-block" style={{ fontSize: 11, maxHeight: 200, overflowY: 'auto' }}>{context}</div>
            </div>
          )}

          <div className="card">
            <div className="card-header"><span className="card-title">Graph Statistics</span></div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {[
                { label: 'Nodes', value: graphData.nodes.length },
                { label: 'Edges', value: graphData.edges.length },
                { label: 'High Risk', value: graphData.nodes.filter(n => n.group === 'customer-risky' || n.group === 'statement-fraud').length },
                { label: 'Patterns', value: graphData.nodes.filter(n => n.group === 'pattern').length },
              ].map(s => (
                <div key={s.label} style={{ textAlign: 'center', padding: '10px', background: 'var(--bg-elevated)', borderRadius: 8 }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 22, color: 'var(--text-primary)' }}>{s.value}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
