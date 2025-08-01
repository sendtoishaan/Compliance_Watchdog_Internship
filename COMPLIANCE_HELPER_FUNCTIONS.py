import pytesseract
import mimetypes
import docx
import re
from pdf2image import convert_from_path
from fuzzywuzzy import fuzz
from PIL import Image


# --------------- FILE-TYPE FUNCTIONS --------------- #

# Reads .txt files
def READ_TEXT_FILE(TEXT_PATH):
    with open(TEXT_PATH, "r", encoding="utf-8") as file:
        return file.read()

# Reads a .docx Word files
def READ_DOCX_FILE(DOCX_PATH):
    DOC = docx.Document(DOCX_PATH)
    return "\n".join([paragraph.text for paragraph in DOC.paragraphs])

# Dispatches to the correct method based on file type
def EXTRACT_TEXT_FROM_FILE(FILE_PATH):
    MIME_TYPE, _ = mimetypes.guess_type(FILE_PATH)

    if MIME_TYPE:
        if MIME_TYPE.startswith("image"):
            return OCR_IMAGE(FILE_PATH)
        elif MIME_TYPE == "application/pdf":
            return OCR_PDF(FILE_PATH)
        elif MIME_TYPE == "text/plain":
            return READ_TEXT_FILE(FILE_PATH)
        elif MIME_TYPE == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return READ_DOCX_FILE(FILE_PATH)

    raise ValueError(f"Unsupported file type for path: {FILE_PATH}")

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
def EXTRACT_EDUCATION_COMPLAINCE_APPLICATION(FILE_CONTENT):
    ENTRIES = []

    # Split the OCR output using "Activity Name:" since it marks the end of each education entry
    BLOCKS = re.split(r'Activity Name\s*:', FILE_CONTENT, flags=re.IGNORECASE)

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

# Extracts the Education field of the AMA profile
def EXTRACT_EDUCATION_AMA_PROFILE(FILE_CONTENT):
    ENTRIES = []

    BLOCKS = re.findall(r'Sponsoring Institution:\s*(.*?)\n.*?Program name:\s*(.*?)\nSpecialty:\s*(.*?)\n.*?Dates:\s*(\d{2}/\d{2}/\d{4}) - (\d{2}/\d{2}/\d{4})', FILE_CONTENT, re.DOTALL | re.IGNORECASE)

    for institution, program, specialty, start_date, end_date in BLOCKS:
        ENTRIES.append({
            "Institution": institution.strip(),
            "Program": program.strip(),
            "Specialty": specialty.strip(),
            "Start Date": start_date,
            "End Date": end_date
        })
    
    return ENTRIES

# Extracts the Boards field of the compliance application
def EXTRACT_BOARDS_COMPLIANCE_APPLICATION(FILE_CONTENT):
    ENTRIES = []

    BLOCKS = re.split(r'Board Status\s*:\s*', FILE_CONTENT, flags=re.IGNORECASE)

    for BLOCK in BLOCKS[1:]:
        LINES = BLOCK.strip().splitlines()

        MATCH = re.search(r'(.*?)Board Status\s*:\s*' + re.escape(BLOCK[:30]), FILE_CONTENT, re.DOTALL | re.IGNORECASE)
        PRECEDING_TEXT = MATCH.group(1) if MATCH else FILE_CONTENT
        PRECEDING_LINES = PRECEDING_TEXT.strip().splitlines()

        BOARD_NAME = ""
        for LINE in reversed(PRECEDING_LINES):
            CLEAN_LINE = LINE.strip()
            if CLEAN_LINE and ':' not in CLEAN_LINE:
                BOARD_NAME = CLEAN_LINE
                break

        STATUS_MATCH = re.search(r'^(Active|Inactive)', BLOCK.strip(), re.IGNORECASE)
        STATUS = STATUS_MATCH.group(1).strip() if STATUS_MATCH else None

        EXP_MATCH = re.search(r'Expiration\s*Date\s*:\s*(\d{2}[-/]\d{2}[-/]\d{4})', BLOCK, re.IGNORECASE)
        EXPIRATION = EXP_MATCH.group(1).strip() if EXP_MATCH else None

        if BOARD_NAME and STATUS and EXPIRATION:
            ENTRIES.append({
                "Board Name": BOARD_NAME,
                "Status": STATUS,
                "Expiration Date": EXPIRATION
            })

    return ENTRIES

# Extracts the Boards field of the AMA profile
def EXTRACT_BOARDS_AMA_PROFILE(FILE_CONTENT):
    ENTRIES = []

    MATCH = re.search(r'Certifying board:\s*(.*?)\nCertificate:\s*(.*?)\nCertificate type:.*?\n\nDuration Status\s*(.*?)\s+(\d{2}/\d{2}/\d{4})', FILE_CONTENT, re.DOTALL | re.IGNORECASE)

    if MATCH:
        BOARD_NAME = MATCH.group(1).strip()
        CERT = MATCH.group(2).strip()
        STATUS = MATCH.group(3).strip()
        EXPIRATION = MATCH.group(4).strip()

        ENTRIES.append({
            "Board Name": f"{BOARD_NAME} - {CERT}",
            "Status": STATUS,
            "Expiration Date": EXPIRATION
        })

    return ENTRIES

# --------------- COMPARISON FUNCTION --------------- #

# Compares information in compliance application with AMA profile data
def COMPARE_INFORMATION(APPLICATION_EDU_DATA=None, AMA_EDU_DATA=None, APPLICATION_BOARD_DATA=None, AMA_BOARD_DATA=None, threshold=85):
    RESULTS = {
        "education": [],
        "boards": []
    }

    # --- EDUCATION COMPARISON ---
    for APP_ENTRY in APPLICATION_EDU_DATA:
        BEST_MATCH = None
        BEST_SCORE = 0

        for AMA_ENTRY in AMA_EDU_DATA:
            PROGRAM_SCORE = fuzz.token_sort_ratio(APP_ENTRY["Program"], AMA_ENTRY["Program"])
            SPECIALTY_SCORE = fuzz.token_sort_ratio(APP_ENTRY["Specialty"], AMA_ENTRY["Specialty"])
            AVERAGE_SCORE = (PROGRAM_SCORE + SPECIALTY_SCORE) / 2

            if AVERAGE_SCORE > BEST_SCORE:
                BEST_SCORE = AVERAGE_SCORE
                BEST_MATCH = AMA_ENTRY

        RESULTS["education"].append({
            "application_entry": APP_ENTRY,
            "matched_ama_entry": BEST_MATCH,
            "match": BEST_SCORE >= threshold
        })

    # --- BOARDS COMPARISON ---
    if APPLICATION_BOARD_DATA and AMA_BOARD_DATA:
        for APP_BOARD in APPLICATION_BOARD_DATA:
            MATCH_FOUND = False
            for AMA_BOARD in AMA_BOARD_DATA:
                if (
                    APP_BOARD["Board Name"].lower() in AMA_BOARD["Board Name"].lower() and
                    APP_BOARD["Status"].lower() == AMA_BOARD["Status"].lower() and
                    APP_BOARD["Expiration Date"] in AMA_BOARD["Expiration Date"]
                ):
                    MATCH_FOUND = True
                    break

            RESULTS["boards"].append({
                "application_entry": APP_BOARD,
                "match": MATCH_FOUND
            })

    return RESULTS