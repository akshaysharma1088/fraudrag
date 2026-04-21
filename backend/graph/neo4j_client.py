"""
Neo4j Knowledge Graph Client
Manages all graph operations for FraudRAG's fraud detection knowledge base.

Graph Schema:
  Nodes:   (:Customer), (:Institution), (:Statement), (:FraudPattern), (:Transaction)
  Edges:   [:HAS_ACCOUNT], [:FILED_WITH], [:CONTAINS], [:SIMILAR_TO],
           [:MATCHES_PATTERN], [:LINKED_TO], [:DETECTED_IN]
"""

from __future__ import annotations

import structlog
from neo4j import AsyncGraphDatabase, AsyncDriver
from typing import Any, Dict, List, Optional

logger = structlog.get_logger(__name__)

SCHEMA_QUERIES = [
    # Constraints (also create indexes)
    "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT statement_id IF NOT EXISTS FOR (s:Statement) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT pattern_id IF NOT EXISTS FOR (p:FraudPattern) REQUIRE p.id IS UNIQUE",
    # Indexes for performance
    "CREATE INDEX customer_risk IF NOT EXISTS FOR (c:Customer) ON (c.risk_score)",
    "CREATE INDEX statement_date IF NOT EXISTS FOR (s:Statement) ON (s.upload_timestamp)",
    "CREATE FULLTEXT INDEX customer_name IF NOT EXISTS FOR (c:Customer) ON EACH [c.name]",
    "CREATE FULLTEXT INDEX pattern_name IF NOT EXISTS FOR (p:FraudPattern) ON EACH [p.pattern_name, p.description]",
]


class Neo4jClient:
    """Async Neo4j driver wrapper with FraudRAG-specific query methods."""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver: Optional[AsyncDriver] = None

    async def initialize_schema(self):
        """Create schema constraints and indexes on first run."""
        async with self._driver.session(database=self.database) as session:
            for query in SCHEMA_QUERIES:
                try:
                    await session.run(query)
                except Exception as e:
                    logger.warning("Schema query skipped", query=query[:60], error=str(e))
        logger.info("Neo4j schema initialized")

    async def close(self):
        if self._driver:
            await self._driver.close()

    def _get_driver(self) -> AsyncDriver:
        if not self._driver:
            self._driver = AsyncGraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        return self._driver

    @property
    def driver(self) -> AsyncDriver:
        return self._get_driver()

    # ─── Customer Operations ───────────────────────────────────────

    async def upsert_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a Customer node."""
        query = """
        MERGE (c:Customer {id: $id})
        ON CREATE SET
            c.name = $name,
            c.risk_score = $risk_score,
            c.fraud_history_count = $fraud_history_count,
            c.created_at = datetime(),
            c.updated_at = datetime()
        ON MATCH SET
            c.name = $name,
            c.risk_score = $risk_score,
            c.fraud_history_count = $fraud_history_count,
            c.updated_at = datetime()
        RETURN c
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, **customer_data)
            record = await result.single()
            return dict(record["c"]) if record else {}

    async def get_customer_subgraph(self, customer_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Retrieve k-hop neighborhood of a customer node.
        Used to build RAG context for fraud analysis.
        """
        query = """
        MATCH (c:Customer {id: $customer_id})
        CALL apoc.path.subgraphAll(c, {maxLevel: $depth, relationshipFilter: '>'})
        YIELD nodes, relationships
        RETURN
            [n IN nodes | {id: n.id, labels: labels(n), properties: properties(n)}] AS nodes,
            [r IN relationships | {
                type: type(r),
                source: startNode(r).id,
                target: endNode(r).id,
                properties: properties(r)
            }] AS relationships
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, customer_id=customer_id, depth=depth)
            record = await result.single()
            if record:
                return {"nodes": record["nodes"], "relationships": record["relationships"]}
            return {"nodes": [], "relationships": []}

    async def get_customer_subgraph_simple(self, customer_id: str, depth: int = 2) -> Dict[str, Any]:
        """Fallback subgraph query without APOC."""
        query = """
        MATCH path = (c:Customer {id: $customer_id})-[*1..$depth]-(related)
        WITH collect(DISTINCT {
            id: related.id,
            labels: labels(related),
            properties: properties(related)
        }) AS nodes,
        collect(DISTINCT {
            type: type(relationships(path)[0]),
            source: startNode(relationships(path)[0]).id,
            target: endNode(relationships(path)[0]).id
        }) AS relationships
        RETURN nodes, relationships
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, customer_id=customer_id, depth=depth)
            record = await result.single()
            if record:
                return {"nodes": record["nodes"], "relationships": record["relationships"]}
            return {"nodes": [], "relationships": []}

    # ─── Statement Operations ──────────────────────────────────────

    async def link_statement_to_customer(
        self, statement_id: str, customer_id: str, statement_meta: Dict[str, Any]
    ):
        """Create Statement node and link to Customer."""
        query = """
        MERGE (s:Statement {id: $statement_id})
        SET s += $meta,
            s.updated_at = datetime()
        WITH s
        MATCH (c:Customer {id: $customer_id})
        MERGE (c)-[:FILED]->(s)
        RETURN s.id
        """
        async with self.driver.session(database=self.database) as session:
            await session.run(
                query,
                statement_id=statement_id,
                customer_id=customer_id,
                meta=statement_meta,
            )

    async def link_statement_to_institution(self, statement_id: str, institution_id: str):
        query = """
        MATCH (s:Statement {id: $statement_id})
        MERGE (i:Institution {id: $institution_id})
        MERGE (s)-[:ISSUED_BY]->(i)
        """
        async with self.driver.session(database=self.database) as session:
            await session.run(query, statement_id=statement_id, institution_id=institution_id)

    # ─── Fraud Pattern Operations ──────────────────────────────────

    async def store_fraud_pattern(self, pattern: Dict[str, Any]):
        """Store a detected fraud pattern for future reference."""
        query = """
        MERGE (p:FraudPattern {id: $id})
        SET p += $props,
            p.frequency = COALESCE(p.frequency, 0) + 1,
            p.last_seen = datetime()
        RETURN p
        """
        async with self.driver.session(database=self.database) as session:
            await session.run(query, id=pattern["id"], props=pattern)

    async def find_similar_fraud_patterns(
        self, embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Vector similarity search over fraud patterns using Neo4j vector index."""
        query = """
        CALL db.index.vector.queryNodes('fraud_pattern_embeddings', $top_k, $embedding)
        YIELD node, score
        RETURN node.id AS id,
               node.pattern_name AS pattern_name,
               node.description AS description,
               node.pattern_type AS pattern_type,
               score
        ORDER BY score DESC
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, top_k=top_k, embedding=embedding)
            return [dict(r) async for r in result]

    # ─── Risk Propagation ─────────────────────────────────────────

    async def update_customer_risk(self, customer_id: str, new_fraud_score: float):
        """Update risk score and propagate influence to linked entities."""
        query = """
        MATCH (c:Customer {id: $customer_id})
        SET c.risk_score = $score,
            c.fraud_history_count = c.fraud_history_count + 1,
            c.updated_at = datetime()
        WITH c
        MATCH (c)-[:LINKED_TO|SHARED_ACCOUNT]-(related:Customer)
        SET related.risk_score = related.risk_score * 0.9 + $score * 0.1
        RETURN c.id, count(related) AS influenced_nodes
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, customer_id=customer_id, score=new_fraud_score)
            record = await result.single()
            return dict(record) if record else {}

    async def find_fraud_ring(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Detect potential fraud rings: shared accounts, addresses, devices.
        Uses graph traversal to find suspicious clusters.
        """
        query = """
        MATCH (c:Customer {id: $customer_id})
        MATCH (c)-[:SHARED_ACCOUNT|SAME_DEVICE|SAME_ADDRESS*1..3]-(suspect:Customer)
        WHERE suspect.id <> $customer_id
          AND suspect.risk_score > 0.5
        RETURN suspect.id AS id,
               suspect.name AS name,
               suspect.risk_score AS risk_score,
               length(shortestPath((c)-[*]-(suspect))) AS degrees_of_separation
        ORDER BY risk_score DESC
        LIMIT 20
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, customer_id=customer_id)
            return [dict(r) async for r in result]

    async def get_graph_context_for_rag(self, customer_id: str) -> str:
        """
        Build a natural-language summary of the customer's graph neighborhood
        for injection into the LLM RAG prompt.
        """
        query = """
        MATCH (c:Customer {id: $customer_id})
        OPTIONAL MATCH (c)-[:FILED]->(s:Statement)
        OPTIONAL MATCH (s)-[:ISSUED_BY]->(i:Institution)
        OPTIONAL MATCH (c)-[:MATCHES_PATTERN]->(p:FraudPattern)
        RETURN
            c.name AS customer_name,
            c.risk_score AS risk_score,
            c.fraud_history_count AS fraud_count,
            collect(DISTINCT {
                period: s.statement_period,
                institution: i.name,
                fraud_flagged: s.fraud_flagged
            }) AS statements,
            collect(DISTINCT {
                type: p.pattern_type,
                name: p.pattern_name,
                frequency: p.frequency
            }) AS patterns
        """
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, customer_id=customer_id)
            record = await result.single()
            if not record:
                return f"No graph context found for customer {customer_id}."

            lines = [
                f"Customer: {record['customer_name']}",
                f"Risk Score: {record['risk_score']:.2f}",
                f"Prior Fraud Detections: {record['fraud_count']}",
            ]
            stmts = [s for s in record["statements"] if s["institution"]]
            if stmts:
                lines.append(f"Statements filed with: {', '.join(set(s['institution'] for s in stmts))}")
                flagged = [s for s in stmts if s.get("fraud_flagged")]
                if flagged:
                    lines.append(f"Previously flagged statements: {len(flagged)}")

            patterns = [p for p in record["patterns"] if p["name"]]
            if patterns:
                lines.append(f"Known fraud patterns: {', '.join(p['name'] for p in patterns)}")

            return "\n".join(lines)

    async def seed_demo_data(self):
        """Seed the graph with sample customers and fraud patterns for development."""
        demo_queries = [
            """
            MERGE (c1:Customer {id: 'demo-001'})
            SET c1.name = 'Alice Johnson', c1.risk_score = 0.1,
                c1.fraud_history_count = 0, c1.created_at = datetime()
            """,
            """
            MERGE (c2:Customer {id: 'demo-002'})
            SET c2.name = 'Bob Williams', c2.risk_score = 0.72,
                c2.fraud_history_count = 2, c2.created_at = datetime()
            """,
            """
            MERGE (i1:Institution {id: 'inst-001'})
            SET i1.name = 'First National Bank', i1.country = 'US',
                i1.institution_type = 'bank'
            """,
            """
            MERGE (p1:FraudPattern {id: 'pattern-001'})
            SET p1.pattern_name = 'Balance Rounding Anomaly',
                p1.pattern_type = 'balance_inconsistency',
                p1.description = 'Closing balance inconsistent with arithmetic sum of transactions',
                p1.frequency = 47
            """,
            """
            MERGE (p2:FraudPattern {id: 'pattern-002'})
            SET p2.pattern_name = 'Digit Substitution',
                p2.pattern_type = 'amount_manipulation',
                p2.description = 'Single digit changed in transaction amount, e.g. 1200 -> 12000',
                p2.frequency = 31
            """,
            """
            MATCH (c2:Customer {id: 'demo-002'}), (p2:FraudPattern {id: 'pattern-002'})
            MERGE (c2)-[:MATCHES_PATTERN {detected_at: datetime()}]->(p2)
            """,
        ]
        async with self.driver.session(database=self.database) as session:
            for q in demo_queries:
                await session.run(q)
        logger.info("Demo graph data seeded")
