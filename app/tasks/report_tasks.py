import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.report import Report, ReportStatus
from app.models.tender import Tender
from app.models.proposal import TenderProposal
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from celery import shared_task
from app.config import settings


UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


@shared_task
def generate_report_task(report_id: int):
    db: Session = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return {"status": "error", "message": "Report not found"}
        
        report.status = ReportStatus.GENERATING
        db.commit()

        # Generate PDF
        pdf_filename = f"report_{report_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title = Paragraph(report.title, styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Content based on report type
        if report.type == "tender_summary":
            tenders = db.query(Tender).all()
            data = [["ID", "Тақырыбы", "Статус", "Дедлайн"]]
            for tender in tenders:
                data.append([tender.id, tender.title, tender.status.value, tender.deadline.strftime("%Y-%m-%d")])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            elements.append(table)

        # Save PDF
        doc.build(elements)

        # Generate Excel
        xlsx_filename = f"report_{report_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        xlsx_path = os.path.join(UPLOAD_DIR, xlsx_filename)
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"
        
        if report.type == "tender_summary":
            ws.append(["ID", "Тақырыбы", "Статус", "Дедлайн"])
            tenders = db.query(Tender).all()
            for tender in tenders:
                ws.append([tender.id, tender.title, tender.status.value, tender.deadline.strftime("%Y-%m-%d")])
            
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")

        wb.save(xlsx_path)

        # Update report
        report.file_path = pdf_path
        report.file_type = "pdf"
        report.status = ReportStatus.COMPLETED
        db.commit()
        
        return {"status": "success", "pdf_path": pdf_path, "xlsx_path": xlsx_path}
    except Exception as e:
        report.status = ReportStatus.FAILED
        db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
