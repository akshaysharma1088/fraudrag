import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'
import api from '../utils/api'

const RISK_COLORS = {
  minimal: '#4ade80',
  low: '#a3e635',
  medium: '#facc15',
  high: '#f97316',
  critical: '#ef4444',
  unknown: '#3d4468',
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color || 'var(--accent)' }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(3) : p.value}</p>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [statements, setStatements] = useState([])
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [mRes, sRes, aRes] = await Promise.allSettled([
          api.get('/fraud/dashboard'),
          api.get('/statements/'),
          api.get('/fraud/recent-alerts'),
        ])
        if (mRes.status === 'fulfilled') setMetrics(mRes.value.data)
        if (sRes.status === 'fulfilled') setStatements(sRes.value.data.statements || [])
        if (aRes.status === 'fulfilled') setAlerts(aRes.value.data.alerts || [])
      } catch (e) { /* demo mode */ }
      finally { setLoading(false) }
    }
    load()
  }, [])

  // Demo data when backend is offline
  const demoMetrics = metrics || {
    total_analyzed: 1247,
    high_risk_count: 38,
    medium_risk_count: 94,
    low_risk_count: 312,
    average_fraud_score: 0.127,
    confirmed_fraud_rate: 0.031,
  }

  const trendData = [
    { day: 'Mon', score: 0.09, flagged: 4 },
    { day: 'Tue', score: 0.14, flagged: 7 },
    { day: 'Wed', score: 0.11, flagged: 5 },
    { day: 'Thu', score: 0.21, flagged: 12 },
    { day: 'Fri', score: 0.18, flagged: 9 },
    { day: 'Sat', score: 0.08, flagged: 3 },
    { day: 'Sun', score: 0.12, flagged: 6 },
  ]

  const riskDistribution = [
    { name: 'Minimal', value: demoMetrics.total_analyzed - demoMetrics.high_risk_count - demoMetrics.medium_risk_count - demoMetrics.low_risk_count, color: RISK_COLORS.minimal },
    { name: 'Low', value: demoMetrics.low_risk_count, color: RISK_COLORS.low },
    { name: 'Medium', value: demoMetrics.medium_risk_count, color: RISK_COLORS.medium },
    { name: 'High/Critical', value: demoMetrics.high_risk_count, color: RISK_COLORS.high },
  ]

  const indicatorTypes = [
    { type: 'Balance Manipulation', count: 47, pct: 38 },
    { type: 'Amount Substitution', count: 31, pct: 25 },
    { type: 'Date Forgery', count: 18, pct: 15 },
    { type: 'Entity Mismatch', count: 14, pct: 11 },
    { type: 'Metadata Tampering', count: 9, pct: 7 },
    { type: 'Graph Anomaly', count: 5, pct: 4 },
  ]

  return (
    <div className="page fade-up">
      <div className="scan-line" />
      <div className="page-header">
        <h1>Intelligence Dashboard</h1>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', marginTop: 6 }}>
          FraudRAG v1.0 · KNOWLEDGE GRAPH RAG · MEDALLION ARCHITECTURE
        </p>
      </div>

      {/* Metrics */}
      <div className="metric-grid">
        {[
          { label: 'Total Analyzed', value: demoMetrics.total_analyzed.toLocaleString(), sub: 'Statements processed' },
          { label: 'High Risk Flagged', value: demoMetrics.high_risk_count, sub: `${((demoMetrics.high_risk_count / demoMetrics.total_analyzed) * 100).toFixed(1)}% of total`, accent: true },
          { label: 'Avg Fraud Score', value: demoMetrics.average_fraud_score.toFixed(3), sub: 'Across all statements' },
          { label: 'Confirmed Fraud Rate', value: `${(demoMetrics.confirmed_fraud_rate * 100).toFixed(1)}%`, sub: 'Analyst verified' },
        ].map((m, i) => (
          <div key={i} className="metric-card" style={m.accent ? { borderColor: 'rgba(249,115,22,0.3)' } : {}}>
            {m.accent && <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: 'var(--risk-high)' }} />}
            <div className="metric-label">{m.label}</div>
            <div className="metric-value" style={m.accent ? { color: 'var(--risk-high)' } : {}}>{m.value}</div>
            <div className="metric-sub">{m.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid-2 mb-6">
        <div className="card">
          <div className="card-header">
            <span className="card-title">7-Day Fraud Score Trend</span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={trendData}>
              <XAxis dataKey="day" tick={{ fill: 'var(--text-secondary)', fontSize: 11, fontFamily: 'var(--font-mono)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 11, fontFamily: 'var(--font-mono)' }} axisLine={false} tickLine={false} domain={[0, 0.3]} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="score" stroke="var(--accent)" strokeWidth={2} dot={{ fill: 'var(--accent)', r: 3 }} name="Avg Score" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Risk Distribution</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <PieChart width={140} height={140}>
              <Pie data={riskDistribution} cx={65} cy={65} innerRadius={40} outerRadius={65} dataKey="value" strokeWidth={0}>
                {riskDistribution.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
            </PieChart>
            <div style={{ flex: 1 }}>
              {riskDistribution.map(d => (
                <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: d.color, flexShrink: 0 }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', flex: 1 }}>{d.name}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-primary)' }}>{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid-2">
        {/* Indicator Breakdown */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Top Fraud Indicators</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {indicatorTypes.map(ind => (
              <div key={ind.type}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>{ind.type}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>{ind.count}</span>
                </div>
                <div className="score-bar-track">
                  <div className="score-bar-fill" style={{ width: `${ind.pct}%`, background: 'var(--accent)', opacity: 0.7 }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Recent High-Risk Alerts</span>
            <Link to="/upload" className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: 12 }}>New Scan</Link>
          </div>
          {alerts.length === 0 ? (
            <div style={{ padding: '24px 0', textAlign: 'center' }}>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)' }}>
                No high-risk alerts. Upload a statement to begin.
              </p>
              <Link to="/upload" className="btn btn-primary" style={{ marginTop: 16, display: 'inline-flex' }}>
                Upload Statement
              </Link>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {alerts.slice(0, 5).map(a => (
                <Link key={a.statement_id} to={`/analysis/${a.statement_id}`}
                  style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-elevated)' }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: RISK_COLORS[a.risk_level] || RISK_COLORS.minimal, boxShadow: `0 0 6px ${RISK_COLORS[a.risk_level]}` }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-primary)', flex: 1 }}>{a.statement_id.slice(0, 12)}…</span>
                  <span className={`risk-badge ${a.risk_level}`}>{a.risk_level}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>{a.fraud_score?.toFixed(3)}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
