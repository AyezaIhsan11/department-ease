from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from models.student import Student
from datetime import datetime
from typing import List
import io


class PDFReportGenerator:
    """Generate PDF reports for student data"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            spaceBefore=12
        ))
    
    async def generate_monthly_report(self, year: int, month: int) -> io.BytesIO:
        """Generate monthly student report"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph(
            f"Monthly Student Report - {datetime(year, month, 1).strftime('%B %Y')}",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))
        
        # Calculate date range
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Fetch students enrolled in this month
        students = await Student.find({
            "enrollment_date": {
                "$gte": start_date,
                "$lt": end_date
            }
        }).to_list()
        
        # Summary section
        summary_heading = Paragraph("Report Summary", self.styles['CustomHeading'])
        story.append(summary_heading)
        
        summary_data = [
            ['Metric', 'Value'],
            ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M')],
            ['Report Period', f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"],
            ['New Enrollments', str(len(students))],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.5 * inch))
        
        # Student Details Table
        if students:
            details_heading = Paragraph("New Enrolled Students", self.styles['CustomHeading'])
            story.append(details_heading)
            
            table_data = [['ID', 'Name', 'Department', 'Year', 'GPA']]
            for s in students:
                table_data.append([
                    s.student_id,
                    f"{s.first_name} {s.last_name}",
                    s.department,
                    str(s.year),
                    str(s.gpa) if s.gpa is not None else "N/A"
                ])
            
            table = Table(table_data, colWidths=[1.2*inch, 2*inch, 1.5*inch, 0.8*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No new students enrolled in this period.", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    async def generate_yearly_report(self, year: int) -> io.BytesIO:
        """Generate yearly student report"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph(f"Annual Student Report - {year}", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))
        
        # Fetch students enrolled in this year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        
        students = await Student.find({
            "enrollment_date": {
                "$gte": start_date,
                "$lt": end_date
            }
        }).to_list()
        
        # Summary section
        summary_heading = Paragraph("Annual Summary", self.styles['CustomHeading'])
        story.append(summary_heading)
        
        summary_data = [
            ['Metric', 'Value'],
            ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M')],
            ['Academic Year', str(year)],
            ['Total New Enrollments', str(len(students))],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.5 * inch))
        
        # Student Details Table
        if students:
            details_heading = Paragraph("Students Enrolled This Year", self.styles['CustomHeading'])
            story.append(details_heading)
            
            table_data = [['ID', 'Name', 'Department', 'Year', 'GPA']]
            for s in students:
                table_data.append([
                    s.student_id,
                    f"{s.first_name} {s.last_name}",
                    s.department,
                    str(s.year),
                    str(s.gpa) if s.gpa is not None else "N/A"
                ])
            
            table = Table(table_data, colWidths=[1.2*inch, 2*inch, 1.5*inch, 0.8*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            story.append(table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    async def generate_student_list_report(self, students: List[Student]) -> io.BytesIO:
        """Generate detailed student list report"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph("Student Directory Report", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))
        
        # Metadata
        meta = Paragraph(
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>Total Students: {len(students)}",
            self.styles['Normal']
        )
        story.append(meta)
        story.append(Spacer(1, 0.3 * inch))
        
        # Student table
        if students:
            table_data = [['ID', 'Name', 'Email', 'Department', 'Year', 'GPA', 'Status']]
            
            for student in students:
                table_data.append([
                    student.student_id,
                    f"{student.first_name} {student.last_name}",
                    student.email,
                    student.department,
                    str(student.year),
                    str(student.gpa) if student.gpa else 'N/A',
                    student.status
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            story.append(table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer


# Global instance
pdf_generator = PDFReportGenerator()
