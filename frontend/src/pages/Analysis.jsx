import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../utils/api'

const RISK_COLORS = {
  minimal: '#4ade80', low: '#a3e635', medium: '#facc15', high: '#f97316', critical: '#ef4444', unknown: '#3d4468',
}

function ScoreGauge({ score }) {
  const pct = (score * 100).toFixed(1)
  const color = score >= 0.75 ? RISK_COLORS.high : score >= 0.45 ? RISK_COLORS.medium : score >= 0.20 ? RISK_COLORS.low : RISK_COLORS.minimal
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>FRAUD SCORE</span>
        <span style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, color, lineHeight: 1 }}>{pct}%</span>
      </div>
      <div className="score-bar-track" style={{ height: 10 }}>
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: `linear-gradient(to right, var(--risk-minimal), ${color})` }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>0 — Legitimate</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>1.0 — Fraudulent</span>
      </div>
    </div>
  )
}

function IndicatorCard({ indicator }) {
  const color = RISK_COLORS[indicator.severity] || RISK_COLORS.unknown
  return (
    <div className="indicator-item" style={{ borderColor: `${color}33` }}>
      <div className="indicator-dot" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase', color }}>{indicator.indicator_type?.replace(/_/g, ' ')}</span>
          <span className={`risk-badge ${indicator.severity}`}>{indicator.severity}</span>
          <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>conf: {((indicator.confidence || 0) * 100).toFixed(0)}%</span>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>{indicator.description}</p>
        {indicator.evidence && Object.keys(indicator.evidence).length > 0 && (
          <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {Object.entries(indicator.evidence).map(([k, v]) => (
              <span key={k} style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', background: 'var(--bg-base)', border: '1px solid var(--border)', borderRadius: 4, padding: '2px 6px' }}>
                {k}: {String(v).slice(0, 40)}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function Analysis() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reviewVerdict, setReviewVerdict] = useState('')
  const [reviewNotes, setReviewNotes] = useState('')
  const [reviewing, setReviewing] = useState(false)
  const [reviewed, setReviewed] = useState(false)

  useEffect(() => {
    api.get(`/fraud/analysis/${id}`)
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load analysis'))
      .finally(() => setLoading(false))
  }, [id])

  async function submitReview() {
    if (!reviewVerdict) return
    setReviewing(true)
    try {
      await api.post(`/fraud/review/${id}`, { analyst_id: 'analyst-001', verdict: reviewVerdict, notes: reviewNotes })
      setReviewed(true)
    } catch { }
    setReviewing(false)
  }

  if (loading) return (
    <div className="page" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div className="spinner" /> <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>Loading analysis…</span>
    </div>
  )

  if (error) return (
    <div className="page">
      <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 12, padding: 24 }}>
        <p style={{ fontFamily: 'var(--font-mono)', color: 'var(--risk-critical)' }}>{error}</p>
        <Link to="/upload" className="btn btn-ghost" style={{ marginTop: 12 }}>← Upload New Statement</Link>
      </div>
    </div>
  )

  const analysis = data?.analysis
  const silver = data?.silver_metadata
  const pipeline = data?.pipeline_metadata
  const fraudScore = analysis?.fraud_score
  const score = typeof fraudScore === 'object' ? fraudScore?.score ?? 0 : fraudScore ?? 0
  const riskLevel = analysis?.risk_level || 'unknown'
  const indicators = analysis?.indicators || []
  const discrepancies = analysis?.discrepancies || []

  return (
    <div className="page fade-up">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1>Fraud Analysis Report</h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>ID: {id} · Customer: {data?.customer_id}</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span className={`risk-badge ${riskLevel}`} style={{ fontSize: 12, padding: '5px 14px' }}>{riskLevel}</span>
          <Link to="/upload" className="btn btn-ghost">New Scan</Link>
        </div>
      </div>

      <div className="grid-2 mb-6" style={{ alignItems: 'flex-start' }}>
        {/* Score card */}
        <div className="card">
          <ScoreGauge score={score} />
          <div style={{ marginTop: 20, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {[
              { label: 'Confidence', value: `${((typeof fraudScore === 'object' ? fraudScore?.confidence : 0.5) * 100).toFixed(0)}%` },
              { label: 'Indicators', value: indicators.length },
              { label: 'Discrepancies', value: discrepancies.length },
              { label: 'Quality Score', value: silver?.quality_score ? `${(silver.quality_score * 100).toFixed(0)}%` : 'N/A' },
              { label: 'Transactions', value: silver?.transaction_count ?? '—' },
              { label: 'Balance Check', value: silver?.balance_check?.is_valid === true ? '✓ Valid' : silver?.balance_check?.is_valid === false ? '⚠ Invalid' : '—' },
            ].map(m => (
              <div key={m.label} style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: '10px 14px' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 4 }}>{m.label}</div>
                <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18, color: 'var(--text-primary)' }}>{m.value}</div>
              </div>
            ))}
          </div>

          {/* Warehouse match */}
          {analysis?.warehouse_match_score !== null && analysis?.warehouse_match_score !== undefined && (
            <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--bg-elevated)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Warehouse Match Score</div>
              <div className="score-bar-track">
                <div className="score-bar-fill" style={{ width: `${(analysis.warehouse_match_score * 100)}%`, background: analysis.warehouse_match_score > 0.9 ? 'var(--risk-minimal)' : analysis.warehouse_match_score > 0.7 ? 'var(--risk-medium)' : 'var(--risk-critical)' }} />
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-primary)', marginTop: 4, textAlign: 'right' }}>{(analysis.warehouse_match_score * 100).toFixed(1)}%</div>
            </div>
          )}
        </div>

        {/* LLM Reasoning */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">AI Reasoning</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>{analysis?.llm_model_used || 'rule-based'}</span>
          </div>
          <div className="mono-block" style={{ maxHeight: 320, overflowY: 'auto', fontSize: 12 }}>
            {analysis?.llm_reasoning || 'No reasoning available.'}
          </div>
        </div>
      </div>

      {/* Fraud Indicators */}
      {indicators.length > 0 && (
        <div className="card mb-6">
          <div className="card-header">
            <span className="card-title">Fraud Indicators ({indicators.length})</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {indicators.map((ind, i) => <IndicatorCard key={i} indicator={ind} />)}
          </div>
        </div>
      )}

      {/* Discrepancies */}
      {discrepancies.length > 0 && (
        <div className="card mb-6">
          <div className="card-header"><span className="card-title">Discrepancies vs Warehouse ({discrepancies.length})</span></div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Field</th><th>Uploaded Value</th><th>Expected Value</th><th>Significance</th></tr>
              </thead>
              <tbody>
                {discrepancies.map((d, i) => (
                  <tr key={i}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{d.field}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--risk-high)' }}>{d.uploaded_value}</td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--risk-minimal)' }}>{d.expected_value}</td>
                    <td><span className={`risk-badge ${d.significance}`}>{d.significance}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Analyst Review */}
      <div className="card">
        <div className="card-header"><span className="card-title">Analyst Review</span></div>
        {reviewed ? (
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--risk-minimal)' }}>✓ Review submitted: <strong>{reviewVerdict}</strong></p>
        ) : (
          <div>
            <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
              {['confirmed_fraud', 'false_positive', 'needs_investigation'].map(v => (
                <button key={v} onClick={() => setReviewVerdict(v)}
                  className="btn btn-ghost"
                  style={{ borderColor: reviewVerdict === v ? 'var(--accent)' : undefined, color: reviewVerdict === v ? 'var(--accent)' : undefined, fontSize: 12 }}>
                  {v.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </button>
              ))}
            </div>
            <textarea className="input" rows={3} placeholder="Analyst notes (optional)…"
              value={reviewNotes} onChange={e => setReviewNotes(e.target.value)}
              style={{ marginBottom: 12, resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: 12 }} />
            <button className="btn btn-primary" onClick={submitReview} disabled={!reviewVerdict || reviewing}>
              {reviewing ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Submitting…</> : 'Submit Review'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
