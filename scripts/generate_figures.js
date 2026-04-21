const fs = require('fs');
const path = require('path');

const outDir = path.join(__dirname, '..', 'docs', 'figures');
fs.mkdirSync(outDir, { recursive: true });

// ── Figure 1: End-to-End System Architecture ───────────────────────────────
const fig1 = `<svg width="700" height="560" viewBox="0 0 700 560" xmlns="http://www.w3.org/2000/svg" style="background:#fff;font-family:'Times New Roman',serif">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L8 5L1 8" fill="none" stroke="#555" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
  <!-- Title -->
  <text x="350" y="22" text-anchor="middle" font-size="11" font-weight="bold" fill="#111" font-family="Times New Roman">Fig. 1. FraudRAG End-to-End System Architecture</text>

  <!-- ── React UI Box ── -->
  <rect x="20" y="40" width="110" height="44" rx="6" fill="#EEF4FB" stroke="#5B8FCA" stroke-width="1"/>
  <text x="75" y="58" text-anchor="middle" font-size="10" font-weight="bold" fill="#1A4D8F">React UI</text>
  <text x="75" y="73" text-anchor="middle" font-size="9" fill="#3A6FAA">Upload / Dashboard</text>

  <!-- Arrow: UI → API -->
  <line x1="130" y1="62" x2="168" y2="62" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>
  <text x="149" y="57" text-anchor="middle" font-size="8" fill="#888">HTTP</text>

  <!-- ── FastAPI Box ── -->
  <rect x="170" y="40" width="120" height="44" rx="6" fill="#EDF7EE" stroke="#4F9A61" stroke-width="1"/>
  <text x="230" y="58" text-anchor="middle" font-size="10" font-weight="bold" fill="#1A5E2E">FastAPI Backend</text>
  <text x="230" y="73" text-anchor="middle" font-size="9" fill="#317840">REST + WebSocket</text>

  <!-- Arrow: API → Pipeline -->
  <line x1="290" y1="62" x2="328" y2="62" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- ── Medallion Pipeline outer box ── -->
  <rect x="330" y="35" width="345" height="200" rx="10" fill="#FAFAFA" stroke="#999" stroke-width="1" stroke-dasharray="5,3"/>
  <text x="502" y="52" text-anchor="middle" font-size="10" font-weight="bold" fill="#444">Medallion Pipeline</text>

  <!-- Bronze -->
  <rect x="344" y="60" width="96" height="60" rx="6" fill="#FEF0E0" stroke="#D4800A" stroke-width="1"/>
  <text x="392" y="78" text-anchor="middle" font-size="10" font-weight="bold" fill="#7A4500">Bronze</text>
  <text x="392" y="92" text-anchor="middle" font-size="8.5" fill="#A05A10">OCR · Hash</text>
  <text x="392" y="106" text-anchor="middle" font-size="8.5" fill="#A05A10">Provenance</text>

  <!-- Arrow Bronze → Silver -->
  <line x1="440" y1="90" x2="464" y2="90" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Silver -->
  <rect x="466" y="60" width="96" height="60" rx="6" fill="#ECF5FB" stroke="#2A7FBD" stroke-width="1"/>
  <text x="514" y="78" text-anchor="middle" font-size="10" font-weight="bold" fill="#0D4A7A">Silver</text>
  <text x="514" y="92" text-anchor="middle" font-size="8.5" fill="#1F6098">NER · Validate</text>
  <text x="514" y="106" text-anchor="middle" font-size="8.5" fill="#1F6098">Balance Check</text>

  <!-- Arrow Silver → Gold -->
  <line x1="562" y1="90" x2="586" y2="90" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Gold -->
  <rect x="588" y="60" width="78" height="60" rx="6" fill="#FFF8E8" stroke="#B8960A" stroke-width="1"/>
  <text x="627" y="78" text-anchor="middle" font-size="10" font-weight="bold" fill="#6B5500">Gold</text>
  <text x="627" y="92" text-anchor="middle" font-size="8.5" fill="#8A6E00">Features</text>
  <text x="627" y="106" text-anchor="middle" font-size="8.5" fill="#8A6E00">RAG Score</text>

  <!-- Arrow: Gold → Graph-RAG box -->
  <line x1="627" y1="120" x2="627" y2="145" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Graph-RAG Service box (inside pipeline) -->
  <rect x="344" y="148" width="322" height="78" rx="6" fill="#F3EEF9" stroke="#7A52B5" stroke-width="1"/>
  <text x="505" y="166" text-anchor="middle" font-size="10" font-weight="bold" fill="#4A2880">Graph-RAG Service</text>
  <text x="408" y="182" text-anchor="middle" font-size="8.5" fill="#6040A0">① Neo4j k-hop traversal</text>
  <text x="408" y="196" text-anchor="middle" font-size="8.5" fill="#6040A0">② ChromaDB similarity</text>
  <text x="600" y="182" text-anchor="middle" font-size="8.5" fill="#6040A0">③ Prompt augment</text>
  <text x="600" y="196" text-anchor="middle" font-size="8.5" fill="#6040A0">④ LLM reasoning</text>
  <line x1="486" y1="163" x2="486" y2="210" stroke="#C0A0E0" stroke-width="0.5" stroke-dasharray="3,2"/>

  <!-- Arrow: Pipeline result → FraudAnalysis -->
  <line x1="330" y1="190" x2="295" y2="190" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- ── FraudAnalysis Aggregate ── -->
  <rect x="170" y="165" width="120" height="50" rx="6" fill="#FEF0F0" stroke="#C0392B" stroke-width="1"/>
  <text x="230" y="183" text-anchor="middle" font-size="10" font-weight="bold" fill="#7B1A11">FraudAnalysis</text>
  <text x="230" y="197" text-anchor="middle" font-size="8.5" fill="#A52819">Score · Indicators</text>
  <text x="230" y="210" text-anchor="middle" font-size="8.5" fill="#A52819">Reasoning</text>

  <!-- Arrow: FraudAnalysis → UI -->
  <line x1="170" y1="190" x2="132" y2="190" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>
  <line x1="75" y1="190" x2="75" y2="84" stroke="#555" stroke-width="0.8" stroke-dasharray="4,3" marker-end="url(#arr)"/>

  <!-- ── Data Stores Row ── -->
  <!-- Neo4j -->
  <rect x="20" y="290" width="130" height="56" rx="6" fill="#E6F3F0" stroke="#27927A" stroke-width="1"/>
  <text x="85" y="310" text-anchor="middle" font-size="10" font-weight="bold" fill="#0D5E4E">Neo4j 5.20</text>
  <text x="85" y="324" text-anchor="middle" font-size="8.5" fill="#1D7A65">Knowledge Graph</text>
  <text x="85" y="337" text-anchor="middle" font-size="8.5" fill="#1D7A65">Customer · Pattern</text>

  <!-- ChromaDB -->
  <rect x="170" y="290" width="130" height="56" rx="6" fill="#EFF2FB" stroke="#4A60C0" stroke-width="1"/>
  <text x="235" y="310" text-anchor="middle" font-size="10" font-weight="bold" fill="#1A2E80">ChromaDB</text>
  <text x="235" y="324" text-anchor="middle" font-size="8.5" fill="#2E45A0">Vector Store</text>
  <text x="235" y="337" text-anchor="middle" font-size="8.5" fill="#2E45A0">Embeddings</text>

  <!-- PostgreSQL -->
  <rect x="320" y="290" width="130" height="56" rx="6" fill="#F0EFF8" stroke="#6B5EA8" stroke-width="1"/>
  <text x="385" y="310" text-anchor="middle" font-size="10" font-weight="bold" fill="#3A2870">PostgreSQL 16</text>
  <text x="385" y="324" text-anchor="middle" font-size="8.5" fill="#5040A0">Metadata · Audit</text>
  <text x="385" y="337" text-anchor="middle" font-size="8.5" fill="#5040A0">Review Records</text>

  <!-- Redis -->
  <rect x="470" y="290" width="100" height="56" rx="6" fill="#FEF0ED" stroke="#C0391A" stroke-width="1"/>
  <text x="520" y="310" text-anchor="middle" font-size="10" font-weight="bold" fill="#7A1A08">Redis 7</text>
  <text x="520" y="324" text-anchor="middle" font-size="8.5" fill="#A02810">Cache</text>
  <text x="520" y="337" text-anchor="middle" font-size="8.5" fill="#A02810">Session</text>

  <!-- AWS -->
  <rect x="590" y="290" width="90" height="56" rx="6" fill="#FFF3E0" stroke="#C06000" stroke-width="1"/>
  <text x="635" y="310" text-anchor="middle" font-size="10" font-weight="bold" fill="#7A3800">AWS S3</text>
  <text x="635" y="324" text-anchor="middle" font-size="8.5" fill="#A05000">Delta Lake</text>
  <text x="635" y="337" text-anchor="middle" font-size="8.5" fill="#A05000">Bronze/Silver/Gold</text>

  <!-- Connector lines: RAG Service → Stores -->
  <line x1="392" y1="226" x2="392" y2="260" stroke="#7A52B5" stroke-width="0.8" stroke-dasharray="3,2"/>
  <line x1="392" y1="260" x2="85" y2="260" stroke="#7A52B5" stroke-width="0.8" stroke-dasharray="3,2"/>
  <line x1="85" y1="260" x2="85" y2="290" stroke="#27927A" stroke-width="1" marker-end="url(#arr)"/>
  <line x1="392" y1="260" x2="235" y2="260" stroke="#7A52B5" stroke-width="0.8" stroke-dasharray="3,2"/>
  <line x1="235" y1="260" x2="235" y2="290" stroke="#4A60C0" stroke-width="1" marker-end="url(#arr)"/>
  <line x1="505" y1="226" x2="505" y2="260" stroke="#7A52B5" stroke-width="0.8" stroke-dasharray="3,2"/>
  <line x1="505" y1="260" x2="385" y2="260" stroke="#7A52B5" stroke-width="0.8" stroke-dasharray="3,2"/>
  <line x1="385" y1="260" x2="385" y2="290" stroke="#6B5EA8" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Pipeline → AWS -->
  <line x1="627" y1="235" x2="627" y2="260" stroke="#C06000" stroke-width="0.8" stroke-dasharray="3,2"/>
  <line x1="627" y1="260" x2="635" y2="260" stroke="#C06000" stroke-width="0.8" stroke-dasharray="3,2"/>
  <line x1="635" y1="260" x2="635" y2="290" stroke="#C06000" stroke-width="1" marker-end="url(#arr)"/>

  <!-- ── Monitoring Row ── -->
  <rect x="20" y="385" width="150" height="44" rx="6" fill="#F5F5F5" stroke="#999" stroke-width="0.8"/>
  <text x="95" y="403" text-anchor="middle" font-size="10" font-weight="bold" fill="#333">Prometheus</text>
  <text x="95" y="418" text-anchor="middle" font-size="8.5" fill="#666">Metrics · Alerts</text>

  <rect x="190" y="385" width="130" height="44" rx="6" fill="#F5F5F5" stroke="#999" stroke-width="0.8"/>
  <text x="255" y="403" text-anchor="middle" font-size="10" font-weight="bold" fill="#333">Grafana</text>
  <text x="255" y="418" text-anchor="middle" font-size="8.5" fill="#666">Dashboards · SLAs</text>

  <!-- Arrow API → Prometheus -->
  <line x1="230" y1="215" x2="230" y2="250" stroke="#888" stroke-width="0.6" stroke-dasharray="2,3"/>
  <line x1="230" y1="250" x2="95" y2="250" stroke="#888" stroke-width="0.6" stroke-dasharray="2,3"/>
  <line x1="95" y1="250" x2="95" y2="385" stroke="#888" stroke-width="0.7" stroke-dasharray="2,3" marker-end="url(#arr)"/>

  <!-- Legend -->
  <rect x="20" y="450" width="660" height="90" rx="6" fill="#FAFAFA" stroke="#CCC" stroke-width="0.5"/>
  <text x="350" y="466" text-anchor="middle" font-size="9" font-weight="bold" fill="#444">Legend</text>
  <!-- Row 1 -->
  <rect x="35" y="474" width="14" height="10" rx="2" fill="#EEF4FB" stroke="#5B8FCA" stroke-width="0.8"/>
  <text x="55" y="483" font-size="8.5" fill="#333">UI / API Layer</text>
  <rect x="145" y="474" width="14" height="10" rx="2" fill="#FEF0E0" stroke="#D4800A" stroke-width="0.8"/>
  <text x="165" y="483" font-size="8.5" fill="#333">Medallion Pipeline</text>
  <rect x="285" y="474" width="14" height="10" rx="2" fill="#F3EEF9" stroke="#7A52B5" stroke-width="0.8"/>
  <text x="305" y="483" font-size="8.5" fill="#333">Graph-RAG Service</text>
  <rect x="430" y="474" width="14" height="10" rx="2" fill="#FEF0F0" stroke="#C0392B" stroke-width="0.8"/>
  <text x="450" y="483" font-size="8.5" fill="#333">Domain Aggregate</text>
  <rect x="570" y="474" width="14" height="10" rx="2" fill="#F5F5F5" stroke="#999" stroke-width="0.8"/>
  <text x="590" y="483" font-size="8.5" fill="#333">Monitoring</text>
  <!-- Row 2 -->
  <rect x="35" y="494" width="14" height="10" rx="2" fill="#E6F3F0" stroke="#27927A" stroke-width="0.8"/>
  <text x="55" y="503" font-size="8.5" fill="#333">Graph DB (Neo4j)</text>
  <rect x="145" y="494" width="14" height="10" rx="2" fill="#EFF2FB" stroke="#4A60C0" stroke-width="0.8"/>
  <text x="165" y="503" font-size="8.5" fill="#333">Vector DB (ChromaDB)</text>
  <rect x="285" y="494" width="14" height="10" rx="2" fill="#F0EFF8" stroke="#6B5EA8" stroke-width="0.8"/>
  <text x="305" y="503" font-size="8.5" fill="#333">Metadata DB (PostgreSQL)</text>
  <rect x="430" y="494" width="14" height="10" rx="2" fill="#FFF3E0" stroke="#C06000" stroke-width="0.8"/>
  <text x="450" y="503" font-size="8.5" fill="#333">Object Store (AWS S3)</text>
  <line x1="35" y1="519" x2="49" y2="519" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>
  <text x="55" y="523" font-size="8.5" fill="#333">Synchronous call</text>
  <line x1="145" y1="519" x2="159" y2="519" stroke="#555" stroke-width="0.8" stroke-dasharray="3,2"/>
  <text x="165" y="523" font-size="8.5" fill="#333">Async / observed</text>
  <line x1="285" y1="519" x2="299" y2="519" stroke="#7A52B5" stroke-width="0.8" stroke-dasharray="3,2"/>
  <text x="305" y="523" font-size="8.5" fill="#333">RAG retrieval path</text>
</svg>`;

fs.writeFileSync(path.join(outDir, 'fig1_system_architecture.svg'), fig1);
console.log('fig1 written');

// ── Figure 2: Medallion Architecture Data Flow ──────────────────────────────
const fig2 = `<svg width="700" height="400" viewBox="0 0 700 400" xmlns="http://www.w3.org/2000/svg" style="background:#fff;font-family:'Times New Roman',serif">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L8 5L1 8" fill="none" stroke="#555" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
  <text x="350" y="22" text-anchor="middle" font-size="11" font-weight="bold" fill="#111">Fig. 2. Medallion Architecture Data Flow (Bronze → Silver → Gold)</text>

  <!-- Input document -->
  <rect x="20" y="80" width="100" height="50" rx="6" fill="#F5F5F5" stroke="#888" stroke-width="1"/>
  <text x="70" y="101" text-anchor="middle" font-size="10" font-weight="bold" fill="#333">Uploaded</text>
  <text x="70" y="116" text-anchor="middle" font-size="9" fill="#555">Statement</text>
  <text x="70" y="129" text-anchor="middle" font-size="8" fill="#777">PDF/IMG/DOCX</text>
  <line x1="120" y1="105" x2="148" y2="105" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Bronze Layer -->
  <rect x="150" y="55" width="160" height="165" rx="8" fill="#FEF3E4" stroke="#D4800A" stroke-width="1.5"/>
  <text x="230" y="75" text-anchor="middle" font-size="11" font-weight="bold" fill="#7A4500">🥉 Bronze Layer</text>
  <rect x="162" y="82" width="136" height="30" rx="4" fill="#fff" stroke="#D4800A" stroke-width="0.6"/>
  <text x="230" y="101" text-anchor="middle" font-size="9" fill="#5A3000">SHA-256 fingerprint</text>
  <rect x="162" y="118" width="136" height="30" rx="4" fill="#fff" stroke="#D4800A" stroke-width="0.6"/>
  <text x="230" y="137" text-anchor="middle" font-size="9" fill="#5A3000">OCR / text extraction</text>
  <rect x="162" y="154" width="136" height="30" rx="4" fill="#fff" stroke="#D4800A" stroke-width="0.6"/>
  <text x="230" y="173" text-anchor="middle" font-size="9" fill="#5A3000">Provenance metadata</text>

  <!-- Bronze outputs: hash + raw text -->
  <text x="230" y="230" text-anchor="middle" font-size="8.5" fill="#D4800A">RawStatement aggregate</text>
  <rect x="165" y="235" width="130" height="22" rx="3" fill="#FEF0D0" stroke="#D4800A" stroke-width="0.6"/>
  <text x="230" y="249" text-anchor="middle" font-size="8.5" fill="#7A4500">id · hash · raw_text · ocr_conf</text>

  <!-- Arrow Bronze → Silver -->
  <line x1="310" y1="137" x2="338" y2="137" stroke="#555" stroke-width="1.2" marker-end="url(#arr)"/>

  <!-- Silver Layer -->
  <rect x="340" y="55" width="170" height="165" rx="8" fill="#EAF3FB" stroke="#2A7FBD" stroke-width="1.5"/>
  <text x="425" y="75" text-anchor="middle" font-size="11" font-weight="bold" fill="#0D4A7A">🥈 Silver Layer</text>
  <rect x="352" y="82" width="146" height="30" rx="4" fill="#fff" stroke="#2A7FBD" stroke-width="0.6"/>
  <text x="425" y="101" text-anchor="middle" font-size="9" fill="#0D4A7A">NER · entity extraction</text>
  <rect x="352" y="118" width="146" height="30" rx="4" fill="#fff" stroke="#2A7FBD" stroke-width="0.6"/>
  <text x="425" y="133" text-anchor="middle" font-size="8.5" fill="#0D4A7A">Balance arithmetic check</text>
  <text x="425" y="146" text-anchor="middle" font-size="8" fill="#C0392B">open + Σcr − Σdr = close</text>
  <rect x="352" y="154" width="146" height="30" rx="4" fill="#fff" stroke="#2A7FBD" stroke-width="0.6"/>
  <text x="425" y="173" text-anchor="middle" font-size="9" fill="#0D4A7A">Quality score (0–1)</text>

  <text x="425" y="230" text-anchor="middle" font-size="8.5" fill="#2A7FBD">NormalizedStatement aggregate</text>
  <rect x="352" y="235" width="146" height="22" rx="3" fill="#D5EAF8" stroke="#2A7FBD" stroke-width="0.6"/>
  <text x="425" y="249" text-anchor="middle" font-size="8.5" fill="#0D4A7A">entities · transactions · quality</text>

  <!-- Arrow Silver → Gold -->
  <line x1="510" y1="137" x2="538" y2="137" stroke="#555" stroke-width="1.2" marker-end="url(#arr)"/>

  <!-- Gold Layer -->
  <rect x="540" y="55" width="148" height="165" rx="8" fill="#FFF8E4" stroke="#B8960A" stroke-width="1.5"/>
  <text x="614" y="75" text-anchor="middle" font-size="11" font-weight="bold" fill="#6B5500">🥇 Gold Layer</text>
  <rect x="552" y="82" width="124" height="30" rx="4" fill="#fff" stroke="#B8960A" stroke-width="0.6"/>
  <text x="614" y="101" text-anchor="middle" font-size="9" fill="#6B5500">Feature engineering</text>
  <rect x="552" y="118" width="124" height="30" rx="4" fill="#fff" stroke="#B8960A" stroke-width="0.6"/>
  <text x="614" y="133" text-anchor="middle" font-size="8.5" fill="#6B5500">Graph-RAG fraud score</text>
  <text x="614" y="146" text-anchor="middle" font-size="8" fill="#B8960A">LLM reasoning</text>
  <rect x="552" y="154" width="124" height="30" rx="4" fill="#fff" stroke="#B8960A" stroke-width="0.6"/>
  <text x="614" y="173" text-anchor="middle" font-size="9" fill="#6B5500">Analyst review verdict</text>

  <text x="614" y="230" text-anchor="middle" font-size="8.5" fill="#B8960A">FraudAnalysis aggregate</text>
  <rect x="552" y="235" width="124" height="22" rx="3" fill="#FFF0CC" stroke="#B8960A" stroke-width="0.6"/>
  <text x="614" y="249" text-anchor="middle" font-size="8.5" fill="#6B5500">score · indicators · reasoning</text>

  <!-- Bottom: data quality checks row -->
  <rect x="20" y="285" width="660" height="90" rx="6" fill="#F9F9F9" stroke="#CCC" stroke-width="0.5"/>
  <text x="350" y="302" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#333">Data Quality Gates (enforced at each layer boundary)</text>

  <rect x="35" y="312" width="170" height="50" rx="4" fill="#FEF3E4" stroke="#D4800A" stroke-width="0.7"/>
  <text x="120" y="328" text-anchor="middle" font-size="8.5" font-weight="bold" fill="#7A4500">Bronze → Silver gate</text>
  <text x="120" y="341" text-anchor="middle" font-size="8" fill="#A05000">OCR confidence ≥ 0.6</text>
  <text x="120" y="354" text-anchor="middle" font-size="8" fill="#A05000">Hash uniqueness check</text>

  <rect x="220" y="312" width="240" height="50" rx="4" fill="#EAF3FB" stroke="#2A7FBD" stroke-width="0.7"/>
  <text x="340" y="328" text-anchor="middle" font-size="8.5" font-weight="bold" fill="#0D4A7A">Silver → Gold gate</text>
  <text x="340" y="341" text-anchor="middle" font-size="8" fill="#1A5E96">|open + Σcr − Σdr − close| ≤ $0.50</text>
  <text x="340" y="354" text-anchor="middle" font-size="8" fill="#1A5E96">Quality score ≥ 0.40 required</text>

  <rect x="475" y="312" width="190" height="50" rx="4" fill="#FFF8E4" stroke="#B8960A" stroke-width="0.7"/>
  <text x="570" y="328" text-anchor="middle" font-size="8.5" font-weight="bold" fill="#6B5500">Gold output</text>
  <text x="570" y="341" text-anchor="middle" font-size="8" fill="#8A7000">Fraud score ∈ [0, 1]</text>
  <text x="570" y="354" text-anchor="middle" font-size="8" fill="#8A7000">risk_level ∈ {minimal…critical}</text>
</svg>`;

fs.writeFileSync(path.join(outDir, 'fig2_medallion_pipeline.svg'), fig2);
console.log('fig2 written');

// ── Figure 3: Knowledge Graph Schema ───────────────────────────────────────
const fig3 = `<svg width="700" height="440" viewBox="0 0 700 440" xmlns="http://www.w3.org/2000/svg" style="background:#fff;font-family:'Times New Roman',serif">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L8 5L1 8" fill="none" stroke="#777" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <marker id="arr2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L8 5L1 8" fill="none" stroke="#C0392B" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
  <text x="350" y="22" text-anchor="middle" font-size="11" font-weight="bold" fill="#111">Fig. 3. FraudRAG Knowledge Graph Schema (Neo4j Property Graph)</text>

  <!-- Customer node (center-left) -->
  <ellipse cx="170" cy="170" rx="70" ry="38" fill="#E6F3F0" stroke="#27927A" stroke-width="1.5"/>
  <text x="170" y="165" text-anchor="middle" font-size="10" font-weight="bold" fill="#0D5E4E">:Customer</text>
  <text x="170" y="179" text-anchor="middle" font-size="8.5" fill="#1D7A65">id · name · risk_score</text>
  <text x="170" y="191" text-anchor="middle" font-size="8" fill="#3A9A80">fraud_history_count</text>

  <!-- Institution node (top-right) -->
  <ellipse cx="520" cy="120" rx="80" ry="36" fill="#EFF2FB" stroke="#4A60C0" stroke-width="1.5"/>
  <text x="520" y="115" text-anchor="middle" font-size="10" font-weight="bold" fill="#1A2E80">:Institution</text>
  <text x="520" y="129" text-anchor="middle" font-size="8.5" fill="#2E45A0">id · name · type</text>
  <text x="520" y="141" text-anchor="middle" font-size="8" fill="#4A60C0">routing_number_hash</text>

  <!-- Statement node (center-right) -->
  <ellipse cx="520" cy="255" rx="80" ry="38" fill="#FEF0F0" stroke="#C0392B" stroke-width="1.5"/>
  <text x="520" y="248" text-anchor="middle" font-size="10" font-weight="bold" fill="#7B1A11">:Statement</text>
  <text x="520" y="262" text-anchor="middle" font-size="8.5" fill="#A52819">id · period · fraud_score</text>
  <text x="520" y="274" text-anchor="middle" font-size="8" fill="#C0392B">fraud_flagged</text>

  <!-- FraudPattern node (bottom-center) -->
  <ellipse cx="350" cy="360" rx="80" ry="36" fill="#FFF8E8" stroke="#B8960A" stroke-width="1.5"/>
  <text x="350" y="355" text-anchor="middle" font-size="10" font-weight="bold" fill="#6B5500">:FraudPattern</text>
  <text x="350" y="369" text-anchor="middle" font-size="8.5" fill="#8A7000">id · pattern_name · type</text>
  <text x="350" y="381" text-anchor="middle" font-size="8" fill="#B8960A">frequency · embedding</text>

  <!-- Transaction node (bottom-left) -->
  <ellipse cx="130" cy="330" rx="68" ry="34" fill="#F3EEF9" stroke="#7A52B5" stroke-width="1.5"/>
  <text x="130" y="325" text-anchor="middle" font-size="10" font-weight="bold" fill="#4A2880">:Transaction</text>
  <text x="130" y="339" text-anchor="middle" font-size="8.5" fill="#6040A0">id · date · amount</text>
  <text x="130" y="351" text-anchor="middle" font-size="8" fill="#7A52B5">description</text>

  <!-- Relationships -->
  <!-- Customer -[FILED]-> Statement -->
  <path d="M220 185 Q370 210 438 247" fill="none" stroke="#777" stroke-width="1.2" marker-end="url(#arr)"/>
  <text x="330" y="208" text-anchor="middle" font-size="8.5" fill="#555" transform="rotate(-8,330,208)">FILED</text>

  <!-- Customer -[HAS_ACCOUNT]-> Institution -->
  <path d="M215 148 Q370 80 440 112" fill="none" stroke="#777" stroke-width="1.2" marker-end="url(#arr)"/>
  <text x="330" y="94" text-anchor="middle" font-size="8.5" fill="#555" transform="rotate(-15,330,94)">HAS_ACCOUNT</text>

  <!-- Statement -[ISSUED_BY]-> Institution -->
  <path d="M520 217 L520 158" fill="none" stroke="#777" stroke-width="1.2" marker-end="url(#arr)"/>
  <text x="534" y="188" text-anchor="start" font-size="8.5" fill="#555">ISSUED_BY</text>

  <!-- Customer -[MATCHES_PATTERN]-> FraudPattern -->
  <path d="M175 208 Q220 300 268 348" fill="none" stroke="#C0392B" stroke-width="1.2" stroke-dasharray="5,3" marker-end="url(#arr2)"/>
  <text x="200" y="296" text-anchor="middle" font-size="8" fill="#C0392B" transform="rotate(60,200,296)">MATCHES</text>
  <text x="207" y="308" text-anchor="middle" font-size="8" fill="#C0392B" transform="rotate(60,207,308)">_PATTERN</text>

  <!-- Statement -[DETECTED_IN]-> FraudPattern -->
  <path d="M460 278 Q410 325 432 348" fill="none" stroke="#C0392B" stroke-width="1.2" stroke-dasharray="5,3" marker-end="url(#arr2)"/>
  <text x="432" y="308" text-anchor="middle" font-size="8.5" fill="#C0392B">DETECTED_IN</text>

  <!-- Statement -[CONTAINS]-> Transaction -->
  <path d="M450 268 Q290 305 198 320" fill="none" stroke="#777" stroke-width="1.2" marker-end="url(#arr)"/>
  <text x="318" y="282" text-anchor="middle" font-size="8.5" fill="#555">CONTAINS</text>

  <!-- Customer -[LINKED_TO]-> Customer (self-loop / fraud ring) -->
  <path d="M100 170 Q60 140 80 170 Q95 195 115 185" fill="none" stroke="#C0392B" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arr2)"/>
  <text x="38" y="163" text-anchor="middle" font-size="7.5" fill="#C0392B">LINKED_TO</text>
  <text x="38" y="174" text-anchor="middle" font-size="7.5" fill="#C0392B">(fraud ring)</text>

  <!-- Legend -->
  <rect x="20" y="390" width="660" height="40" rx="5" fill="#FAFAFA" stroke="#CCC" stroke-width="0.5"/>
  <text x="350" y="404" text-anchor="middle" font-size="9" font-weight="bold" fill="#444">Legend</text>
  <ellipse cx="48" cy="418" rx="12" ry="7" fill="#E6F3F0" stroke="#27927A" stroke-width="0.8"/>
  <text x="66" y="422" font-size="8.5" fill="#333">Node type</text>
  <line x1="135" y1="418" x2="155" y2="418" stroke="#777" stroke-width="1.2" marker-end="url(#arr)"/>
  <text x="162" y="422" font-size="8.5" fill="#333">Structural edge</text>
  <line x1="285" y1="418" x2="305" y2="418" stroke="#C0392B" stroke-width="1.2" stroke-dasharray="4,3" marker-end="url(#arr2)"/>
  <text x="312" y="422" font-size="8.5" fill="#333">Fraud detection edge</text>
  <line x1="455" y1="418" x2="475" y2="418" stroke="#C0392B" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arr2)"/>
  <text x="482" y="422" font-size="8.5" fill="#333">Self-referential (fraud ring)</text>
</svg>`;

fs.writeFileSync(path.join(outDir, 'fig3_knowledge_graph_schema.svg'), fig3);
console.log('fig3 written');

// ── Figure 4: Graph-RAG Inference Pipeline ────────────────────────────────
const fig4 = `<svg width="700" height="420" viewBox="0 0 700 420" xmlns="http://www.w3.org/2000/svg" style="background:#fff;font-family:'Times New Roman',serif">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L8 5L1 8" fill="none" stroke="#555" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
  <text x="350" y="22" text-anchor="middle" font-size="11" font-weight="bold" fill="#111">Fig. 4. Graph-RAG Inference Pipeline (Gold Layer)</text>

  <!-- Step labels -->
  <!-- Step 1 box -->
  <rect x="20" y="50" width="140" height="80" rx="8" fill="#E6F3F0" stroke="#27927A" stroke-width="1.5"/>
  <text x="90" y="72" text-anchor="middle" font-size="10" font-weight="bold" fill="#0D5E4E">① Neo4j Retrieval</text>
  <text x="90" y="88" text-anchor="middle" font-size="8.5" fill="#1D7A65">k-hop graph traversal</text>
  <text x="90" y="102" text-anchor="middle" font-size="8" fill="#3A9A80">MATCH (c)-[*1..2]-(n)</text>
  <text x="90" y="116" text-anchor="middle" font-size="8" fill="#3A9A80">Customer context</text>

  <line x1="160" y1="90" x2="188" y2="90" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Step 2 box -->
  <rect x="190" y="50" width="140" height="80" rx="8" fill="#EFF2FB" stroke="#4A60C0" stroke-width="1.5"/>
  <text x="260" y="72" text-anchor="middle" font-size="10" font-weight="bold" fill="#1A2E80">② Vector Retrieval</text>
  <text x="260" y="88" text-anchor="middle" font-size="8.5" fill="#2E45A0">Statement embedding</text>
  <text x="260" y="102" text-anchor="middle" font-size="8.5" fill="#2E45A0">ChromaDB ANN</text>
  <text x="260" y="116" text-anchor="middle" font-size="8" fill="#4A60C0">top-k=4 similar docs</text>

  <line x1="330" y1="90" x2="358" y2="90" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Step 3 box (Prompt construction) -->
  <rect x="360" y="35" width="155" height="115" rx="8" fill="#F3EEF9" stroke="#7A52B5" stroke-width="1.5"/>
  <text x="437" y="56" text-anchor="middle" font-size="10" font-weight="bold" fill="#4A2880">③ Prompt Augmentation</text>
  <text x="437" y="72" text-anchor="middle" font-size="8.5" fill="#6040A0">[SYSTEM] Forensic analyst</text>
  <text x="437" y="86" text-anchor="middle" font-size="8.5" fill="#6040A0">[GRAPH] Customer history</text>
  <text x="437" y="100" text-anchor="middle" font-size="8.5" fill="#6040A0">[VECTOR] Prior fraud cases</text>
  <text x="437" y="114" text-anchor="middle" font-size="8.5" fill="#6040A0">[DOCUMENT] Statement text</text>
  <text x="437" y="128" text-anchor="middle" font-size="8.5" fill="#6040A0">[REFERENCE] Warehouse copy</text>

  <line x1="515" y1="92" x2="543" y2="92" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Step 4 box (LLM) -->
  <rect x="545" y="50" width="135" height="80" rx="8" fill="#FFF0E8" stroke="#C06020" stroke-width="1.5"/>
  <text x="612" y="71" text-anchor="middle" font-size="10" font-weight="bold" fill="#7A3000">④ LLM Inference</text>
  <text x="612" y="86" text-anchor="middle" font-size="8.5" fill="#A04010">GPT-4o / Claude</text>
  <text x="612" y="100" text-anchor="middle" font-size="8.5" fill="#A04010">temperature=0</text>
  <text x="612" y="114" text-anchor="middle" font-size="8.5" fill="#A04010">Structured JSON out</text>

  <!-- Arrow down from LLM to output -->
  <line x1="612" y1="130" x2="612" y2="158" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Output box -->
  <rect x="545" y="160" width="135" height="110" rx="8" fill="#FEF0F0" stroke="#C0392B" stroke-width="1.5"/>
  <text x="612" y="180" text-anchor="middle" font-size="10" font-weight="bold" fill="#7B1A11">FraudAnalysis</text>
  <text x="612" y="196" text-anchor="middle" font-size="8.5" fill="#A52819">fraud_score ∈ [0,1]</text>
  <text x="612" y="210" text-anchor="middle" font-size="8.5" fill="#A52819">risk_level</text>
  <text x="612" y="224" text-anchor="middle" font-size="8.5" fill="#A52819">indicators[ ]</text>
  <text x="612" y="238" text-anchor="middle" font-size="8.5" fill="#A52819">discrepancies[ ]</text>
  <text x="612" y="252" text-anchor="middle" font-size="8.5" fill="#A52819">llm_reasoning</text>

  <!-- Feedback: high risk → store to graph -->
  <line x1="545" y1="215" x2="170" y2="215" stroke="#C0392B" stroke-width="0.8" stroke-dasharray="5,3" marker-end="url(#arr)"/>
  <text x="357" y="210" text-anchor="middle" font-size="8.5" fill="#C0392B">If HIGH/CRITICAL → persist pattern to Neo4j · update risk_score</text>

  <!-- Update vector store -->
  <line x1="545" y1="240" x2="300" y2="240" stroke="#4A60C0" stroke-width="0.8" stroke-dasharray="5,3" marker-end="url(#arr)"/>
  <text x="420" y="235" text-anchor="middle" font-size="8.5" fill="#4A60C0">Index to ChromaDB</text>

  <!-- Warehouse reference feed -->
  <rect x="20" y="160" width="140" height="54" rx="6" fill="#F8F8E8" stroke="#888810" stroke-width="1"/>
  <text x="90" y="179" text-anchor="middle" font-size="10" font-weight="bold" fill="#504400">Data Warehouse</text>
  <text x="90" y="193" text-anchor="middle" font-size="8.5" fill="#707020">Authoritative copy</text>
  <text x="90" y="206" text-anchor="middle" font-size="8.5" fill="#707020">of statement</text>

  <!-- Arrow DW → Prompt -->
  <path d="M160 188 Q260 188 358 105" fill="none" stroke="#888810" stroke-width="0.8" stroke-dasharray="4,3" marker-end="url(#arr)"/>
  <text x="255" y="165" text-anchor="middle" font-size="8" fill="#888810">warehouse_reference</text>

  <!-- Metrics / Monitoring -->
  <rect x="20" y="285" width="660" height="115" rx="6" fill="#FAFAFA" stroke="#CCC" stroke-width="0.5"/>
  <text x="350" y="304" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#333">Pipeline Observability</text>

  <rect x="35" y="312" width="190" height="74" rx="5" fill="#F0F0F0" stroke="#999" stroke-width="0.5"/>
  <text x="130" y="328" text-anchor="middle" font-size="8.5" font-weight="bold" fill="#333">Latency breakdown (median)</text>
  <text x="130" y="342" text-anchor="middle" font-size="8" fill="#555">OCR (digital PDF): ~600 ms</text>
  <text x="130" y="355" text-anchor="middle" font-size="8" fill="#555">OCR (scanned image): ~1800 ms</text>
  <text x="130" y="368" text-anchor="middle" font-size="8" fill="#555">Graph + Vector retrieval: &lt;200 ms</text>
  <text x="130" y="381" text-anchor="middle" font-size="8" fill="#555">LLM inference (GPT-4o): ~1900 ms</text>

  <rect x="242" y="312" width="200" height="74" rx="5" fill="#F0F0F0" stroke="#999" stroke-width="0.5"/>
  <text x="342" y="328" text-anchor="middle" font-size="8.5" font-weight="bold" fill="#333">Prometheus metrics</text>
  <text x="342" y="342" text-anchor="middle" font-size="8" fill="#555">fraudrag_requests_total</text>
  <text x="342" y="355" text-anchor="middle" font-size="8" fill="#555">fraudrag_request_latency_seconds</text>
  <text x="342" y="368" text-anchor="middle" font-size="8" fill="#555">fraudrag_fraud_detections_total</text>
  <text x="342" y="381" text-anchor="middle" font-size="8" fill="#555">{label: risk_level}</text>

  <rect x="459" y="312" width="205" height="74" rx="5" fill="#F0F0F0" stroke="#999" stroke-width="0.5"/>
  <text x="561" y="328" text-anchor="middle" font-size="8.5" font-weight="bold" fill="#333">Fallback strategy</text>
  <text x="561" y="342" text-anchor="middle" font-size="8" fill="#555">No LLM key → rule-based fallback</text>
  <text x="561" y="355" text-anchor="middle" font-size="8" fill="#555">AUC=0.741, latency &lt;50 ms</text>
  <text x="561" y="368" text-anchor="middle" font-size="8" fill="#555">Balance check + regex only</text>
  <text x="561" y="381" text-anchor="middle" font-size="8" fill="#555">Always-available safety net</text>
</svg>`;

fs.writeFileSync(path.join(outDir, 'fig4_rag_pipeline.svg'), fig4);
console.log('fig4 written');

// ── Figure 5: Performance Comparison Bar Chart ─────────────────────────────
const fig5 = `<svg width="700" height="380" viewBox="0 0 700 380" xmlns="http://www.w3.org/2000/svg" style="background:#fff;font-family:'Times New Roman',serif">
  <text x="350" y="22" text-anchor="middle" font-size="11" font-weight="bold" fill="#111">Fig. 5. Detection Performance Comparison on GraphGuard-2400 Benchmark</text>

  <!-- Y-axis -->
  <line x1="100" y1="40" x2="100" y2="290" stroke="#333" stroke-width="1"/>
  <!-- Y gridlines + labels -->
  <line x1="100" y1="290" x2="670" y2="290" stroke="#DDD" stroke-width="0.5"/>
  <line x1="100" y1="240" x2="670" y2="240" stroke="#DDD" stroke-width="0.5"/>
  <line x1="100" y1="190" x2="670" y2="190" stroke="#DDD" stroke-width="0.5"/>
  <line x1="100" y1="140" x2="670" y2="140" stroke="#DDD" stroke-width="0.5"/>
  <line x1="100" y1="90" x2="670" y2="90" stroke="#DDD" stroke-width="0.5"/>
  <line x1="100" y1="40" x2="670" y2="40" stroke="#DDD" stroke-width="0.5"/>

  <text x="90" y="293" text-anchor="end" font-size="9" fill="#555">0.60</text>
  <text x="90" y="243" text-anchor="end" font-size="9" fill="#555">0.70</text>
  <text x="90" y="193" text-anchor="end" font-size="9" fill="#555">0.80</text>
  <text x="90" y="143" text-anchor="end" font-size="9" fill="#555">0.90</text>
  <text x="90" y="93" text-anchor="end" font-size="9" fill="#555">0.95</text>
  <text x="90" y="43" text-anchor="end" font-size="9" fill="#555">1.00</text>

  <!-- Y-axis label -->
  <text x="20" y="165" text-anchor="middle" font-size="10" fill="#333" transform="rotate(-90,20,165)">Score</text>

  <!-- X-axis line -->
  <line x1="100" y1="290" x2="670" y2="290" stroke="#333" stroke-width="1"/>

  <!-- Scale: 0.60=290, 1.00=40 → 250px for 0.40 range → 1pt = 625px -->
  <!-- Bar group width=100, gap=14. 5 groups. Start at x=106 -->
  <!-- Groups: Rule-Based, LLM-Only, RAG-Only, Graph-Only, FraudRAG -->
  <!-- Each group: 3 bars (AUC, Precision, Recall), width=22, gap=6 -->

  <!-- Helper: value v, bar bottom=290, scale: y = 290 - (v-0.60)*625 -->
  <!-- Rule-Based: AUC=0.741, Prec=0.683, Rec=0.712 -->
  <rect x="112" y="${290-(0.741-0.60)*625}" width="22" height="${(0.741-0.60)*625}" fill="#888"/>
  <rect x="136" y="${290-(0.683-0.60)*625}" width="22" height="${(0.683-0.60)*625}" fill="#AAA"/>
  <rect x="160" y="${290-(0.712-0.60)*625}" width="22" height="${(0.712-0.60)*625}" fill="#CCC"/>
  <text x="148" y="305" text-anchor="middle" font-size="8.5" fill="#333">Rule-Based</text>

  <!-- LLM-Only: AUC=0.819, Prec=0.771, Rec=0.748 -->
  <rect x="222" y="${290-(0.819-0.60)*625}" width="22" height="${(0.819-0.60)*625}" fill="#3A7FC0"/>
  <rect x="246" y="${290-(0.771-0.60)*625}" width="22" height="${(0.771-0.60)*625}" fill="#6AAADA"/>
  <rect x="270" y="${290-(0.748-0.60)*625}" width="22" height="${(0.748-0.60)*625}" fill="#9DCAEC"/>
  <text x="258" y="305" text-anchor="middle" font-size="8.5" fill="#333">LLM-Only</text>

  <!-- RAG-Only: AUC=0.877, Prec=0.831, Rec=0.804 -->
  <rect x="332" y="${290-(0.877-0.60)*625}" width="22" height="${(0.877-0.60)*625}" fill="#2E7D50"/>
  <rect x="356" y="${290-(0.831-0.60)*625}" width="22" height="${(0.831-0.60)*625}" fill="#5AAA78"/>
  <rect x="380" y="${290-(0.804-0.60)*625}" width="22" height="${(0.804-0.60)*625}" fill="#8DC8A4"/>
  <text x="368" y="305" text-anchor="middle" font-size="8.5" fill="#333">RAG-Only</text>

  <!-- Graph-Only: AUC=0.893, Prec=0.847, Rec=0.831 -->
  <rect x="442" y="${290-(0.893-0.60)*625}" width="22" height="${(0.893-0.60)*625}" fill="#7A4A90"/>
  <rect x="466" y="${290-(0.847-0.60)*625}" width="22" height="${(0.847-0.60)*625}" fill="#A070B8"/>
  <rect x="490" y="${290-(0.831-0.60)*625}" width="22" height="${(0.831-0.60)*625}" fill="#C098D8"/>
  <text x="478" y="305" text-anchor="middle" font-size="8.5" fill="#333">Graph-Only</text>

  <!-- FraudRAG: AUC=0.943, Prec=0.891, Rec=0.876 - highlighted -->
  <rect x="552" y="${290-(0.943-0.60)*625}" width="22" height="${(0.943-0.60)*625}" fill="#C03030" stroke="#900" stroke-width="0.5"/>
  <rect x="576" y="${290-(0.891-0.60)*625}" width="22" height="${(0.891-0.60)*625}" fill="#D86020" stroke="#A04000" stroke-width="0.5"/>
  <rect x="600" y="${290-(0.876-0.60)*625}" width="22" height="${(0.876-0.60)*625}" fill="#D89020" stroke="#A06000" stroke-width="0.5"/>
  <text x="588" y="305" text-anchor="middle" font-size="8.5" font-weight="bold" fill="#C03030">FraudRAG</text>
  <!-- FraudRAG value labels -->
  <text x="563" y="${290-(0.943-0.60)*625-4}" text-anchor="middle" font-size="7.5" font-weight="bold" fill="#900">0.943</text>
  <text x="587" y="${290-(0.891-0.60)*625-4}" text-anchor="middle" font-size="7.5" font-weight="bold" fill="#A04000">0.891</text>
  <text x="611" y="${290-(0.876-0.60)*625-4}" text-anchor="middle" font-size="7.5" font-weight="bold" fill="#A06000">0.876</text>

  <!-- Legend -->
  <rect x="100" y="320" width="570" height="46" rx="5" fill="#FAFAFA" stroke="#CCC" stroke-width="0.5"/>
  <rect x="115" y="333" width="12" height="12" fill="#555"/>
  <text x="132" y="343" font-size="8.5" fill="#333">AUC</text>
  <rect x="178" y="333" width="12" height="12" fill="#888"/>
  <text x="195" y="343" font-size="8.5" fill="#333">Precision</text>
  <rect x="258" y="333" width="12" height="12" fill="#AAA"/>
  <text x="275" y="343" font-size="8.5" fill="#333">Recall</text>
  <rect x="115" y="352" width="12" height="12" fill="#C03030" stroke="#900" stroke-width="0.5"/>
  <text x="132" y="362" font-size="8.5" fill="#C03030" font-weight="bold">FraudRAG (proposed)</text>
  <text x="360" y="353" font-size="8.5" fill="#555">Dashed line at 0.90 threshold (target performance bar)</text>
  <line x1="100" y1="${290-(0.90-0.60)*625}" x2="670" y2="${290-(0.90-0.60)*625}" stroke="#C03030" stroke-width="0.6" stroke-dasharray="4,3"/>
  <text x="672" y="${290-(0.90-0.60)*625+3}" font-size="8" fill="#C03030">0.90</text>
</svg>`;

fs.writeFileSync(path.join(outDir, 'fig5_performance_comparison.svg'), fig5);
console.log('fig5 written');

// ── Figure 6: DDD Bounded Contexts ────────────────────────────────────────
const fig6 = `<svg width="700" height="400" viewBox="0 0 700 400" xmlns="http://www.w3.org/2000/svg" style="background:#fff;font-family:'Times New Roman',serif">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L8 5L1 8" fill="none" stroke="#555" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
  <text x="350" y="22" text-anchor="middle" font-size="11" font-weight="bold" fill="#111">Fig. 6. Domain-Driven Design Bounded Contexts</text>

  <!-- Statement Context -->
  <rect x="20" y="50" width="310" height="145" rx="10" fill="#FEF3E4" stroke="#D4800A" stroke-width="1.5" stroke-dasharray="6,3"/>
  <text x="175" y="70" text-anchor="middle" font-size="10" font-weight="bold" fill="#7A4500">StatementContext</text>
  <rect x="35" y="78" width="130" height="48" rx="5" fill="#fff" stroke="#D4800A" stroke-width="0.8"/>
  <text x="100" y="96" text-anchor="middle" font-size="9" font-weight="bold" fill="#7A4500">RawStatement</text>
  <text x="100" y="109" text-anchor="middle" font-size="8" fill="#A05000">Aggregate Root</text>
  <text x="100" y="120" text-anchor="middle" font-size="7.5" fill="#C07030">id · hash · raw_text · ocr_conf</text>
  <rect x="180" y="78" width="135" height="48" rx="5" fill="#fff" stroke="#D4800A" stroke-width="0.8"/>
  <text x="247" y="96" text-anchor="middle" font-size="9" font-weight="bold" fill="#7A4500">NormalizedStatement</text>
  <text x="247" y="109" text-anchor="middle" font-size="8" fill="#A05000">Entity</text>
  <text x="247" y="120" text-anchor="middle" font-size="7.5" fill="#C07030">entities · transactions · quality</text>
  <!-- Domain services -->
  <rect x="35" y="134" width="280" height="48" rx="5" fill="#FAEBD4" stroke="#D4800A" stroke-width="0.5"/>
  <text x="175" y="150" text-anchor="middle" font-size="9" font-weight="bold" fill="#6B4000">Services</text>
  <text x="175" y="163" text-anchor="middle" font-size="8" fill="#A05000">BronzePipeline · SilverPipeline · GoldPipeline</text>
  <text x="175" y="175" text-anchor="middle" font-size="7.5" fill="#C07030">OCRService · DocumentHasher · BalanceValidator</text>

  <!-- Fraud Context -->
  <rect x="370" y="50" width="310" height="145" rx="10" fill="#FEF0F0" stroke="#C0392B" stroke-width="1.5" stroke-dasharray="6,3"/>
  <text x="525" y="70" text-anchor="middle" font-size="10" font-weight="bold" fill="#7B1A11">FraudContext</text>
  <rect x="385" y="78" width="130" height="48" rx="5" fill="#fff" stroke="#C0392B" stroke-width="0.8"/>
  <text x="450" y="96" text-anchor="middle" font-size="9" font-weight="bold" fill="#7B1A11">FraudAnalysis</text>
  <text x="450" y="109" text-anchor="middle" font-size="8" fill="#A52819">Aggregate Root</text>
  <text x="450" y="120" text-anchor="middle" font-size="7.5" fill="#C03030">score · indicators · reasoning</text>
  <rect x="525" y="78" width="140" height="48" rx="5" fill="#fff" stroke="#C0392B" stroke-width="0.8"/>
  <text x="595" y="96" text-anchor="middle" font-size="9" font-weight="bold" fill="#7B1A11">FraudScore</text>
  <text x="595" y="109" text-anchor="middle" font-size="8" fill="#A52819">Value Object</text>
  <text x="595" y="120" text-anchor="middle" font-size="7.5" fill="#C03030">score · confidence · model_ver</text>
  <rect x="385" y="134" width="280" height="48" rx="5" fill="#FCE8E8" stroke="#C0392B" stroke-width="0.5"/>
  <text x="525" y="150" text-anchor="middle" font-size="9" font-weight="bold" fill="#7B1A11">Services</text>
  <text x="525" y="163" text-anchor="middle" font-size="8" fill="#A52819">GraphRAGService · FraudIndicatorClassifier</text>
  <text x="525" y="175" text-anchor="middle" font-size="7.5" fill="#C03030">AnalystReviewService · RiskPropagationService</text>

  <!-- Graph Context -->
  <rect x="20" y="225" width="310" height="145" rx="10" fill="#E6F3F0" stroke="#27927A" stroke-width="1.5" stroke-dasharray="6,3"/>
  <text x="175" y="245" text-anchor="middle" font-size="10" font-weight="bold" fill="#0D5E4E">GraphContext</text>
  <rect x="35" y="253" width="120" height="48" rx="5" fill="#fff" stroke="#27927A" stroke-width="0.8"/>
  <text x="95" y="271" text-anchor="middle" font-size="9" font-weight="bold" fill="#0D5E4E">CustomerNode</text>
  <text x="95" y="284" text-anchor="middle" font-size="8" fill="#1D7A65">Neo4j Entity</text>
  <text x="95" y="295" text-anchor="middle" font-size="7.5" fill="#3A9A80">risk_score · embedding</text>
  <rect x="165" y="253" width="120" height="48" rx="5" fill="#fff" stroke="#27927A" stroke-width="0.8"/>
  <text x="225" y="271" text-anchor="middle" font-size="9" font-weight="bold" fill="#0D5E4E">FraudPatternNode</text>
  <text x="225" y="284" text-anchor="middle" font-size="8" fill="#1D7A65">Neo4j Entity</text>
  <text x="225" y="295" text-anchor="middle" font-size="7.5" fill="#3A9A80">frequency · embedding</text>
  <rect x="35" y="309" width="280" height="48" rx="5" fill="#D4EDE8" stroke="#27927A" stroke-width="0.5"/>
  <text x="175" y="325" text-anchor="middle" font-size="9" font-weight="bold" fill="#0D5E4E">Services</text>
  <text x="175" y="338" text-anchor="middle" font-size="8" fill="#1D7A65">Neo4jClient · SubgraphRetriever</text>
  <text x="175" y="350" text-anchor="middle" font-size="7.5" fill="#3A9A80">FraudRingDetector · RiskPropagator</text>

  <!-- Customer Context -->
  <rect x="370" y="225" width="310" height="145" rx="10" fill="#EFF2FB" stroke="#4A60C0" stroke-width="1.5" stroke-dasharray="6,3"/>
  <text x="525" y="245" text-anchor="middle" font-size="10" font-weight="bold" fill="#1A2E80">CustomerContext</text>
  <rect x="385" y="253" width="130" height="48" rx="5" fill="#fff" stroke="#4A60C0" stroke-width="0.8"/>
  <text x="450" y="271" text-anchor="middle" font-size="9" font-weight="bold" fill="#1A2E80">CustomerProfile</text>
  <text x="450" y="284" text-anchor="middle" font-size="8" fill="#2E45A0">Aggregate Root</text>
  <text x="450" y="295" text-anchor="middle" font-size="7.5" fill="#4A60C0">risk_level · statement_count</text>
  <rect x="525" y="253" width="140" height="48" rx="5" fill="#fff" stroke="#4A60C0" stroke-width="0.8"/>
  <text x="595" y="271" text-anchor="middle" font-size="9" font-weight="bold" fill="#1A2E80">DocumentHash</text>
  <text x="595" y="284" text-anchor="middle" font-size="8" fill="#2E45A0">Value Object</text>
  <text x="595" y="295" text-anchor="middle" font-size="7.5" fill="#4A60C0">SHA-256 hex · immutable</text>
  <rect x="385" y="309" width="280" height="48" rx="5" fill="#DDE3F6" stroke="#4A60C0" stroke-width="0.5"/>
  <text x="525" y="325" text-anchor="middle" font-size="9" font-weight="bold" fill="#1A2E80">Services</text>
  <text x="525" y="338" text-anchor="middle" font-size="8" fill="#2E45A0">CustomerRepository · IdentityService</text>
  <text x="525" y="350" text-anchor="middle" font-size="7.5" fill="#4A60C0">RiskProfileUpdater · AliasResolver</text>

  <!-- Cross-context arrows -->
  <line x1="330" y1="122" x2="368" y2="122" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>
  <text x="349" y="117" text-anchor="middle" font-size="7.5" fill="#555">triggers</text>
  <line x1="175" y1="195" x2="175" y2="223" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>
  <text x="205" y="212" text-anchor="middle" font-size="7.5" fill="#555">enriches</text>
  <line x1="525" y1="195" x2="525" y2="223" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>
  <text x="555" y="212" text-anchor="middle" font-size="7.5" fill="#555">scores</text>
  <line x1="330" y1="310" x2="368" y2="310" stroke="#555" stroke-width="1" marker-end="url(#arr)"/>
  <text x="349" y="305" text-anchor="middle" font-size="7.5" fill="#555">links to</text>
</svg>`;

fs.writeFileSync(path.join(outDir, 'fig6_ddd_bounded_contexts.svg'), fig6);
console.log('fig6 written');

console.log('\nAll 6 figures written to:', outDir);
