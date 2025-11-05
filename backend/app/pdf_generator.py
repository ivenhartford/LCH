"""
PDF Generation Module for Lenox Cat Hospital

This module provides utilities for generating various PDF documents including:
- Vaccination certificates
- Health certificates
- Medical record summaries

Uses ReportLab for PDF generation.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PDFGenerator:
    """Base class for PDF generation with common utilities"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles"""
        self.styles.add(
            ParagraphStyle(
                name="CenterHeading",
                parent=self.styles["Heading1"],
                alignment=TA_CENTER,
                fontSize=16,
                spaceAfter=12,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CenterSubheading",
                parent=self.styles["Heading2"],
                alignment=TA_CENTER,
                fontSize=12,
                textColor=colors.HexColor("#666666"),
                spaceAfter=20,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Label",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#666666"),
                spaceAfter=2,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Value",
                parent=self.styles["Normal"],
                fontSize=11,
                spaceAfter=10,
            )
        )

    def create_header(self, clinic_name="Lenox Cat Hospital", subtitle=None):
        """Create a standard header for documents"""
        elements = []

        # Clinic name
        title = Paragraph(clinic_name, self.styles["CenterHeading"])
        elements.append(title)

        # Subtitle
        if subtitle:
            subtitle_para = Paragraph(subtitle, self.styles["CenterSubheading"])
            elements.append(subtitle_para)

        # Clinic information
        clinic_info = """
        123 Main Street, Anytown, State 12345<br/>
        Phone: (555) 123-4567 | Fax: (555) 123-4568<br/>
        Email: info@lenoxcathospital.com<br/>
        www.lenoxcathospital.com
        """
        clinic_para = Paragraph(clinic_info, self.styles["CenterSubheading"])
        elements.append(clinic_para)

        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def create_section_header(self, title):
        """Create a section header"""
        style = ParagraphStyle(
            name="SectionHeader",
            parent=self.styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#2196F3"),
            spaceAfter=10,
            spaceBefore=15,
        )
        return Paragraph(title, style)

    def create_field(self, label, value):
        """Create a labeled field"""
        elements = []
        elements.append(Paragraph(f"<b>{label}:</b>", self.styles["Label"]))
        elements.append(Paragraph(str(value) if value else "N/A", self.styles["Value"]))
        return elements

    def create_signature_section(self, veterinarian_name=None):
        """Create a signature section"""
        elements = []
        elements.append(Spacer(1, 0.5 * inch))

        # Signature line
        sig_data = [
            ["", ""],
            ["Veterinarian Signature: _______________________", f"Date: {datetime.now().strftime('%m/%d/%Y')}"],
        ]

        if veterinarian_name:
            sig_data.append([f"Printed Name: {veterinarian_name}", ""])

        sig_table = Table(sig_data, colWidths=[3.5 * inch, 2.5 * inch])
        sig_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(sig_table)

        return elements


class VaccinationCertificateGenerator(PDFGenerator):
    """Generator for vaccination certificates"""

    def generate(self, patient_data, vaccination_data, owner_data):
        """
        Generate a vaccination certificate PDF

        Args:
            patient_data: Dictionary with patient information
            vaccination_data: Dictionary with vaccination details
            owner_data: Dictionary with owner information

        Returns:
            BytesIO object containing the PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)

        elements = []

        # Header
        elements.extend(self.create_header(subtitle="Certificate of Vaccination"))

        # Certificate number
        cert_number = Paragraph(
            f"<b>Certificate No:</b> {vaccination_data.get('id', 'N/A')}",
            self.styles["Normal"],
        )
        elements.append(cert_number)
        elements.append(Spacer(1, 0.2 * inch))

        # Patient Information Section
        elements.append(self.create_section_header("Patient Information"))

        patient_info_data = [
            ["Patient Name:", patient_data.get("name", "N/A"), "Species:", "Feline (Cat)"],
            [
                "Breed:",
                patient_data.get("breed", "N/A"),
                "Color:",
                patient_data.get("color", "N/A"),
            ],
            [
                "Sex:",
                patient_data.get("sex", "N/A"),
                "Date of Birth:",
                patient_data.get("date_of_birth", "N/A"),
            ],
            [
                "Microchip #:",
                patient_data.get("microchip_number", "N/A"),
                "Weight:",
                f"{patient_data.get('weight', 'N/A')} lbs",
            ],
        ]

        patient_table = Table(patient_info_data, colWidths=[1.3 * inch, 2.2 * inch, 1.3 * inch, 2.2 * inch])
        patient_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E3F2FD")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#E3F2FD")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(patient_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Owner Information Section
        elements.append(self.create_section_header("Owner Information"))

        owner_info_data = [
            ["Owner Name:", owner_data.get("name", "N/A"), "Phone:", owner_data.get("phone", "N/A")],
            [
                "Address:",
                owner_data.get("address", "N/A"),
                "Email:",
                owner_data.get("email", "N/A"),
            ],
        ]

        owner_table = Table(owner_info_data, colWidths=[1.3 * inch, 2.2 * inch, 1.3 * inch, 2.2 * inch])
        owner_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F5E9")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#E8F5E9")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(owner_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Vaccination Information Section
        elements.append(self.create_section_header("Vaccination Details"))

        vacc_info_data = [
            ["Vaccine Name:", vaccination_data.get("vaccine_name", "N/A")],
            ["Manufacturer:", vaccination_data.get("manufacturer", "N/A")],
            ["Lot/Serial Number:", vaccination_data.get("lot_number", "N/A")],
            ["Date Administered:", vaccination_data.get("administered_date", "N/A")],
            ["Expiration Date:", vaccination_data.get("expiration_date", "N/A")],
            ["Next Due Date:", vaccination_data.get("next_due_date", "N/A")],
            ["Administered By:", vaccination_data.get("administered_by", "N/A")],
        ]

        vacc_table = Table(vacc_info_data, colWidths=[2 * inch, 5 * inch])
        vacc_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#FFF3E0")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(vacc_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Notes section if any
        if vaccination_data.get("notes"):
            elements.append(self.create_section_header("Additional Notes"))
            notes = Paragraph(vaccination_data.get("notes", ""), self.styles["Normal"])
            elements.append(notes)

        # Signature section
        elements.extend(self.create_signature_section(vaccination_data.get("administered_by")))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer


class HealthCertificateGenerator(PDFGenerator):
    """Generator for health certificates"""

    def generate(self, patient_data, exam_data, owner_data):
        """
        Generate a health certificate PDF

        Args:
            patient_data: Dictionary with patient information
            exam_data: Dictionary with examination details
            owner_data: Dictionary with owner information

        Returns:
            BytesIO object containing the PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)

        elements = []

        # Header
        elements.extend(self.create_header(subtitle="Health Certificate"))

        # Certificate number
        cert_number = Paragraph(
            f"<b>Certificate No:</b> {exam_data.get('certificate_number', 'N/A')}",
            self.styles["Normal"],
        )
        elements.append(cert_number)
        elements.append(Spacer(1, 0.2 * inch))

        # Purpose
        purpose = Paragraph(
            f"<b>Purpose:</b> {exam_data.get('purpose', 'General Health Assessment')}",
            self.styles["Normal"],
        )
        elements.append(purpose)
        elements.append(Spacer(1, 0.2 * inch))

        # Patient Information
        elements.append(self.create_section_header("Patient Information"))
        patient_info_data = [
            ["Patient Name:", patient_data.get("name", "N/A"), "Species:", "Feline (Cat)"],
            ["Breed:", patient_data.get("breed", "N/A"), "Color:", patient_data.get("color", "N/A")],
            ["Sex:", patient_data.get("sex", "N/A"), "Age:", patient_data.get("age", "N/A")],
            [
                "Microchip #:",
                patient_data.get("microchip_number", "N/A"),
                "Weight:",
                f"{patient_data.get('weight', 'N/A')} lbs",
            ],
        ]

        patient_table = Table(patient_info_data, colWidths=[1.3 * inch, 2.2 * inch, 1.3 * inch, 2.2 * inch])
        patient_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E3F2FD")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#E3F2FD")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(patient_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Owner Information
        elements.append(self.create_section_header("Owner Information"))
        owner_info_data = [
            ["Owner Name:", owner_data.get("name", "N/A"), "Phone:", owner_data.get("phone", "N/A")],
            ["Address:", owner_data.get("address", "N/A"), "Email:", owner_data.get("email", "N/A")],
        ]

        owner_table = Table(owner_info_data, colWidths=[1.3 * inch, 2.2 * inch, 1.3 * inch, 2.2 * inch])
        owner_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F5E9")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#E8F5E9")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(owner_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Physical Examination
        elements.append(self.create_section_header("Physical Examination"))

        exam_date = Paragraph(
            f"<b>Examination Date:</b> {exam_data.get('exam_date', 'N/A')}",
            self.styles["Normal"],
        )
        elements.append(exam_date)
        elements.append(Spacer(1, 0.1 * inch))

        # Vital Signs
        vitals_data = [
            ["Temperature:", f"{exam_data.get('temperature', 'N/A')}°F", "Heart Rate:", f"{exam_data.get('heart_rate', 'N/A')} bpm"],
            [
                "Respiratory Rate:",
                f"{exam_data.get('respiratory_rate', 'N/A')} rpm",
                "Weight:",
                f"{exam_data.get('weight', 'N/A')} lbs",
            ],
        ]

        vitals_table = Table(vitals_data, colWidths=[1.5 * inch, 2 * inch, 1.5 * inch, 2 * inch])
        vitals_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#FFF3E0")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#FFF3E0")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(vitals_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Examination Findings
        findings = Paragraph(
            f"<b>Findings:</b><br/>{exam_data.get('findings', 'Patient appears healthy with no abnormalities detected.')}",
            self.styles["Normal"],
        )
        elements.append(findings)
        elements.append(Spacer(1, 0.2 * inch))

        # Health Status
        health_status = exam_data.get("health_status", "HEALTHY")
        status_color = colors.green if health_status == "HEALTHY" else colors.orange

        status_para = Paragraph(
            f"<b>Health Status:</b> <font color='{status_color}'><b>{health_status}</b></font>",
            self.styles["Normal"],
        )
        elements.append(status_para)
        elements.append(Spacer(1, 0.2 * inch))

        # Certification Statement
        cert_statement = Paragraph(
            "<i>I hereby certify that I have examined the above-named animal and that, to the best of my knowledge, "
            "the animal is free from clinical signs of infectious, contagious, or communicable disease and is fit "
            "for the stated purpose.</i>",
            self.styles["Normal"],
        )
        elements.append(cert_statement)

        # Signature section
        elements.extend(self.create_signature_section(exam_data.get("examined_by")))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer


class MedicalRecordSummaryGenerator(PDFGenerator):
    """Generator for medical record summaries"""

    def generate(self, patient_data, owner_data, visits_data, vaccinations_data):
        """
        Generate a medical record summary PDF

        Args:
            patient_data: Dictionary with patient information
            owner_data: Dictionary with owner information
            visits_data: List of visit dictionaries
            vaccinations_data: List of vaccination dictionaries

        Returns:
            BytesIO object containing the PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)

        elements = []

        # Header
        elements.extend(self.create_header(subtitle="Medical Record Summary"))

        # Report date
        report_date = Paragraph(
            f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y')}",
            self.styles["Normal"],
        )
        elements.append(report_date)
        elements.append(Spacer(1, 0.2 * inch))

        # Patient Information
        elements.append(self.create_section_header("Patient Information"))
        patient_info_data = [
            ["Patient Name:", patient_data.get("name", "N/A"), "Patient ID:", f"#{patient_data.get('id', 'N/A')}"],
            ["Breed:", patient_data.get("breed", "N/A"), "Color:", patient_data.get("color", "N/A")],
            [
                "Sex:",
                patient_data.get("sex", "N/A"),
                "Reproductive Status:",
                patient_data.get("reproductive_status", "N/A"),
            ],
            [
                "Date of Birth:",
                patient_data.get("date_of_birth", "N/A"),
                "Age:",
                patient_data.get("age", "N/A"),
            ],
            [
                "Microchip #:",
                patient_data.get("microchip_number", "N/A"),
                "Weight:",
                f"{patient_data.get('weight', 'N/A')} lbs",
            ],
        ]

        patient_table = Table(patient_info_data, colWidths=[1.5 * inch, 2 * inch, 1.5 * inch, 2 * inch])
        patient_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E3F2FD")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#E3F2FD")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(patient_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Owner Information
        elements.append(self.create_section_header("Owner Information"))
        owner_info_data = [
            ["Owner Name:", owner_data.get("name", "N/A"), "Phone:", owner_data.get("phone", "N/A")],
            ["Address:", owner_data.get("address", "N/A"), "Email:", owner_data.get("email", "N/A")],
        ]

        owner_table = Table(owner_info_data, colWidths=[1.5 * inch, 2 * inch, 1.5 * inch, 2 * inch])
        owner_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F5E9")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#E8F5E9")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(owner_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Allergies and Medical Conditions
        if patient_data.get("allergies") or patient_data.get("medical_conditions"):
            elements.append(self.create_section_header("Allergies & Medical Conditions"))

            if patient_data.get("allergies"):
                allergies = Paragraph(
                    f"<b>Known Allergies:</b> {patient_data.get('allergies', 'None')}",
                    self.styles["Normal"],
                )
                elements.append(allergies)

            if patient_data.get("medical_conditions"):
                conditions = Paragraph(
                    f"<b>Medical Conditions:</b> {patient_data.get('medical_conditions', 'None')}",
                    self.styles["Normal"],
                )
                elements.append(conditions)

            elements.append(Spacer(1, 0.2 * inch))

        # Vaccination History
        if vaccinations_data and len(vaccinations_data) > 0:
            elements.append(self.create_section_header("Vaccination History"))

            vacc_table_data = [["Date", "Vaccine", "Manufacturer", "Next Due"]]
            for vacc in vaccinations_data[:10]:  # Limit to 10 most recent
                vacc_table_data.append(
                    [
                        vacc.get("administered_date", "N/A"),
                        vacc.get("vaccine_name", "N/A"),
                        vacc.get("manufacturer", "N/A"),
                        vacc.get("next_due_date", "N/A"),
                    ]
                )

            vacc_table = Table(vacc_table_data, colWidths=[1.5 * inch, 2.5 * inch, 2 * inch, 1 * inch])
            vacc_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF3E0")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(vacc_table)
            elements.append(Spacer(1, 0.2 * inch))

        # Visit History
        if visits_data and len(visits_data) > 0:
            elements.append(self.create_section_header("Recent Visit History"))

            for i, visit in enumerate(visits_data[:5]):  # Limit to 5 most recent visits
                visit_header = Paragraph(
                    f"<b>Visit Date:</b> {visit.get('visit_date', 'N/A')} | "
                    f"<b>Type:</b> {visit.get('visit_type', 'N/A')}",
                    self.styles["Normal"],
                )
                elements.append(visit_header)

                if visit.get("chief_complaint"):
                    complaint = Paragraph(
                        f"<b>Chief Complaint:</b> {visit.get('chief_complaint')}",
                        self.styles["Normal"],
                    )
                    elements.append(complaint)

                if visit.get("diagnosis"):
                    diagnosis = Paragraph(
                        f"<b>Diagnosis:</b> {visit.get('diagnosis')}",
                        self.styles["Normal"],
                    )
                    elements.append(diagnosis)

                if visit.get("treatment"):
                    treatment = Paragraph(
                        f"<b>Treatment:</b> {visit.get('treatment')}",
                        self.styles["Normal"],
                    )
                    elements.append(treatment)

                elements.append(Spacer(1, 0.15 * inch))

                # Add page break after 2 visits if more visits exist
                if i == 1 and len(visits_data) > 2:
                    elements.append(PageBreak())

        # Footer note
        elements.append(Spacer(1, 0.3 * inch))
        footer = Paragraph(
            "<i>This is a summary of medical records. For complete details, please contact the clinic.</i>",
            self.styles["Normal"],
        )
        elements.append(footer)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
