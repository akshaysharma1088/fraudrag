"""
Medallion Architecture Pipeline – FraudRAG
Bronze → Silver → Gold data processing layers

Bronze:  Raw document ingestion, OCR, hashing, S3 storage
Silver:  Entity extraction, normalization, validation, balance checks
Gold:    ML feature engineering, embeddings, fraud scoring
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


# ─── Bronze Layer Pipeline ────────────────────────────────────────

class BronzePipeline:
    """
    Stage 1 – Raw Ingestion.
    Responsibilities:
    - Accept uploaded document (PDF, image, DOCX)
    - Compute SHA-256 fingerprint
    - Extract raw text via OCR or direct parsing
    - Store to bronze S3 bucket / local path with full provenance
    """

    def __init__(self, storage_path: str = "./data/bronze"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def ingest(
        self,
        file_bytes: bytes,
        filename: str,
        customer_id: str,
        statement_type: str,
        mime_type: str,
    ) -> Dict[str, Any]:
        """
        Ingest raw document and produce Bronze layer record.
        Returns provenance metadata for downstream Silver processing.
        """
        doc_id = str(uuid.uuid4())
        doc_hash = hashlib.sha256(file_bytes).hexdigest()

        logger.info("Bronze ingestion started", doc_id=doc_id, filename=filename, size=len(file_bytes))

        # Extract text based on mime type
        raw_text, ocr_confidence = await self._extract_text(file_bytes, mime_type, filename)

        # Persist raw bytes + metadata
        bronze_record = {
            "id": doc_id,
            "customer_id": customer_id,
            "document_hash": doc_hash,
            "filename": filename,
            "file_size_bytes": len(file_bytes),
            "mime_type": mime_type,
            "statement_type": statement_type,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "raw_text": raw_text,
            "ocr_confidence": ocr_confidence,
            "layer": "bronze",
            "status": "bronze_complete",
        }

        # Write to bronze storage
        bronze_path = self.storage_path / f"{doc_id}.json"
        bronze_path.write_text(json.dumps(bronze_record, indent=2))

        logger.info("Bronze ingestion complete", doc_id=doc_id, text_length=len(raw_text or ""))
        return bronze_record

    async def _extract_text(
        self, file_bytes: bytes, mime_type: str, filename: str
    ) -> Tuple[str, float]:
        """Extract text from document. Returns (text, confidence)."""

        if mime_type == "application/pdf" or filename.endswith(".pdf"):
            return await self._extract_pdf(file_bytes)
        elif mime_type in ("image/png", "image/jpeg", "image/jpg", "image/tiff"):
            return await self._extract_image_ocr(file_bytes)
        elif mime_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ) or filename.endswith(".docx"):
            return await self._extract_docx(file_bytes)
        else:
            # Try as plain text
            try:
                return file_bytes.decode("utf-8", errors="replace"), 1.0
            except Exception:
                return "", 0.0

    async def _extract_pdf(self, file_bytes: bytes) -> Tuple[str, float]:
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            full_text = "\n".join(text_parts)
            confidence = 0.95 if full_text.strip() else 0.0
            # If native text extraction fails, try OCR
            if not full_text.strip():
                return await self._pdf_ocr_fallback(file_bytes)
            return full_text, confidence
        except Exception as e:
            logger.warning("PDF text extraction failed", error=str(e))
            return "", 0.0

    async def _pdf_ocr_fallback(self, file_bytes: bytes) -> Tuple[str, float]:
        """OCR fallback for scanned/image PDFs."""
        try:
            import pdf2image
            import pytesseract
            images = pdf2image.convert_from_bytes(file_bytes, dpi=300)
            texts = []
            for img in images:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                conf_values = [c for c in data["conf"] if c != -1]
                texts.append(pytesseract.image_to_string(img))
            avg_conf = sum(conf_values) / len(conf_values) / 100 if conf_values else 0.7
            return "\n".join(texts), avg_conf
        except Exception as e:
            logger.warning("PDF OCR fallback failed", error=str(e))
            return "", 0.0

    async def _extract_image_ocr(self, file_bytes: bytes) -> Tuple[str, float]:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            conf_values = [c for c in data["conf"] if c != -1]
            text = pytesseract.image_to_string(img)
            avg_conf = sum(conf_values) / len(conf_values) / 100 if conf_values else 0.7
            return text, avg_conf
        except Exception as e:
            logger.warning("Image OCR failed", error=str(e))
            return "", 0.0

    async def _extract_docx(self, file_bytes: bytes) -> Tuple[str, float]:
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join(para.text for para in doc.paragraphs)
            return text, 1.0
        except Exception as e:
            logger.warning("DOCX extraction failed", error=str(e))
            return "", 0.0


# ─── Silver Layer Pipeline ─────────────────────────────────────────

class SilverPipeline:
    """
    Stage 2 – Normalization & Entity Extraction.
    Responsibilities:
    - Parse structured fields from raw text (NER, regex, heuristics)
    - Validate accounting arithmetic
    - Normalize dates, currencies, account numbers
    - Compute data quality score
    - Link to known institutions in graph
    """

    def __init__(self, storage_path: str = "./data/silver"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def normalize(self, bronze_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Bronze record → Silver normalized record."""
        logger.info("Silver normalization started", doc_id=bronze_record["id"])

        raw_text = bronze_record.get("raw_text", "")
        entities = self._extract_entities(raw_text)
        transactions = self._parse_transactions(raw_text)
        balance_check = self._validate_balances(entities, transactions)
        quality_score = self._compute_quality_score(entities, transactions, bronze_record)

        silver_record = {
            "id": str(uuid.uuid4()),
            "raw_statement_id": bronze_record["id"],
            "customer_id": bronze_record["customer_id"],
            "entities": entities,
            "transactions": transactions,
            "balance_check": balance_check,
            "quality_score": quality_score,
            "statement_type": bronze_record.get("statement_type"),
            "layer": "silver",
            "status": "silver_complete",
            "normalization_timestamp": datetime.utcnow().isoformat(),
        }

        silver_path = self.storage_path / f"{silver_record['id']}.json"
        silver_path.write_text(json.dumps(silver_record, indent=2, default=str))

        logger.info("Silver normalization complete",
                    quality=quality_score,
                    transactions=len(transactions),
                    balance_ok=balance_check.get("is_valid"))
        return silver_record

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract structured entities using regex patterns."""
        entities: Dict[str, Any] = {}

        # Account number (masked)
        acct_match = re.search(
            r'(?:account|acct|acc)[\s#:.]*([*Xx\d]{4,20})', text, re.IGNORECASE
        )
        if acct_match:
            entities["account_number_masked"] = acct_match.group(1)

        # Institution name
        inst_patterns = [
            r'(?:bank|credit union|financial|savings)\b.*?(?=\n|$)',
            r'^([A-Z][A-Za-z\s&.]+(?:Bank|Financial|Credit Union|Savings))',
        ]
        for pat in inst_patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                entities["institution_name"] = m.group(0).strip()[:100]
                break

        # Statement period
        period_match = re.search(
            r'(?:statement period|period)[:\s]+(\d{1,2}/\d{1,2}/\d{2,4})'
            r'\s+(?:to|through|-)\s+(\d{1,2}/\d{1,2}/\d{2,4})',
            text, re.IGNORECASE
        )
        if period_match:
            entities["period_start"] = period_match.group(1)
            entities["period_end"] = period_match.group(2)

        # Balances
        opening_match = re.search(
            r'(?:opening|beginning)\s+balance[\s:$]+([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if opening_match:
            entities["opening_balance"] = self._parse_amount(opening_match.group(1))

        closing_match = re.search(
            r'(?:closing|ending)\s+balance[\s:$]+([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if closing_match:
            entities["closing_balance"] = self._parse_amount(closing_match.group(1))

        # Customer name
        name_match = re.search(
            r'(?:account holder|customer|name)[:\s]+([A-Z][a-zA-Z\s,.-]{2,50})',
            text, re.IGNORECASE
        )
        if name_match:
            entities["customer_name"] = name_match.group(1).strip()

        return entities

    def _parse_transactions(self, text: str) -> List[Dict[str, Any]]:
        """Parse transaction table from statement text."""
        transactions = []

        # Common transaction table pattern: date | description | amount | balance
        pattern = re.compile(
            r'(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\s+'  # date
            r'([A-Za-z0-9\s*#.-]{5,60}?)\s+'             # description
            r'([\d,]+\.\d{2})\s*'                         # amount
            r'(?:([\d,]+\.\d{2}))?',                       # optional balance
            re.MULTILINE
        )
        for match in pattern.finditer(text):
            amount_str = match.group(3)
            transactions.append({
                "date": match.group(1),
                "description": match.group(2).strip(),
                "amount": self._parse_amount(amount_str),
                "balance_after": self._parse_amount(match.group(4)) if match.group(4) else None,
            })
        return transactions[:200]  # Cap at 200 for performance

    def _validate_balances(
        self, entities: Dict[str, Any], transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Accounting identity check:
        opening_balance + Σcredits - Σdebits ≈ closing_balance
        """
        result = {"is_valid": True, "discrepancy": None, "confidence": 0.0}

        opening = entities.get("opening_balance")
        closing = entities.get("closing_balance")

        if opening is None or closing is None:
            result["confidence"] = 0.0
            return result

        total_credits = sum(t["amount"] for t in transactions if t.get("amount", 0) > 0)
        total_debits = sum(abs(t["amount"]) for t in transactions if t.get("amount", 0) < 0)

        computed_closing = opening + total_credits - total_debits
        discrepancy = abs(computed_closing - closing)

        result["is_valid"] = discrepancy < 0.50  # Allow $0.50 rounding tolerance
        result["discrepancy"] = round(discrepancy, 2)
        result["computed_closing"] = round(computed_closing, 2)
        result["stated_closing"] = closing
        result["confidence"] = 0.9

        if not result["is_valid"]:
            logger.warning(
                "Balance arithmetic failed",
                discrepancy=discrepancy,
                computed=computed_closing,
                stated=closing,
            )
        return result

    def _compute_quality_score(
        self,
        entities: Dict[str, Any],
        transactions: List[Dict[str, Any]],
        bronze_record: Dict[str, Any],
    ) -> float:
        """Data quality score [0,1] based on extraction completeness."""
        weights = {
            "has_account_number": 0.1,
            "has_institution": 0.1,
            "has_period": 0.15,
            "has_balances": 0.20,
            "has_transactions": 0.20,
            "balance_valid": 0.15,
            "high_ocr_confidence": 0.10,
        }
        score = 0.0
        score += weights["has_account_number"] if entities.get("account_number_masked") else 0
        score += weights["has_institution"] if entities.get("institution_name") else 0
        score += weights["has_period"] if entities.get("period_start") else 0
        score += weights["has_balances"] if (entities.get("opening_balance") and entities.get("closing_balance")) else 0
        score += weights["has_transactions"] if len(transactions) > 0 else 0
        score += weights["high_ocr_confidence"] if (bronze_record.get("ocr_confidence") or 0) > 0.8 else 0
        return round(min(score, 1.0), 3)

    @staticmethod
    def _parse_amount(s: Optional[str]) -> Optional[float]:
        if not s:
            return None
        try:
            return float(str(s).replace(",", "").replace("$", "").strip())
        except ValueError:
            return None


# ─── Gold Layer Pipeline ──────────────────────────────────────────

class GoldPipeline:
    """
    Stage 3 – Analytics & ML Feature Engineering.
    Responsibilities:
    - Compute fraud feature vectors
    - Generate graph embeddings
    - Produce final risk-scored records
    - Write analytics-ready parquet to gold layer
    """

    def __init__(self, storage_path: str = "./data/gold"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def enrich(
        self,
        silver_record: Dict[str, Any],
        fraud_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Produce Gold layer analytics record."""
        logger.info("Gold enrichment started", silver_id=silver_record["id"])

        features = self._compute_features(silver_record)

        gold_record = {
            "id": str(uuid.uuid4()),
            "silver_statement_id": silver_record["id"],
            "raw_statement_id": silver_record["raw_statement_id"],
            "customer_id": silver_record["customer_id"],
            "features": features,
            "fraud_analysis": fraud_analysis or {},
            "layer": "gold",
            "status": "gold_complete",
            "enrichment_timestamp": datetime.utcnow().isoformat(),
        }

        gold_path = self.storage_path / f"{gold_record['id']}.json"
        gold_path.write_text(json.dumps(gold_record, indent=2, default=str))

        logger.info("Gold enrichment complete", gold_id=gold_record["id"])
        return gold_record

    def _compute_features(self, silver: Dict[str, Any]) -> Dict[str, Any]:
        """Feature vector for ML and anomaly detection."""
        txns = silver.get("transactions", [])
        entities = silver.get("entities", {})
        balance_check = silver.get("balance_check", {})

        amounts = [abs(t.get("amount", 0)) for t in txns if t.get("amount")]
        return {
            "transaction_count": len(txns),
            "total_volume": sum(amounts),
            "avg_transaction_amount": sum(amounts) / len(amounts) if amounts else 0,
            "max_transaction_amount": max(amounts) if amounts else 0,
            "min_transaction_amount": min(amounts) if amounts else 0,
            "round_number_ratio": self._round_number_ratio(amounts),
            "balance_arithmetic_valid": balance_check.get("is_valid", None),
            "balance_discrepancy": balance_check.get("discrepancy", 0),
            "has_institution_name": bool(entities.get("institution_name")),
            "has_account_number": bool(entities.get("account_number_masked")),
            "quality_score": silver.get("quality_score", 0),
            "ocr_confidence": None,  # Passed from bronze if needed
        }

    @staticmethod
    def _round_number_ratio(amounts: List[float]) -> float:
        """Ratio of transactions with suspiciously round amounts (fraud signal)."""
        if not amounts:
            return 0.0
        round_count = sum(1 for a in amounts if a > 0 and a % 100 == 0)
        return round_count / len(amounts)
