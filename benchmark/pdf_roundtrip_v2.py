"""Render selected synthetic statements to vector-text PDFs and verify extraction.

No real bank branding, actual account numbers, or confidential data. These
generated PDFs do NOT reproduce real-scanned forgery or institution formats.
"""
import argparse
import csv
import io
import json
from pathlib import Path

def render(statement_text, case_id):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer
    from reportlab.lib import colors
    buffer=io.BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=letter,
                          leftMargin=42,rightMargin=42,topMargin=42,bottomMargin=36)
    styles=getSampleStyleSheet()
    mono=ParagraphStyle("mono",fontName="Courier",fontSize=7.2,leading=10,
                        textColor=colors.black,spaceAfter=0)
    story=[
        Paragraph("SYNTHETIC FINANCIAL STATEMENT — RESEARCH TEST ONLY",
                  styles["Heading3"]),
        Paragraph("No real account, bank endorsement, or fraud allegation.",
                  styles["BodyText"]),
        Spacer(1,10),
        Preformatted(statement_text,mono)
    ]
    doc.build(story)
    return buffer.getvalue()

def verify(pdf_bytes,row):
    import pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        extracted="\n".join((p.extract_text() or "") for p in pdf.pages)
    assert "SYNTHETIC FINANCIAL STATEMENT" in extracted
    for field in ("Institution:","Account:","Opening balance:","Closing balance:"):
        assert field in extracted, field
    # Validate exact monetary balance is present after PDF generation/extraction;
    # do not trust the parser simply because the file exists.
    import re
    closing=re.search(r"Closing balance: ([0-9]+\.[0-9]{2})",row["statement_text"])
    assert closing is not None and closing.group(1) in extracted
    return extracted

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="artifacts/fraudrag_v2/held_out_cases.csv")
    p.add_argument("--out",default="artifacts/fraudrag_v2/pdf_validation")
    args=p.parse_args()
    with open(args.source,newline="",encoding="utf8") as f:
        rows=list(csv.DictReader(f))
    output=Path(args.out)
    output.mkdir(parents=True,exist_ok=True)
    results=[]
    for row in rows:
        blob=render(row["statement_text"],row["case_id"])
        pdf_path=output/(row["case_id"]+".pdf")
        pdf_path.write_bytes(blob)
        text=verify(blob,row)
        results.append({"case_id":row["case_id"],"bytes":len(blob),
                        "extracted_characters":len(text),"digital_pdf_verified":True})
    (output/"pdf_validation.json").write_text(json.dumps({
        "task":"digital vector-text PDF round-trip only",
        "n":len(results),"scanned_images_tested":0,
        "real_bank_statements_tested":0,"cases":results
    },indent=2)+"\n")
    print(f"PASS: {len(results)} synthetic digital-PDF generation and extraction checks")

if __name__=="__main__":
    main()
