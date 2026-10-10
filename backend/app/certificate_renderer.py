"""Draws one certificate PDF. This file knows nothing about the database."""
import io
from datetime import datetime

import qrcode
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
CENTER_X = PAGE_WIDTH / 2

INK = HexColor("#14213D")
GOLD = HexColor("#B8892B")
GREY = HexColor("#5A6270")

TEXT_WIDTH = PAGE_WIDTH - 180
QR_SIZE = 100


def fit_font_size(text, font_name, max_size, min_size, max_width):
    # Start big and shrink until the text fits, so long names stay on the page.
    size = max_size
    while size > min_size and stringWidth(text, font_name, size) > max_width:
        size = size - 1
    return size


def pretty_date(issue_date):
    # issue_date was already validated as YYYY-MM-DD before it got here.
    return datetime.strptime(issue_date, "%Y-%m-%d").strftime("%d %B %Y")


def make_qr_image(url):
    image = qrcode.make(url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return ImageReader(buffer)


def draw_borders(pdf):
    pdf.setStrokeColor(INK)
    pdf.setLineWidth(3)
    pdf.rect(24, 24, PAGE_WIDTH - 48, PAGE_HEIGHT - 48)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1)
    pdf.rect(34, 34, PAGE_WIDTH - 68, PAGE_HEIGHT - 68)


def draw_centered(pdf, text, y, font_name, size, color):
    pdf.setFont(font_name, size)
    pdf.setFillColor(color)
    pdf.drawCentredString(CENTER_X, y, text)


def render_certificate(output_path, recipient_name, event_name, issue_date, issuer_name, verify_url):
    recipient_name = recipient_name.strip()
    event_name = event_name.strip()
    issuer_name = issuer_name.strip()

    pdf = canvas.Canvas(output_path, pagesize=landscape(A4))
    draw_borders(pdf)

    draw_centered(pdf, "Certificate of Completion", PAGE_HEIGHT - 120, "Times-Bold", 38, INK)
    draw_centered(pdf, "This is to certify that", PAGE_HEIGHT - 170, "Helvetica", 15, GREY)

    name_size = fit_font_size(recipient_name, "Times-BoldItalic", 42, 10, TEXT_WIDTH)
    draw_centered(pdf, recipient_name, PAGE_HEIGHT - 232, "Times-BoldItalic", name_size, INK)

    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1)
    pdf.line(CENTER_X - 220, PAGE_HEIGHT - 246, CENTER_X + 220, PAGE_HEIGHT - 246)

    draw_centered(pdf, "has successfully completed", PAGE_HEIGHT - 285, "Helvetica", 15, GREY)

    event_size = fit_font_size(event_name, "Helvetica-Bold", 26, 10, TEXT_WIDTH)
    draw_centered(pdf, event_name, PAGE_HEIGHT - 325, "Helvetica-Bold", event_size, INK)

    draw_centered(pdf, "Issued on " + pretty_date(issue_date), PAGE_HEIGHT - 365, "Helvetica", 13, GREY)

    # Issuer signature block, bottom left.
    pdf.setStrokeColor(INK)
    pdf.setLineWidth(0.8)
    pdf.line(80, 105, 290, 105)
    issuer_size = fit_font_size(issuer_name, "Helvetica-Bold", 13, 8, 210)
    pdf.setFont("Helvetica-Bold", issuer_size)
    pdf.setFillColor(INK)
    pdf.drawString(80, 88, issuer_name)
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(GREY)
    pdf.drawString(80, 74, "Issued by")

    # QR code, bottom right: scanning it opens the verification page.
    qr_x = PAGE_WIDTH - 70 - QR_SIZE
    pdf.drawImage(make_qr_image(verify_url), qr_x, 62, width=QR_SIZE, height=QR_SIZE)
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(GREY)
    pdf.drawCentredString(qr_x + QR_SIZE / 2, 50, "Scan to verify")

    pdf.save()
