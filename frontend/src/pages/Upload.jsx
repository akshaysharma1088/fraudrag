import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import api from '../utils/api'

const STATEMENT_TYPES = [
  { value: 'bank', label: 'Bank Statement' },
  { value: 'credit_card', label: 'Credit Card Statement' },
  { value: 'investment', label: 'Investment Statement' },
  { value: 'mortgage', label: 'Mortgage Statement' },
  { value: 'tax', label: 'Tax Document' },
  { value: 'payroll', label: 'Payroll / Pay Stub' },
]

const PIPELINE_STAGES = [
  { id: 'bronze', label: 'Bronze Layer', desc: 'OCR extraction & document hashing' },
  { id: 'silver', label: 'Silver Layer', desc: 'Entity normalization & balance validation' },
  { id: 'gold', label: 'Gold Layer', desc: 'Graph-RAG fraud scoring' },
  { id: 'complete', label: 'Analysis Complete', desc: 'Results ready for review' },
]

export default function Upload() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [customerId, setCustomerId] = useState('demo-001')
  const [statementType, setStatementType] = useState('bank')
  const [processing, setProcessing] = useState(false)
  const [stage, setStage] = useState(-1)
  const [error, setError] = useState(null)

  const onDrop = useCallback(accepted => {
    if (accepted[0]) { setFile(accepted[0]); setError(null) }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'image/*': ['.png', '.jpg', '.jpeg', '.tiff'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    maxSize: 20 * 1024 * 1024,
    multiple: false,
    onDropRejected: () => setError('Invalid file. Please upload a PDF, image, or DOCX under 20MB.'),
  })

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) { setError('Please select a file.'); return }
    if (!customerId.trim()) { setError('Customer ID is required.'); return }

    setProcessing(true)
    setStage(0)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('customer_id', customerId)
      formData.append('statement_type', statementType)

      // Animate through pipeline stages
      const stageTimer = (i) => setTimeout(() => setStage(i), i * 1800)
      stageTimer(1); stageTimer(2)

      const res = await api.post('/statements/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setStage(3)
      toast.success('Analysis complete!')
      setTimeout(() => navigate(`/analysis/${res.data.statement_id}`), 800)

    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Upload failed'
      setError(msg)
      toast.error(msg)
      setProcessing(false)
      setStage(-1)
    }
  }

  const formatSize = (bytes) => bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.round(bytes / 1024)} KB`

  return (
    <div className="page fade-up">
      <div className="page-header">
        <h1>Upload Statement</h1>
        <p>Run document through the Bronze → Silver → Gold Medallion pipeline</p>
      </div>

      <div className="grid-2" style={{ alignItems: 'flex-start' }}>
        {/* Upload Form */}
        <div>
          <form onSubmit={handleSubmit}>
            {/* Drop Zone */}
            <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`} style={{ marginBottom: 24 }}>
              <input {...getInputProps()} />
              {file ? (
                <div>
                  <div style={{ fontSize: 36, marginBottom: 12 }}>📄</div>
                  <p style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{file.name}</p>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent)' }}>{formatSize(file.size)} · {file.type || 'document'}</p>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>Click or drag to replace</p>
                </div>
              ) : (
                <div>
                  <div className="dropzone-icon">⊕</div>
                  <h3>{isDragActive ? 'Release to upload' : 'Drop statement here'}</h3>
                  <p style={{ marginTop: 8 }}>PDF · PNG · JPEG · DOCX · Max 20MB</p>
                </div>
              )}
            </div>

            {/* Fields */}
            <div className="form-group">
              <label className="form-label">Customer ID</label>
              <input className="input" value={customerId} onChange={e => setCustomerId(e.target.value)}
                placeholder="e.g. demo-001" disabled={processing} />
            </div>

            <div className="form-group">
              <label className="form-label">Statement Type</label>
              <select className="input" value={statementType} onChange={e => setStatementType(e.target.value)} disabled={processing}>
                {STATEMENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>

            {error && (
              <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '10px 14px', marginBottom: 16 }}>
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--risk-critical)' }}>{error}</p>
              </div>
            )}

            <button type="submit" className="btn btn-primary w-full" disabled={processing || !file}
              style={{ justifyContent: 'center', padding: '12px', fontSize: 14 }}>
              {processing ? (
                <><div className="spinner" style={{ width: 16, height: 16 }} /> Analyzing…</>
              ) : '⬡ Run Fraud Analysis'}
            </button>
          </form>
        </div>

        {/* Pipeline Status */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Medallion Pipeline</span>
            {stage >= 0 && <div className="spinner" style={{ width: 14, height: 14 }} />}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {PIPELINE_STAGES.map((s, i) => {
              const isDone = stage > i
              const isCurrent = stage === i
              const isPending = stage < i

              return (
                <div key={s.id} style={{ display: 'flex', gap: 16, paddingBottom: i < PIPELINE_STAGES.length - 1 ? 0 : 0 }}>
                  {/* Line connector */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24 }}>
                    <div style={{
                      width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: isDone ? 'var(--accent)' : isCurrent ? 'var(--accent-dim)' : 'var(--border)',
                      border: `2px solid ${isDone ? 'var(--accent)' : isCurrent ? 'var(--accent)' : 'var(--border-bright)'}`,
                      fontSize: 11, fontWeight: 700,
                      color: isDone ? '#000' : isCurrent ? 'var(--accent)' : 'var(--text-muted)',
                      transition: 'all 0.4s ease',
                      boxShadow: isCurrent ? '0 0 12px var(--accent)' : 'none',
                    }}>
                      {isDone ? '✓' : i + 1}
                    </div>
                    {i < PIPELINE_STAGES.length - 1 && (
                      <div style={{ width: 2, flex: 1, minHeight: 32, background: isDone ? 'var(--accent)' : 'var(--border)', opacity: isDone ? 0.5 : 1, transition: 'background 0.4s ease', margin: '2px 0' }} />
                    )}
                  </div>

                  <div style={{ paddingBottom: i < PIPELINE_STAGES.length - 1 ? 24 : 0, paddingTop: 2 }}>
                    <p style={{
                      fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700,
                      color: isDone ? 'var(--text-primary)' : isCurrent ? 'var(--accent)' : 'var(--text-muted)',
                      transition: 'color 0.3s',
                    }}>{s.label}</p>
                    <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{s.desc}</p>
                  </div>
                </div>
              )
            })}
          </div>

          <div style={{ marginTop: 24, padding: '14px', background: 'var(--bg-elevated)', borderRadius: 8, border: '1px solid var(--border)' }}>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              <span style={{ color: 'var(--accent)' }}>Graph-RAG pipeline</span> combines Neo4j knowledge graph traversal with ChromaDB semantic similarity to provide LLM-augmented fraud scoring with full explainability.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
