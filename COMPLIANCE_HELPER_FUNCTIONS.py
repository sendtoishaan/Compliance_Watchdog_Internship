import pytesseract
import mimetypes
import datetime
import docx
import re
from PIL import Image
from pdf2image import convert_from_path
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

# Hugging Face LLM pipeline
LLM_PIPELINE = pipeline("text2text-generation", model="google/flan-t5-base")

# Load/Initialize embedding model globally
EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# Normalizes expiration date strings into a standard date object
def NORMALIZE_DATE(DATE_STR):
    DATE_STR = str(DATE_STR).strip()
    DATE_STR = DATE_STR.replace("-", "/")
    FORMATS = ["%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d", "%m/%d/%Y", "%m/%d/%y"]

    for FMT in FORMATS:
        try:
            return datetime.datetime.strptime(DATE_STR, FMT).date()
        
        except Exception:
            continue

    return DATE_STR

# Toggle between RULE_BASED and LLM explanations
USE_LLM_EXPLANATIONS = True

# Generates an explanation for comparison results
def GENERATE_EXPLANATION(SECTION, APP_ENTRY, AMA_ENTRY, MATCH):
    SECTION = SECTION.strip()
    APP_ENTRY_STR = str(APP_ENTRY).strip()
    AMA_ENTRY_STR = str(AMA_ENTRY).strip() if AMA_ENTRY else "No AMA entry found"

    if not USE_LLM_EXPLANATIONS:
        if MATCH:
            return f"Both entries align. Application entry: {APP_ENTRY_STR} AMA entry: {AMA_ENTRY_STR}"
        else:
            return f"Discrepancy: Application entry: {APP_ENTRY_STR} AMA entry: {AMA_ENTRY_STR}"

    if not AMA_ENTRY:
        return "No matching AMA entry found."

    PROMPT = f"""
    You are a compliance auditor. Compare the following two {SECTION} entries.

    Application entry: {APP_ENTRY_STR}
    AMA entry: {AMA_ENTRY_STR}

    Explain concisely whether they match. If they do not match, clearly describe the differences (e.g., program name, specialty, dates, board name, status). 
    Respond in 1–3 sentences only. Do NOT repeat text or add unrelated information.
    """

    try:
        RESULT = LLM_PIPELINE(PROMPT, max_length=100, do_sample=False)
        return RESULT[0]["generated_text"].strip()

    except Exception as e:
        return f"EXPLANATION_ERROR: {str(e)}"

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
        text = pytesseract.image_to_string(IMAGE)
        return text if text.strip() else "OCR_EMPTY"
    
    except Exception as e:
        return f"OCR_ERROR: {str(e)}"

# Uses OCR(Optical Character Recognition) on a PDF file to extract text content
def OCR_PDF(PDF_PATH):
    try:
        PDF_PAGES = convert_from_path(PDF_PATH, dpi=300)
        PDF_CONTENT = ""
        for PAGE in PDF_PAGES:
            PAGE_TEXT = pytesseract.image_to_string(PAGE)
            PDF_CONTENT += PAGE_TEXT.strip() + "\n" if PAGE_TEXT.strip() else "OCR_EMPTY\n"
        return PDF_CONTENT
    
    except Exception as e:
        return f"OCR_ERROR: {str(e)}"

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

        BLOCKS = re.findall(
            r'Sponsoring Institution:\s*(.*?)\n'  
            r'(?:.*\n)*?'
            r'Program name:\s*(.*?)\n'
            r'(?:.*\n)*?'
            r'Specialty:\s*(.*?)\n'
            r'(?:.*\n)*?'
            r'Dates:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})',
            FILE_CONTENT, 
            re.IGNORECASE
        )

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
        FILE_CONTENT = re.sub(r'\r\n|\r', '\n', FILE_CONTENT)
        FILE_CONTENT = re.sub(r'\n+', '\n', FILE_CONTENT)
        BLOCKS = re.split(r'Board Status\s*:\s*', FILE_CONTENT, flags=re.IGNORECASE)

        for BLOCK in BLOCKS[1:]:
            LINES = [line.strip() for line in BLOCK.strip().splitlines() if line.strip()]
            BOARD_NAME = next((line for line in reversed(LINES) if ':' not in line and not line.lower().startswith("board status")), None)
            STATUS_MATCH = re.search(r'(Active|Inactive)', BLOCK, re.IGNORECASE)
            STATUS = STATUS_MATCH.group(1).strip() if STATUS_MATCH else None
            EXP_MATCH = re.search(r'Expiration\s*Date\s*[:\-\s]*([\d]{2}[/\-][\d]{2}[/\-][\d]{4})', BLOCK, re.IGNORECASE)
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
        FILE_CONTENT = re.sub(r'\r\n|\r', '\n', FILE_CONTENT)
        FILE_CONTENT = re.sub(r'\n+', '\n', FILE_CONTENT)
        BOARD_BLOCKS = re.split(r'Certifying\s*board\s*[:\-]?', FILE_CONTENT, flags=re.IGNORECASE)[1:]
        
        for BLOCK in BOARD_BLOCKS:
            BOARD_NAME_MATCH = re.search(r'^(.*?)\n', BLOCK)
            CERT_MATCH = re.search(r'Certificate\s*[:\-]?\s*(.*?)\n', BLOCK, re.IGNORECASE)
            STATUS_MATCH = re.search(r'Duration\s*Status\s*[:\-]?\s*(.*?)\n', BLOCK, re.IGNORECASE)
            EXP_MATCH = re.search(r'(\d{2}/\d{2}/\d{4})', BLOCK)
            
            if BOARD_NAME_MATCH and CERT_MATCH and STATUS_MATCH and EXP_MATCH:
                BOARD_NAME = f"{BOARD_NAME_MATCH.group(1).strip()} - {CERT_MATCH.group(1).strip()}"
                STATUS = STATUS_MATCH.group(1).strip()
                EXPIRATION = EXP_MATCH.group(1).strip()
                ENTRIES.append({
                    "Board Name": BOARD_NAME,
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
        if AMA_EDU_DATA:
            MAIN_AMA_ENTRY = next((e for e in AMA_EDU_DATA if "Institution" in e and e["Institution"]), AMA_EDU_DATA[0])
        else:
            MAIN_AMA_ENTRY = None

        for APP_ENTRY in APPLICATION_EDU_DATA or []:
            if not MAIN_AMA_ENTRY:
                RESULTS["education"].append({
                    "application_entry": APP_ENTRY,
                    "matched_ama_entry": None,
                    "match": False,
                    "explanation": "No AMA education entries available for comparison.",
                    "similarity_score": 0.0
                })
                continue

            PROGRAM_SCORE = EMBEDDING_SIMILARITY(APP_ENTRY.get("Program", ""), MAIN_AMA_ENTRY.get("Program", ""))
            SPECIALTY_SCORE = EMBEDDING_SIMILARITY(APP_ENTRY.get("Specialty", ""), MAIN_AMA_ENTRY.get("Specialty", ""))
            AVERAGE_SCORE = (PROGRAM_SCORE * 0.4) + (SPECIALTY_SCORE * 0.6)
            MATCH_STATUS = AVERAGE_SCORE >= threshold

            RESULTS["education"].append({
                "application_entry": APP_ENTRY,
                "matched_ama_entry": MAIN_AMA_ENTRY,
                "match": MATCH_STATUS,
                "similarity_score": AVERAGE_SCORE,
                "explanation": GENERATE_EXPLANATION(
                    "education",
                    APP_ENTRY,
                    MAIN_AMA_ENTRY,
                    MATCH_STATUS
                )
            })

        # --- BOARDS COMPARISON ---
        for APP_BOARD in APPLICATION_BOARD_DATA or []:
            MATCH_FOUND = False
            EXPLANATION = None

            for AMA_BOARD in AMA_BOARD_DATA or []:
                BOARD_SCORE = EMBEDDING_SIMILARITY(
                    (APP_BOARD.get("Board Name", "") or "").strip().lower(),
                    (AMA_BOARD.get("Board Name", "") or "").strip().lower()
                )
                STATUS_MATCH = (APP_BOARD.get("Status", "") or "").strip().lower() == (AMA_BOARD.get("Status", "") or "").strip().lower()

                APP_DATE_STR = str(APP_BOARD.get("Expiration Date", "")).strip()
                AMA_DATE_STR = str(AMA_BOARD.get("Expiration Date", "")).strip()
                APP_DATE = NORMALIZE_DATE(APP_DATE_STR)
                AMA_DATE = NORMALIZE_DATE(AMA_DATE_STR)
                DATE_MATCH = False
                try:
                    DATE_MATCH = APP_DATE == AMA_DATE
                
                except Exception:
                    DATE_MATCH = False

                if BOARD_SCORE >= threshold and STATUS_MATCH and DATE_MATCH:
                    MATCH_FOUND = True
                    EXPLANATION = GENERATE_EXPLANATION("board", APP_BOARD, AMA_BOARD, True)
                    break
                elif EXPLANATION is None:
                    EXPLANATION = GENERATE_EXPLANATION("board", APP_BOARD, AMA_BOARD, False)

            if EXPLANATION is None:  
                EXPLANATION = "No AMA board entries available for comparison."

            RESULTS["boards"].append({
                "application_entry": APP_BOARD,
                "match": MATCH_FOUND,
                "explanation": EXPLANATION
            })

        return RESULTS

    except Exception as E:
        return {"education": [], "boards": [], "error": str(E)}