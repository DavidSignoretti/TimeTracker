from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from datetime import datetime, date
import io
import os

def calculate_hours(time_in, time_out):
    """Calculate hours between two time objects"""
    # We need to handle overnight shifts
    hours_diff = time_out.hour - time_in.hour
    minutes_diff = time_out.minute - time_in.minute
    
    if hours_diff < 0:  # Overnight shift
        hours_diff += 24
    
    total_minutes = hours_diff * 60 + minutes_diff
    total_hours = total_minutes / 60.0
    
    return round(total_hours, 2)

def generate_invoice_pdf(invoice, company):
    """Generate a PDF invoice"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='RightAlign',
        parent=styles['Normal'],
        alignment=2  # right alignment
    ))
    
    elements = []
    
    # Add company logo and name
    logo_path = os.path.join('static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*inch, height=0.5*inch)
        elements.append(logo)
        elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph(f"<b>{company.company_name}</b>", styles['Heading1']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Company details
    company_address = []
    if company.address:
        company_address.append(company.address)
    if company.city and company.province and company.postal_code:
        company_address.append(f"{company.city}, {company.province} {company.postal_code}")
    if company.phone:
        company_address.append(f"Phone: {company.phone}")
    if company.email:
        company_address.append(f"Email: {company.email}")
    if company.website:
        company_address.append(f"Website: {company.website}")
    if company.tax_number:
        company_address.append(f"Tax Number: {company.tax_number}")
    
    for line in company_address:
        elements.append(Paragraph(line, styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoice details
    elements.append(Paragraph("<b>INVOICE</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    invoice_data = [
        ["Invoice Number:", invoice.invoice_number],
        ["Date Issued:", invoice.date_issued.strftime("%B %d, %Y")],
        ["Date Due:", invoice.date_due.strftime("%B %d, %Y")],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Client details
    client = invoice.client
    elements.append(Paragraph("<b>BILL TO:</b>", styles['Heading3']))
    elements.append(Spacer(1, 0.1*inch))
    
    client_address = [client.name]
    if client.contact_person:
        client_address.append(f"Attn: {client.contact_person}")
    if client.address:
        client_address.append(client.address)
    if client.city and client.province and client.postal_code:
        client_address.append(f"{client.city}, {client.province} {client.postal_code}")
    if client.phone:
        client_address.append(f"Phone: {client.phone}")
    if client.email:
        client_address.append(f"Email: {client.email}")
    
    for line in client_address:
        elements.append(Paragraph(line, styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Time Entries
    elements.append(Paragraph("<b>SERVICES:</b>", styles['Heading3']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Table header
    time_data = [
        ["Date", "Description", "Location", "Hours", "Rate", "Amount"]
    ]
    
    # Table rows for each time entry
    for entry in invoice.time_entries:
        amount = entry.total_hours * entry.hourly_rate
        time_data.append([
            entry.date.strftime("%Y-%m-%d"),
            entry.item,
            entry.location or "",
            f"{entry.total_hours:.2f}",
            f"${entry.hourly_rate:.2f}",
            f"${amount:.2f}"
        ])
    
    # Add subtotal, tax and total rows
    time_data.append(["", "", "", "", "Subtotal:", f"${invoice.subtotal:.2f}"])
    time_data.append(["", "", "", "", f"HST ({invoice.hst_rate*100:.0f}%):", f"${invoice.hst_amount:.2f}"])
    time_data.append(["", "", "", "", "Total:", f"${invoice.total:.2f}"])
    
    # Adjust column widths for time entries table
    col_widths = [1*inch, 2*inch, 1.5*inch, 0.75*inch, 0.75*inch, 1*inch]
    time_table = Table(time_data, colWidths=col_widths)
    
    # Style the table
    style = TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Header alignment
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
        ('ALIGN', (3, 1), (5, -1), 'RIGHT'),  # Right align numbers
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Header underline
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),  # Line above subtotal
        ('FONTNAME', (4, -3), (4, -1), 'Helvetica-Bold'),  # Bold for "Subtotal", "HST", and "Total"
    ])
    
    # Add a thicker line above the total row
    style.add('LINEABOVE', (0, -1), (-1, -1), 2, colors.black)
    
    time_table.setStyle(style)
    elements.append(time_table)
    
    # Add invoice notes if any
    if invoice.notes:
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("<b>NOTES:</b>", styles['Heading3']))
        elements.append(Paragraph(invoice.notes, styles['Normal']))
    
    # Add payment terms
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>PAYMENT TERMS:</b>", styles['Heading3']))
    elements.append(Paragraph("Payment is due within 30 days of invoice date.", styles['Normal']))
    
    # Build the PDF document
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def generate_quote_pdf(quote, company):
    """Generate a PDF quote"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='RightAlign',
        parent=styles['Normal'],
        alignment=2  # right alignment
    ))
    
    elements = []
    
    # Add company logo and name
    logo_path = os.path.join('static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*inch, height=0.5*inch)
        elements.append(logo)
        elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph(f"<b>{company.company_name}</b>", styles['Heading1']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Company details
    company_address = []
    if company.address:
        company_address.append(company.address)
    if company.city and company.province and company.postal_code:
        company_address.append(f"{company.city}, {company.province} {company.postal_code}")
    if company.phone:
        company_address.append(f"Phone: {company.phone}")
    if company.email:
        company_address.append(f"Email: {company.email}")
    if company.website:
        company_address.append(f"Website: {company.website}")
    if company.tax_number:
        company_address.append(f"Tax Number: {company.tax_number}")
    
    for line in company_address:
        elements.append(Paragraph(line, styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Quote details
    elements.append(Paragraph("<b>QUOTE</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    quote_data = [
        ["Quote Number:", quote.quote_number],
        ["Date Issued:", quote.date_issued.strftime("%B %d, %Y")],
        ["Valid Until:", quote.date_valid_until.strftime("%B %d, %Y")],
    ]
    
    quote_table = Table(quote_data, colWidths=[2*inch, 4*inch])
    quote_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
    ]))
    
    elements.append(quote_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Client details
    client = quote.client
    elements.append(Paragraph("<b>PREPARED FOR:</b>", styles['Heading3']))
    elements.append(Spacer(1, 0.1*inch))
    
    client_address = [client.name]
    if client.contact_person:
        client_address.append(f"Attn: {client.contact_person}")
    if client.address:
        client_address.append(client.address)
    if client.city and client.province and client.postal_code:
        client_address.append(f"{client.city}, {client.province} {client.postal_code}")
    if client.phone:
        client_address.append(f"Phone: {client.phone}")
    if client.email:
        client_address.append(f"Email: {client.email}")
    
    for line in client_address:
        elements.append(Paragraph(line, styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Time Entries
    elements.append(Paragraph("<b>SERVICES:</b>", styles['Heading3']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Table header
    time_data = [
        ["Date", "Description", "Location", "Hours", "Rate", "Amount"]
    ]
    
    # Table rows for each time entry
    for entry in quote.time_entries:
        amount = entry.total_hours * entry.hourly_rate
        time_data.append([
            entry.date.strftime("%Y-%m-%d"),
            entry.item,
            entry.location or "",
            f"{entry.total_hours:.2f}",
            f"${entry.hourly_rate:.2f}",
            f"${amount:.2f}"
        ])
    
    # Add subtotal, tax and total rows
    time_data.append(["", "", "", "", "Subtotal:", f"${quote.subtotal:.2f}"])
    time_data.append(["", "", "", "", f"HST ({quote.hst_rate*100:.0f}%):", f"${quote.hst_amount:.2f}"])
    time_data.append(["", "", "", "", "Total:", f"${quote.total:.2f}"])
    
    # Adjust column widths for time entries table
    col_widths = [1*inch, 2*inch, 1.5*inch, 0.75*inch, 0.75*inch, 1*inch]
    time_table = Table(time_data, colWidths=col_widths)
    
    # Style the table
    style = TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Header alignment
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
        ('ALIGN', (3, 1), (5, -1), 'RIGHT'),  # Right align numbers
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Header underline
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),  # Line above subtotal
        ('FONTNAME', (4, -3), (4, -1), 'Helvetica-Bold'),  # Bold for "Subtotal", "HST", and "Total"
    ])
    
    # Add a thicker line above the total row
    style.add('LINEABOVE', (0, -1), (-1, -1), 2, colors.black)
    
    time_table.setStyle(style)
    elements.append(time_table)
    
    # Add quote notes if any
    if quote.notes:
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("<b>NOTES:</b>", styles['Heading3']))
        elements.append(Paragraph(quote.notes, styles['Normal']))
    
    # Add quote terms
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>TERMS AND CONDITIONS:</b>", styles['Heading3']))
    elements.append(Paragraph("This quote is valid until the date specified above. To accept this quote, please contact us.", styles['Normal']))
    
    # Build the PDF document
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data
