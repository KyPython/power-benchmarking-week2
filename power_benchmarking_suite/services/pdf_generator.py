"""
PDF Generator

Provides PDF generation for invoices, reports, and documents.
"""

import logging
from typing import Dict, Optional, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available. Install with: pip install reportlab")


class PDFGenerator:
    """PDF generation service."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize PDF generator.

        Args:
            output_dir: Output directory for PDFs (defaults to ~/.power_benchmarking/pdfs)
        """
        if output_dir is None:
            output_dir = Path.home() / ".power_benchmarking" / "pdfs"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not REPORTLAB_AVAILABLE:
            logger.warning("ReportLab not available. PDF generation will be limited.")

    def generate_invoice(
        self,
        invoice: Dict[str, Any],
        client: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate PDF invoice.

        Args:
            invoice: Invoice data
            client: Client data
            output_path: Output file path (defaults to auto-generated)

        Returns:
            Path to generated PDF or None if failed
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available. Cannot generate PDF.")
            return None

        if output_path is None:
            invoice_id = invoice.get("id", "invoice")
            output_path = self.output_dir / f"invoice_{invoice_id}.pdf"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#2563eb"),
                spaceAfter=30,
            )
            story.append(Paragraph("INVOICE", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Invoice details
            invoice_data = [
                ["Invoice ID:", invoice.get("id", "N/A")],
                ["Date:", invoice.get("createdAt", "N/A")[:10]],
                ["Due Date:", invoice.get("dueDate", "N/A")],
                ["Status:", invoice.get("status", "pending").upper()],
            ]

            invoice_table = Table(invoice_data, colWidths=[2 * inch, 4 * inch])
            invoice_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ]
                )
            )
            story.append(invoice_table)
            story.append(Spacer(1, 0.3 * inch))

            # Client info
            story.append(Paragraph("<b>Bill To:</b>", styles["Normal"]))
            story.append(Paragraph(client.get("company", ""), styles["Normal"]))
            story.append(Paragraph(client.get("contact", {}).get("name", ""), styles["Normal"]))
            story.append(Paragraph(client.get("contact", {}).get("email", ""), styles["Normal"]))
            story.append(Spacer(1, 0.3 * inch))

            # Invoice items
            story.append(Paragraph("<b>Description:</b>", styles["Normal"]))
            story.append(Paragraph(invoice.get("description", ""), styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

            # Amount
            amount_data = [
                ["Subtotal:", f"${invoice.get('amount', 0):.2f}"],
                ["Total:", f"<b>${invoice.get('amount', 0):.2f}</b>"],
            ]

            amount_table = Table(amount_data, colWidths=[2 * inch, 4 * inch])
            amount_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 12),
                        ("TOPPADDING", (0, 0), (-1, -1), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ]
                )
            )
            story.append(amount_table)

            # Build PDF
            doc.build(story)

            logger.info(f"Invoice PDF generated: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating invoice PDF: {e}", exc_info=True)
            return None

    def generate_power_report(
        self,
        client_id: str,
        power_data_path: str,
        recommendations: Optional[List[str]] = None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate power analysis report PDF.

        Args:
            client_id: Client ID
            power_data_path: Path to power data CSV
            recommendations: List of recommendations
            output_path: Output file path (defaults to auto-generated)

        Returns:
            Path to generated PDF or None if failed
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available. Cannot generate PDF.")
            return None

        if output_path is None:
            output_path = (
                self.output_dir
                / f"power_report_{client_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#2563eb"),
                spaceAfter=30,
            )
            story.append(Paragraph("Power Analysis Report", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Report info
            report_data = [
                ["Client ID:", client_id],
                ["Report Date:", datetime.utcnow().strftime("%Y-%m-%d")],
                ["Data Source:", power_data_path],
            ]

            report_table = Table(report_data, colWidths=[2 * inch, 4 * inch])
            report_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ]
                )
            )
            story.append(report_table)
            story.append(Spacer(1, 0.3 * inch))

            # Recommendations
            if recommendations:
                story.append(Paragraph("<b>Recommendations:</b>", styles["Heading2"]))
                for rec in recommendations:
                    story.append(Paragraph(f"• {rec}", styles["Normal"]))
                story.append(Spacer(1, 0.2 * inch))

            # Note about data
            story.append(
                Paragraph(
                    "<i>For detailed power analysis, please refer to the CSV data file.</i>",
                    styles["Normal"],
                )
            )

            # Build PDF
            doc.build(story)

            logger.info(f"Power report PDF generated: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating power report PDF: {e}", exc_info=True)
            return None

