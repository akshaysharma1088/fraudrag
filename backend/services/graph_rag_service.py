"""
Graph RAG Service – FraudRAG
Combines Neo4j knowledge graph traversal with vector similarity search
to build enriched context for LLM-based fraud analysis.

Pipeline:
  1. Extract embeddings from uploaded statement
  2. Query ChromaDB for similar historical statements
  3. Traverse Neo4j for customer risk context
  4. Inject combined context into LangChain RAG chain
  5. Return structured fraud analysis with reasoning
"""

from __future__ import annotations

import json
import structlog
from typing import Any, Dict, List, Optional

from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain.schema import Document as LCDocument
from langchain.output_parsers import PydanticOutputParser

from backend.core.config import get_settings
from backend.graph.neo4j_client import Neo4jClient
from backend.models.domain import FraudAnalysis, FraudIndicator, FraudScore, RiskLevel

settings = get_settings()
logger = structlog.get_logger(__name__)

# ─── Prompt Templates ────────────────────────────────────────────

SYSTEM_PROMPT = """You are FraudRAG, an expert financial forensics AI specializing in 
detecting fraudulent or forged financial statements. You have access to:

1. **Knowledge Graph Context**: Customer history, linked entities, known fraud patterns
2. **Vector Similarity Context**: Semantically similar historical statements  
3. **The Uploaded Statement**: The document under investigation
4. **Warehouse Reference**: The authoritative copy from the data warehouse

Your task is to produce a detailed, structured fraud analysis. Be precise, cite specific 
evidence, and explain your reasoning like a forensic accountant.

FRAUD INDICATORS TO CHECK:
- Balance arithmetic: opening_balance + total_credits - total_debits = closing_balance
- Date consistency: transactions within stated period, no future dates
- Institution formatting: fonts, logos, account number formats match institution standards
- Amount patterns: suspicious rounding, digit substitution, scale manipulation
- Entity consistency: customer name/account match across documents
- Graph anomalies: customer has fraud history, linked to known fraud rings
- Semantic deviation: statement language deviates from this institution's known templates

Respond ONLY with valid JSON matching the schema provided."""

ANALYSIS_PROMPT = """
## GRAPH CONTEXT (Customer Knowledge Graph)
{graph_context}

## VECTOR SIMILARITY CONTEXT (Similar Historical Statements)
{vector_context}

## UPLOADED STATEMENT TEXT
{statement_text}

## WAREHOUSE REFERENCE (Authoritative Copy)
{warehouse_reference}

## CUSTOMER PROFILE
{customer_profile}

---

Analyze for fraud. Return a JSON object with this exact structure:
{{
  "fraud_score": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "risk_level": <"minimal"|"low"|"medium"|"high"|"critical">,
  "warehouse_match_score": <float 0.0-1.0 or null>,
  "indicators": [
    {{
      "indicator_type": <string>,
      "description": <string>,
      "severity": <"minimal"|"low"|"medium"|"high"|"critical">,
      "confidence": <float>,
      "evidence": {{<key>: <value>}}
    }}
  ],
  "discrepancies": [
    {{
      "field": <string>,
      "uploaded_value": <string>,
      "expected_value": <string>,
      "significance": <"low"|"medium"|"high">
    }}
  ],
  "reasoning": <detailed explanation string>
}}
"""


class GraphRAGService:
    """
    Core service orchestrating Graph-RAG fraud detection.
    Implements the retrieval-augmented generation pipeline with
    knowledge graph enrichment.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j = neo4j_client
        self._vectorstore: Optional[Chroma] = None
        self._embeddings = None
        self._llm = None

    async def initialize(self):
        """Initialize LLM, embeddings, and vector store."""
        # Embeddings
        if settings.OPENAI_API_KEY:
            self._embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
            )
        else:
            # Fallback to local sentence transformers
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self._embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            logger.info("Using local HuggingFace embeddings (no OpenAI key)")

        # Vector Store
        self._vectorstore = Chroma(
            collection_name=settings.CHROMA_COLLECTION,
            embedding_function=self._embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIR,
        )

        # LLM
        if settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
            self._llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            logger.info("LLM initialized", provider="anthropic", model="claude-3-5-sonnet")
        elif settings.OPENAI_API_KEY:
            self._llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            logger.info("LLM initialized", provider="openai", model=settings.LLM_MODEL)
        else:
            logger.warning("No LLM API key configured – analysis will use rule-based fallback")

        logger.info("GraphRAGService initialized")

    async def analyze_statement(
        self,
        statement_id: str,
        customer_id: str,
        statement_text: str,
        warehouse_reference: Optional[str] = None,
        customer_profile: Optional[Dict[str, Any]] = None,
    ) -> FraudAnalysis:
        """
        Main entry point: run full Graph-RAG fraud analysis pipeline.

        Steps:
          1. Retrieve graph context from Neo4j
          2. Retrieve similar statements from ChromaDB
          3. Build augmented prompt
          4. Call LLM for analysis
          5. Parse structured output → FraudAnalysis
        """
        logger.info("Starting Graph-RAG analysis", statement_id=statement_id)

        # Step 1: Graph context
        graph_context = await self.neo4j.get_graph_context_for_rag(customer_id)

        # Step 2: Vector similarity retrieval
        vector_context, retrieved_ids = await self._retrieve_similar_statements(statement_text)

        # Step 3: LLM analysis
        if self._llm:
            raw_result = await self._run_llm_analysis(
                statement_text=statement_text,
                graph_context=graph_context,
                vector_context=vector_context,
                warehouse_reference=warehouse_reference or "Not available",
                customer_profile=json.dumps(customer_profile or {}, indent=2),
            )
        else:
            raw_result = self._rule_based_fallback(statement_text, warehouse_reference)

        # Step 4: Build FraudAnalysis aggregate
        analysis = self._build_analysis(
            statement_id=statement_id,
            customer_id=customer_id,
            raw_result=raw_result,
            retrieved_ids=retrieved_ids,
        )

        # Step 5: Persist pattern to graph if high risk
        if analysis.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            await self._persist_fraud_pattern_to_graph(analysis, customer_id)

        # Step 6: Index statement for future retrieval
        await self._index_statement(statement_id, statement_text, analysis)

        logger.info(
            "Analysis complete",
            statement_id=statement_id,
            risk_level=analysis.risk_level,
            score=analysis.fraud_score.score,
        )
        return analysis

    async def _retrieve_similar_statements(
        self, statement_text: str, k: int = 4
    ) -> tuple[str, List[str]]:
        """Query ChromaDB for semantically similar statements."""
        if not self._vectorstore:
            return "Vector store not initialized.", []
        try:
            docs: List[LCDocument] = self._vectorstore.similarity_search(
                statement_text[:2000], k=k  # Truncate for embedding
            )
            ids = [d.metadata.get("statement_id", "unknown") for d in docs]
            context_parts = []
            for i, doc in enumerate(docs, 1):
                meta = doc.metadata
                context_parts.append(
                    f"[Similar Statement {i}]\n"
                    f"Institution: {meta.get('institution', 'Unknown')}\n"
                    f"Period: {meta.get('period', 'Unknown')}\n"
                    f"Was Fraudulent: {meta.get('was_fraudulent', False)}\n"
                    f"Excerpt: {doc.page_content[:500]}\n"
                )
            return "\n".join(context_parts) or "No similar statements found.", ids
        except Exception as e:
            logger.error("Vector retrieval failed", error=str(e))
            return "Vector retrieval unavailable.", []

    async def _run_llm_analysis(self, **kwargs) -> Dict[str, Any]:
        """Build prompt and call LLM."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template(ANALYSIS_PROMPT),
        ])
        chain = LLMChain(llm=self._llm, prompt=prompt)
        try:
            response = await chain.arun(**kwargs)
            # Strip markdown code fences if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error("LLM returned invalid JSON", error=str(e))
            return self._default_analysis_result()
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            return self._default_analysis_result()

    def _rule_based_fallback(
        self, statement_text: str, warehouse_reference: Optional[str]
    ) -> Dict[str, Any]:
        """
        Rule-based fraud detection when LLM is unavailable.
        Checks basic accounting arithmetic and text similarity.
        """
        indicators = []
        score = 0.0

        # Rule 1: Balance arithmetic check (requires parsed data)
        if "TOTAL" in statement_text.upper() and "BALANCE" in statement_text.upper():
            indicators.append({
                "indicator_type": "balance_inconsistency",
                "description": "Balance verification required – manual review recommended",
                "severity": "low",
                "confidence": 0.3,
                "evidence": {}
            })
            score += 0.05

        # Rule 2: Warehouse comparison
        if warehouse_reference and warehouse_reference != "Not available":
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, statement_text[:1000], warehouse_reference[:1000]).ratio()
            if similarity < 0.85:
                score += 0.4
                indicators.append({
                    "indicator_type": "semantic_deviation",
                    "description": f"Statement text similarity to warehouse: {similarity:.1%}",
                    "severity": "medium" if similarity > 0.7 else "high",
                    "confidence": 0.7,
                    "evidence": {"similarity_score": similarity}
                })

        return {
            "fraud_score": min(score, 1.0),
            "confidence": 0.5,
            "risk_level": "medium" if score > 0.4 else ("low" if score > 0.1 else "minimal"),
            "warehouse_match_score": None,
            "indicators": indicators,
            "discrepancies": [],
            "reasoning": "Rule-based analysis (LLM unavailable). Manual review recommended.",
        }

    def _build_analysis(
        self,
        statement_id: str,
        customer_id: str,
        raw_result: Dict[str, Any],
        retrieved_ids: List[str],
    ) -> FraudAnalysis:
        """Map LLM JSON output → FraudAnalysis domain object."""
        indicators = [
            FraudIndicator(
                indicator_type=ind.get("indicator_type", "semantic_deviation"),
                description=ind.get("description", ""),
                severity=RiskLevel(ind.get("severity", "low")),
                confidence=float(ind.get("confidence", 0.5)),
                evidence=ind.get("evidence", {}),
            )
            for ind in raw_result.get("indicators", [])
        ]

        fraud_score = FraudScore(
            score=float(raw_result.get("fraud_score", 0.1)),
            confidence=float(raw_result.get("confidence", 0.5)),
            model_version=f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}",
        )

        return FraudAnalysis(
            statement_id=statement_id,
            customer_id=customer_id,
            fraud_score=fraud_score,
            risk_level=fraud_score.risk_level,
            indicators=indicators,
            rag_context_used=retrieved_ids,
            warehouse_match_score=raw_result.get("warehouse_match_score"),
            discrepancies=raw_result.get("discrepancies", []),
            llm_reasoning=raw_result.get("reasoning", ""),
            llm_model_used=f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}",
        )

    async def _persist_fraud_pattern_to_graph(self, analysis: FraudAnalysis, customer_id: str):
        """Store high-risk fraud patterns back into the knowledge graph."""
        for indicator in analysis.indicators:
            if indicator.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                pattern = {
                    "id": f"pattern-{analysis.statement_id[:8]}-{indicator.indicator_type}",
                    "pattern_name": indicator.description[:100],
                    "pattern_type": str(indicator.indicator_type),
                    "description": indicator.description,
                    "statement_id": analysis.statement_id,
                }
                await self.neo4j.store_fraud_pattern(pattern)
        await self.neo4j.update_customer_risk(customer_id, analysis.fraud_score.score)

    async def _index_statement(
        self, statement_id: str, statement_text: str, analysis: FraudAnalysis
    ):
        """Add statement to ChromaDB for future retrieval."""
        if not self._vectorstore:
            return
        try:
            self._vectorstore.add_texts(
                texts=[statement_text[:3000]],
                metadatas=[{
                    "statement_id": statement_id,
                    "customer_id": analysis.customer_id,
                    "fraud_score": analysis.fraud_score.score,
                    "was_fraudulent": analysis.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL),
                    "risk_level": str(analysis.risk_level),
                }],
                ids=[statement_id],
            )
        except Exception as e:
            logger.warning("Failed to index statement", error=str(e))

    def _default_analysis_result(self) -> Dict[str, Any]:
        return {
            "fraud_score": 0.0,
            "confidence": 0.0,
            "risk_level": "minimal",
            "warehouse_match_score": None,
            "indicators": [],
            "discrepancies": [],
            "reasoning": "Analysis failed – manual review required",
        }
