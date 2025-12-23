"""
Generate a simple PDF for validation testing.

Uses reportlab to create a 1-page PDF with sample insurance text.
"""
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def create_sample_pdf(output_path: Path):
    """
    Create a simple PDF for validation.

    Args:
        output_path: Path to save PDF
    """
    if not REPORTLAB_AVAILABLE:
        print("⚠️  reportlab not installed. Creating text-only PDF using minimal method.")
        # Fallback: Create minimal PDF structure manually
        create_minimal_pdf(output_path)
        return

    # Create PDF with reportlab
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Samsung Cancer Plus Insurance")

    # Content (Korean text - using Helvetica as fallback)
    c.setFont("Helvetica", 12)
    y = height - 150

    lines = [
        "Article 1 (Insurance Payment)",
        "- General cancer diagnosis: 50,000,000 KRW",
        "- Carcinoma in situ: 10,000,000 KRW",
        "",
        "Article 2 (Premium Payment)",
        "- Monthly premium payment required",
    ]

    for line in lines:
        c.drawString(100, y, line)
        y -= 20

    c.save()
    print(f"✅ PDF created: {output_path}")


def create_minimal_pdf(output_path: Path):
    """
    Create a minimal valid PDF without external dependencies.

    This creates a very simple PDF structure that PyMuPDF can read.
    """
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
50 700 Td
(Samsung Cancer Plus Insurance) Tj
0 -20 Td
(General cancer diagnosis: 50,000,000 KRW) Tj
0 -20 Td
(Carcinoma in situ: 10,000,000 KRW) Tj
0 -20 Td
(Monthly premium payment required) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
569
%%EOF
"""

    with open(output_path, 'wb') as f:
        f.write(pdf_content)

    print(f"✅ Minimal PDF created: {output_path}")


if __name__ == "__main__":
    output = Path(__file__).parent.parent / "data/raw/SAMSUNG/약관/sample.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)

    create_sample_pdf(output)
