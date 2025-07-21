import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
from fuzzywuzzy import fuzz
import os

# --------------- OCR FUNCTIONS --------------- #

# Uses OCR(Optical Character Recognition) on an image to extract text content
def OCR_IMAGE(IMAGE_PATH):
    IMAGE = Image.open(IMAGE_PATH)
    return pytesseract.image_to_string(IMAGE)

# Uses OCR(Optical Character Recognition) on a PDF file to extract text content
def OCR_PDF(PDF_PATH):
    PDF_PAGES = convert_from_path(PDF_PATH, dpi=300)
    PDF_CONTENT = ""
    for page in PDF_PAGES:
        PDF_CONTENT += pytesseract.image_to_string(page) + "\n"
    return PDF_CONTENT

# --------------- PARSING FUNCTIONS --------------- #

# Extracts the Education field of the compliance application
def EXTRACT_EDUCATION_COMPLAINCE_APPLICATION(PDF_CONTENT):
    ENTRIES = []

    # Split the OCR output using "Activity Name:" since it marks the end of each education entry
    BLOCKS = re.split(r'Activity Name\s*:', PDF_CONTENT, flags=re.IGNORECASE)

    for BLOCK in BLOCKS:
        PROGRAM = SPECIALTY = START_DATE = END_DATE = None

        PROGRAM_MATCH = re.search(r'Program\s*[:\.\-]?\s*(.*)', BLOCK, re.IGNORECASE)
        if PROGRAM_MATCH:
            PROGRAM = PROGRAM_MATCH.group(1).strip()

        SPECIALTY_MATCH = re.search(r'Dept.*?Special.*?[:\.\-]?\s*(.*)', BLOCK, re.IGNORECASE)
        if SPECIALTY_MATCH:
            SPECIALTY = SPECIALTY_MATCH.group(1).strip()

        START_DATE_MATCH = re.search(r'Start\s*Date\s*[:\.\-]?\s*(.*)', BLOCK, re.IGNORECASE)
        if START_DATE_MATCH:
            START_DATE = START_DATE_MATCH.group(1).strip()

        END_DATE_MATCH = re.search(r'End\s*Date\s*[:\.\-]?\s*(.*)', BLOCK, re.IGNORECASE)
        if END_DATE_MATCH:
            END_DATE = END_DATE_MATCH.group(1).strip()

        if all([PROGRAM, SPECIALTY, START_DATE, END_DATE]):
            ENTRIES.append({
                "Program": PROGRAM,
                "Specialty": SPECIALTY,
                "Start Date": START_DATE,
                "End Date": END_DATE
            })

    return ENTRIES

# Extracts the Education field of the AMA profile pdf
def EXTRACT_EDUCATION_AMA_PROFILE(PDF_CONTENT):
    ENTRIES = []

    BLOCKS = re.findall(r'Sponsoring Institution:\s*(.*?)\n.*?Program name:\s*(.*?)\nSpecialty:\s*(.*?)\n.*?Dates:\s*(\d{2}/\d{2}/\d{4}) - (\d{2}/\d{2}/\d{4})', PDF_CONTENT, re.DOTALL | re.IGNORECASE)

    for institution, program, specialty, start_date, end_date in BLOCKS:
        ENTRIES.append({
            "Institution": institution.strip(),
            "Program": program.strip(),
            "Specialty": specialty.strip(),
            "Start Date": start_date,
            "End Date": end_date
        })
    
    return ENTRIES

# --------------- COMPARISON FUNCTIONS --------------- #

# Compares information in compliance application with AMA profile data
def COMPARE_INFORMATION(APPLICATION_DATA, AMA_PROFILE_DATA, threshold=85):
    RESULTS = []

    for APPLICATION_ENTRY in APPLICATION_DATA:
        BEST_MATCH = None
        BEST_SCORE = 0

        for AMA_ENTRY in AMA_PROFILE_DATA:
            PROGRAM_SCORE = fuzz.token_sort_ratio(APPLICATION_ENTRY["Program"], AMA_ENTRY["Program"])
            SPECIALTY_SCORE = fuzz.token_sort_ratio(APPLICATION_ENTRY["Specialty"], AMA_ENTRY["Specialty"])
            AVERAGE_SCORE = (PROGRAM_SCORE + SPECIALTY_SCORE) / 2

            if AVERAGE_SCORE > BEST_SCORE:
                BEST_SCORE = AVERAGE_SCORE
                BEST_MATCH = AMA_ENTRY
        
        RESULTS.append({
            "application_entry": APPLICATION_ENTRY,
            "matched_ama_entry": BEST_MATCH,
            "similarity_score": BEST_SCORE,
            "match": BEST_SCORE >= threshold
        })

    return RESULTS