import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Analysis from './pages/Analysis'
import GraphView from './pages/GraphView'
import './index.css'

function Layout({ children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">⧫</div>
          <span className="brand-name">Fraud<br />RAG</span>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">◈</span>
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/upload" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">⊕</span>
            <span>Upload</span>
          </NavLink>
          <NavLink to="/graph" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">⬡</span>
            <span>Knowledge Graph</span>
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <div className="status-dot online"></div>
          <span className="status-text">System Online</span>
        </div>
      </aside>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--surface)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border)',
            fontFamily: 'var(--font-mono)',
            fontSize: '12px',
          },
        }}
      />
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/analysis/:id" element={<Analysis />} />
          <Route path="/graph" element={<GraphView />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </React.StrictMode>
)
