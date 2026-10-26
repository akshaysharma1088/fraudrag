import React, { useEffect, useState } from 'react'
import api from '../utils/api'

const statusColors = {
  MATCH_SUPPORTED: '#4ade80',
  DIFFERENCE_PROVEN: '#facc15',
  EVIDENCE_CONFLICT: '#f97316',
  INSUFFICIENT_EVIDENCE: '#a5b4fc',
  SOURCE_UNTRUSTED_OR_STALE: '#ef4444',
}

function pretty(value) {
  return String(value || '').replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, a => a.toUpperCase())
}

const sampleScenarios = {
  consistent: 'Complete fictional issuer records match the submitted statement',
  altered: 'A fictional closing balance has been altered',
  partial: 'Required transaction evidence is missing',
  conflicting: 'Two independently represented issuer records disagree',
  future: 'Evidence was received after the decision cutoff',
}

export default function EvidenceAcquisition() {
  const [scenario, setScenario] = useState('consistent')
  const [policy, setPolicy] = useState('adaptive_dp')
  const [budget, setBudget] = useState(4)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [available, setAvailable] = useState(false)

  useEffect(() => {
    api.get('/eac/demo/scenarios')
      .then(() => setAvailable(true))
      .catch(() => setAvailable(false))
  }, [])

  async function execute() {
    setRunning(true)
    setError(null)
    setResult(null)
    try {
      const response = await api.post('/eac/demo/run', {
        scenario,
        policy,
        budget_units: Number(budget),
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to run the controlled simulation.')
    } finally {
      setRunning(false)
    }
  }

  const certificate = result?.certificate
  const status = certificate?.document_status
  const budgetSpent = result?.spent_units ?? 0
  return (
    <div className="page fade-up">
      <div className="page-header">
        <h1>Evidence Acquisition Controller</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 6 }}>
          FraudRAG-EAC · Provenance-aware, selective verification research sandbox
        </p>
      </div>
      <div className="card mb-6" style={{ borderColor: 'rgba(251,191,36,0.3)', background: 'rgba(251,191,36,0.04)' }}>
        <div style={{ fontSize: 13, lineHeight: 1.6 }}>
          <strong>Fictional demo only.</strong> This demonstration does not connect to banks,
          authenticate issuers, process uploaded financial files, or determine fraud.
          All source facts, trust attestations, availability and costs are simulated.
        </div>
      </div>

      <div className="card mb-6">
        <div className="card-header">
          <span className="card-title">Run a controlled evidence scenario</span>
          <span style={{ fontSize: 11, color: available ? 'var(--risk-minimal)' : 'var(--text-muted)' }}>
            {available ? 'Sandbox enabled' : 'Sandbox disabled'}
          </span>
        </div>
        <div className="grid-2" style={{ marginBottom: 18 }}>
          <label style={{ display: 'grid', gap: 7, fontSize: 12 }}>
            Fictional evidence condition
            <select className="input" value={scenario} onChange={e => setScenario(e.target.value)}>
              {Object.entries(sampleScenarios).map(([key, description]) =>
                <option key={key} value={key}>{pretty(key)} — {description}</option>
              )}
            </select>
          </label>
          <label style={{ display: 'grid', gap: 7, fontSize: 12 }}>
            Source-request strategy
            <select className="input" value={policy} onChange={e => setPolicy(e.target.value)}>
              <option value="adaptive_dp">Adaptive dynamic programming</option>
              <option value="greedy">Prior-aware greedy baseline</option>
              <option value="fixed">Fixed-order baseline</option>
            </select>
          </label>
        </div>
        <div style={{ display: 'flex', gap: 16, alignItems: 'end', flexWrap: 'wrap' }}>
          <label style={{ display: 'grid', gap: 7, minWidth: 180, fontSize: 12 }}>
            Maximum fictional access cost
            <input className="input" type="number" step="0.1" min="1" max="8"
              value={budget} onChange={e => setBudget(e.target.value)} />
          </label>
          <button className="btn btn-primary" disabled={running || !available}
            onClick={execute}>
            {running ? 'Evaluating sources…' : 'Acquire evidence and verify'}
          </button>
        </div>
        {error && <p role="alert" style={{ marginTop: 16, color: 'var(--risk-critical)', fontSize: 12 }}>{error}</p>}
        {!available && <p style={{ marginTop: 12, color: 'var(--text-secondary)', fontSize: 12 }}>
          Enable EAC_DEMO_ENABLED=true in the backend of a controlled test environment.
        </p>}
      </div>

      {result && (
        <>
          <div className="metric-grid" style={{ marginBottom: 20 }}>
            {[
              { name: 'Decision status', value: pretty(status) },
              { name: 'Source requests', value: result.queries },
              { name: 'Simulated cost spent', value: budgetSpent.toFixed(1) },
              { name: 'Full field coverage', value: result.completed_field_coverage ? 'Yes' : 'No' },
            ].map(item => (
              <div key={item.name} className="metric-card">
                <div className="metric-label">{item.name}</div>
                <div className="metric-value" style={{
                  fontSize: item.name === 'Decision status' ? 15 : 22,
                  color: item.name === 'Decision status' ? statusColors[status] : undefined,
                }}>{item.value}</div>
              </div>
            ))}
          </div>

          <div className="card mb-6">
            <div className="card-header"><span className="card-title">Source acquisition trace</span></div>
            {result.trace.length === 0
              ? <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                No additional requests were required or permitted. Review the evidence certificate.
              </p>
              : <div className="table-wrap"><table>
                <thead><tr><th>Request</th><th>Cost (synthetic units)</th><th>Newly covered fields</th><th>Decision</th></tr></thead>
                <tbody>{result.trace.map((step, i) => <tr key={i}>
                  <td>{pretty(step.action)}</td>
                  <td>{step.cost_units.toFixed(1)}</td>
                  <td>{step.newly_covered_fields.join(', ') || 'None'}</td>
                  <td>{pretty(step.decision_after_action)}</td>
                </tr>)}</tbody>
              </table></div>}
          </div>

          <div className="card mb-6">
            <div className="card-header"><span className="card-title">Auditable conditional certificate</span></div>
            <div style={{ marginBottom: 16, fontSize: 12, color: statusColors[status] || 'var(--text-primary)' }}>
              {pretty(status)} · Not a bank authenticity or legal fraud determination
            </div>
            <div className="table-wrap"><table>
              <thead><tr><th>Required field</th><th>Evidence status</th><th>Source witnesses</th></tr></thead>
              <tbody>{Object.entries(certificate.field_results).map(([key, value]) => (
                <tr key={key}>
                  <td>{pretty(key)}</td>
                  <td style={{ color: statusColors[value.status] }}>{pretty(value.status)}</td>
                  <td style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                    {value.witness_source_ids.join(', ') || 'No admissible source'}
                  </td>
                </tr>
              ))}</tbody>
            </table></div>
            {certificate.unresolved_fields.length > 0 &&
              <p style={{ marginTop: 14, fontSize: 12, color: 'var(--text-secondary)' }}>
                Unresolved fields: {certificate.unresolved_fields.join(', ')}
              </p>}
            <p style={{ marginTop: 14, fontSize: 11, color: 'var(--text-muted)', overflowWrap: 'anywhere' }}>
              Replay digest: {certificate.basis_sha256}
            </p>
          </div>
        </>
      )}
    </div>
  )
}
