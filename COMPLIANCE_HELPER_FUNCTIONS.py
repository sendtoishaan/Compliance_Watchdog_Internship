import pytesseract
import mimetypes
import datetime
from openai import OpenAI
import docx
import re
import os
from PIL import Image
from dotenv import load_dotenv
from pdf2image import convert_from_path
from sentence_transformers import SentenceTransformer, util

load_dotenv() # Loads the variables from .env file

# OPENAI API KEY
OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load/Initialize embedding model globally
EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# Normalizes expiration date strings into a standard date object
def NORMALIZE_DATE(DATE_STR):
    try:
        CLEANED = DATE_STR.strip().replace("-", "/")
        return datetime.datetime.strptime(CLEANED, "%m/%d/%Y").date()
    
    except Exception:
        return DATE_STR

# Toggle between RULE_BASED and LLM explanations
USE_LLM_EXPLANATIONS = False

# Generates an explanation for comparison results
def GENERATE_EXPLANATION(SECTION, APP_ENTRY, AMA_ENTRY, MATCH):
    SECTION = SECTION.strip()
    APP_ENTRY = str(APP_ENTRY).strip()
    AMA_ENTRY = str(AMA_ENTRY).strip()
    
    if USE_LLM_EXPLANATIONS:
        PROMPT = f"""
        Compare the following two {SECTION} entries and explain whether they match:
        Application: {APP_ENTRY}
        AMA: {AMA_ENTRY}
        Match status: {MATCH}
        """
        try:
            RESPONSE = OPENAI_CLIENT.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a compliance auditor providing clear justifications."},
                    {"role": "user", "content": PROMPT}
                ]
            )
            return RESPONSE.choices[0].message["content"].strip()
        
        except Exception as e:
            return f"EXPLANATION_ERROR: {str(e)}"
    
    else:
        if MATCH:
            return f"Both {SECTION} entries align."
        else:
            return f"Discrepancy found in {SECTION}: Application lists {APP_ENTRY}, AMA lists {AMA_ENTRY}."

# --------------- FILE-TYPE FUNCTIONS --------------- #

# Reads .txt files
def READ_TEXT_FILE(TEXT_PATH):
    try:
        with open(TEXT_PATH, "r", encoding="utf-8") as FILE:
            return FILE.read()
    
    except Exception as E:
        return f"READ_TEXT_ERROR: {str(E)}"

# Reads a .docx Word files
def READ_DOCX_FILE(DOCX_PATH):
    try:
        DOC = docx.Document(DOCX_PATH)
        return "\n".join([PARAGRAPH.text for PARAGRAPH in DOC.paragraphs])
    
    except Exception as E:
        return f"READ_DOCX_ERROR: {str(E)}"

# Dispatches to the correct method based on file type
def EXTRACT_TEXT_FROM_FILE(FILE_PATH):
    try:
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

        return f"UNSUPPORTED_FILE_TYPE: {FILE_PATH}"
    
    except Exception as E:
        return f"FILE_EXTRACTION_ERROR: {str(E)}"

# --------------- OCR FUNCTIONS --------------- #

# Uses OCR(Optical Character Recognition) on an image to extract text content
def OCR_IMAGE(IMAGE_PATH):
    try:
        IMAGE = Image.open(IMAGE_PATH)
        return pytesseract.image_to_string(IMAGE)
    
    except Exception as e:
        return f"OCR_ERROR: {str(e)}"

# Uses OCR(Optical Character Recognition) on a PDF file to extract text content
def OCR_PDF(PDF_PATH):
    try:
        PDF_PAGES = convert_from_path(PDF_PATH, dpi=300)
        PDF_CONTENT = ""
        for PAGE in PDF_PAGES:
            PDF_CONTENT += pytesseract.image_to_string(PAGE) + "\n"
        return PDF_CONTENT
    
    except Exception as E:
        return f"OCR_ERROR: {str(E)}"

# --------------- PARSING FUNCTIONS --------------- #

# Extracts the Education field of the compliance application
def EXTRACT_EDUCATION_COMPLIANCE_APPLICATION(FILE_CONTENT):
    try:
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
    
    except Exception:
        return []

# Extracts the Education field of the AMA profile
def EXTRACT_EDUCATION_AMA_PROFILE(FILE_CONTENT):
    try:
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
    
    except Exception:
        return []

# Extracts the Boards field of the compliance application
def EXTRACT_BOARDS_COMPLIANCE_APPLICATION(FILE_CONTENT):
    try:
        ENTRIES = []

        BLOCKS = re.split(r'Board Status\s*:\s*', FILE_CONTENT, flags=re.IGNORECASE)

        for BLOCK in BLOCKS[1:]:
            LINES = BLOCK.strip().splitlines()

            BOARD_NAME = ""
            for LINE in reversed(LINES):
                CLEAN_LINE = LINE.strip()
                if CLEAN_LINE and ':' not in CLEAN_LINE and not CLEAN_LINE.lower().startswith("board status"):
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
    
    except Exception:
        return []

# Extracts the Boards field of the AMA profile
def EXTRACT_BOARDS_AMA_PROFILE(FILE_CONTENT):
    try:
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
    
    except Exception:
        return []

# --------------- COMPARISON FUNCTIONS --------------- #

# AI-based similarity score calculation
def EMBEDDING_SIMILARITY(TEXT1, TEXT2):
    try:
        EMB1 = EMBEDDING_MODEL.encode(TEXT1, convert_to_tensor=True)
        EMB2 = EMBEDDING_MODEL.encode(TEXT2, convert_to_tensor=True)
        return float(util.cos_sim(EMB1, EMB2))
    
    except Exception:
        return 0.0

# Compares information in compliance application with AMA profile data
def COMPARE_INFORMATION(APPLICATION_EDU_DATA=None, AMA_EDU_DATA=None, APPLICATION_BOARD_DATA=None, AMA_BOARD_DATA=None, threshold=0.75):
    try:
        RESULTS = {
            "education": [],
            "boards": []
        }

        # --- EDUCATION COMPARISON ---
        for APP_ENTRY in APPLICATION_EDU_DATA or []:
            BEST_MATCH = None
            BEST_SCORE = 0

            for AMA_ENTRY in AMA_EDU_DATA or []:
                PROGRAM_SCORE = EMBEDDING_SIMILARITY(APP_ENTRY.get("Program", ""), AMA_ENTRY.get("Program", ""))
                SPECIALTY_SCORE = EMBEDDING_SIMILARITY(APP_ENTRY.get("Specialty", ""), AMA_ENTRY.get("Specialty", ""))
                AVERAGE_SCORE = (PROGRAM_SCORE * 0.4) + (SPECIALTY_SCORE * 0.6)

                if AVERAGE_SCORE > BEST_SCORE:
                    BEST_SCORE = AVERAGE_SCORE
                    BEST_MATCH = AMA_ENTRY

            MATCH_STATUS = BEST_SCORE >= threshold

            RESULTS["education"].append({
                "application_entry": APP_ENTRY,
                "matched_ama_entry": BEST_MATCH,
                "match": MATCH_STATUS,
                "explanation": GENERATE_EXPLANATION("education", APP_ENTRY, BEST_MATCH if MATCH_STATUS else {}, MATCH_STATUS)
            })

        # --- BOARDS COMPARISON ---
        for APP_BOARD in APPLICATION_BOARD_DATA or []:
            MATCH_FOUND = False
            EXPLANATION = "No matching AMA entry found."

            for AMA_BOARD in AMA_BOARD_DATA or []:
                BOARD_SCORE = EMBEDDING_SIMILARITY(APP_BOARD.get("Board Name", ""), AMA_BOARD.get("Board Name", ""))
                STATUS_MATCH = APP_BOARD.get("Status", "").lower() == AMA_BOARD.get("Status", "").lower()

                APP_DATE = NORMALIZE_DATE(APP_BOARD.get("Expiration Date", ""))
                AMA_DATE = NORMALIZE_DATE(AMA_BOARD.get("Expiration Date", ""))
                DATE_MATCH = APP_DATE == AMA_DATE

                if BOARD_SCORE >= threshold and STATUS_MATCH and DATE_MATCH:
                    MATCH_FOUND = True
                    EXPLANATION = GENERATE_EXPLANATION("board", APP_BOARD, AMA_BOARD, True)
                    break
                else:
                    EXPLANATION = GENERATE_EXPLANATION("board", APP_BOARD, AMA_BOARD, False)

            RESULTS["boards"].append({
                "application_entry": APP_BOARD,
                "match": MATCH_FOUND,
                "explanation": EXPLANATION
            })

        return RESULTS

    except Exception as E:
        return {"education": [], "boards": [], "error": str(E)}