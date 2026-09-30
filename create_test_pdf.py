#!/usr/bin/env python3
"""Create a sample PDF for testing the RAG system."""

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter

def create_sample_pdf(filename, title, content_lines):
    """Create a PDF with the given title and content lines."""
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 750, f'{title}')
    
    y_pos = 700
    c.setFont("Helvetica", 12)
    
    for i, line in enumerate(content_lines):
        c.drawString(72, y_pos, f'{line}')
        y_pos -= 15
        
        if y_pos < 72:
            c.showPage()
            y_pos = 750
    
    c.save()
    print(f'Created {filename}')

if __name__ == "__main__":
    # Sample PDF content
    create_sample_pdf(
        'sample_document.pdf',
        'Sample Document - Q3 2024 Report',
        [
            'Executive Summary',
            'This document provides an overview of our quarterly performance metrics.',
            'Key findings from the analysis are presented below.',
            '',
            '1. Financial Performance',
            'Revenue increased by 25% compared to Q2 2024.',
            'Profit margins improved from 12% to 15% YoY.',
            'Operating expenses were reduced by 8% through cost optimization.',
            '',
            '2. Market Analysis',
            'North American region showed 30% growth.',
            'European market expanded by 18% with new product launches.',
            'Asia Pacific represents 25% of total revenue.',
            '',
            '3. Strategic Initiatives',
            'Launched AI-powered customer service platform.',
            'Completed cloud migration for core systems.',
            'Mobile app user base increased by 45%.',
            '',
            '4. Recommendations for Q4 2025',
            'Continue focus on operational efficiency.',
            'Invest in research and development for next-gen products.',
            'Expand into emerging markets in Latin America.',
            '',
            '5. Conclusion',
            'Overall, Q3 2024 was a highly successful quarter.',
            'Strategic initiatives are on track for Q4 delivery.',
            'Thank you for reviewing this report.',
        ]
    )
    
    print('\nPDF creation complete!')