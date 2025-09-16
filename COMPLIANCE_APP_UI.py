import streamlit as st
import tempfile
import base64
from PIL import Image

from COMPLIANCE_HELPER_FUNCTIONS import (
    EXTRACT_TEXT_FROM_FILE,
    EXTRACT_EDUCATION_COMPLIANCE_APPLICATION,
    EXTRACT_EDUCATION_AMA_PROFILE,
    EXTRACT_BOARDS_COMPLIANCE_APPLICATION,
    EXTRACT_BOARDS_AMA_PROFILE,
    COMPARE_INFORMATION,
)

# Compliance UI page config
st.set_page_config(page_title="Compliance Watchdog Verification", layout="centered")

# Custom CSS for background and styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            radial-gradient(circle at 25% 25%, rgba(255,255,255,0.1) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(255,255,255,0.05) 0%, transparent 50%),
            linear-gradient(45deg, transparent 49%, rgba(255,255,255,0.02) 50%, transparent 51%);
        background-size: 200px 200px, 300px 300px, 50px 50px;
        pointer-events: none;
        z-index: 0;
    }
    
    /* Realistic Stethoscope SVG decorations */
    .stApp::after {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 400'%3E%3C!-- Left earpiece --%3E%3Cellipse cx='80' cy='40' rx='12' ry='8' fill='rgba(220,220,220,0.9)' stroke='rgba(180,180,180,0.9)' stroke-width='2'/%3E%3C!-- Right earpiece --%3E%3Cellipse cx='220' cy='40' rx='12' ry='8' fill='rgba(220,220,220,0.9)' stroke='rgba(180,180,180,0.9)' stroke-width='2'/%3E%3C!-- Left earpiece tube --%3E%3Cpath d='M80 48 Q85 60 90 80 L90 120' stroke='rgba(100,100,100,0.8)' stroke-width='4' fill='none'/%3E%3C!-- Right earpiece tube --%3E%3Cpath d='M220 48 Q215 60 210 80 L210 120' stroke='rgba(100,100,100,0.8)' stroke-width='4' fill='none'/%3E%3C!-- Main tubing connection --%3E%3Cpath d='M90 120 Q120 130 150 130 Q180 130 210 120' stroke='rgba(100,100,100,0.8)' stroke-width='5' fill='none'/%3E%3C!-- Main tube down --%3E%3Cpath d='M150 130 L150 280' stroke='rgba(100,100,100,0.8)' stroke-width='5' fill='none'/%3E%3C!-- Chest piece bell --%3E%3Ccircle cx='150' cy='300' r='20' fill='rgba(200,200,200,0.9)' stroke='rgba(150,150,150,0.9)' stroke-width='3'/%3E%3C!-- Inner diaphragm --%3E%3Ccircle cx='150' cy='300' r='15' fill='rgba(240,240,240,0.8)' stroke='rgba(180,180,180,0.8)' stroke-width='1'/%3E%3C!-- Center detail --%3E%3Ccircle cx='150' cy='300' r='8' fill='rgba(160,160,160,0.7)'/%3E%3C/svg%3E"),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 400'%3E%3C!-- Left earpiece --%3E%3Cellipse cx='80' cy='40' rx='12' ry='8' fill='rgba(220,220,220,0.9)' stroke='rgba(180,180,180,0.9)' stroke-width='2'/%3E%3C!-- Right earpiece --%3E%3Cellipse cx='220' cy='40' rx='12' ry='8' fill='rgba(220,220,220,0.9)' stroke='rgba(180,180,180,0.9)' stroke-width='2'/%3E%3C!-- Left earpiece tube --%3E%3Cpath d='M80 48 Q85 60 90 80 L90 120' stroke='rgba(100,100,100,0.8)' stroke-width='4' fill='none'/%3E%3C!-- Right earpiece tube --%3E%3Cpath d='M220 48 Q215 60 210 80 L210 120' stroke='rgba(100,100,100,0.8)' stroke-width='4' fill='none'/%3E%3C!-- Main tubing connection --%3E%3Cpath d='M90 120 Q120 130 150 130 Q180 130 210 120' stroke='rgba(100,100,100,0.8)' stroke-width='5' fill='none'/%3E%3C!-- Main tube down --%3E%3Cpath d='M150 130 L150 280' stroke='rgba(100,100,100,0.8)' stroke-width='5' fill='none'/%3E%3C!-- Chest piece bell --%3E%3Ccircle cx='150' cy='300' r='20' fill='rgba(200,200,200,0.9)' stroke='rgba(150,150,150,0.9)' stroke-width='3'/%3E%3C!-- Inner diaphragm --%3E%3Ccircle cx='150' cy='300' r='15' fill='rgba(240,240,240,0.8)' stroke='rgba(180,180,180,0.8)' stroke-width='1'/%3E%3C!-- Center detail --%3E%3Ccircle cx='150' cy='300' r='8' fill='rgba(160,160,160,0.7)'/%3E%3C/svg%3E");
        background-position: 
            -5% center, 
            105% center;
        background-size: 400px 500px, 400px 500px;
        background-repeat: no-repeat;
        pointer-events: none;
        z-index: 0;
        opacity: 0.8;
    }
    
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        z-index: 1;
    }
    
    .sidebar .sidebar-content {
        background: rgba(248, 249, 250, 0.95);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Header styling */
    h1 {
        color: #2c3e50;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    h2, h3 {
        color: #34495e;
    }
    
    /* File uploader styling */
    .stFileUploader > div > div {
        background: rgba(240, 248, 255, 0.8);
        border: 2px dashed #4a90e2;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #4a90e2, #357abd);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(74, 144, 226, 0.4);
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background: rgba(212, 237, 218, 0.9);
        border-left: 4px solid #28a745;
        border-radius: 8px;
    }
    
    .stError {
        background: rgba(248, 215, 218, 0.9);
        border-left: 4px solid #dc3545;
        border-radius: 8px;
    }
    
    .stWarning {
        background: rgba(255, 243, 205, 0.9);
        border-left: 4px solid #ffc107;
        border-radius: 8px;
    }
    
    .stInfo {
        background: rgba(209, 236, 241, 0.9);
        border-left: 4px solid #17a2b8;
        border-radius: 8px;
    }
    
    /* Spinner styling */
    .stSpinner {
        text-align: center;
    }
    
    /* Radio button styling */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.7);
        padding: 0.5rem;
        border-radius: 8px;
    }
    
    /* Make sure logo and text remain visible */
    .stMarkdown {
        position: relative;
        z-index: 2;
    }
</style>
""", unsafe_allow_html=True)

COL1, COL2 = st.columns([2, 10])

with open("Compliance Watchdog Logo.png", "rb") as img_file:
    LOGO_BASE64 = base64.b64encode(img_file.read()).decode()

with COL1:
    st.markdown(
        f"""
        <div style="margin-top: 30px;">
            <img src="data:image/png;base64,{LOGO_BASE64}" style="width: 120px;">
        </div>
        """,
        unsafe_allow_html=True
    )

with COL2:
    st.title("🩺 Medical Compliance Checker")

with st.sidebar:
    st.header("Navigation")

    # Radio menu for instructions and external portals
    NAV_SELECTION = st.radio(
        "Select an action:",
        (
            "ℹ️ About / Instructions",
            "🌐 Open Compliance Application Portal",
            "🌐 Lookup AMA Profile Online",
        )
    )

    if NAV_SELECTION == "ℹ️ About / Instructions":
        st.subheader("📖 About The Medical Compliance Checker")
        st.markdown(
            """
            The **Medical Compliance Checker** helps verify whether the information in your
            medical compliance application matches the records in your AMA profile.

            ### ✅ How to Use:
            1. **Upload your documents**  
               - Upload the **Compliance Application** (image, PDF, DOCX, or TXT).  
               - Upload the **AMA Profile** (image, PDF, DOCX, or TXT).  

            2. **Click 'Verify Documents'**  
               - The app will extract text using OCR if needed.  
               - It will parse **Education** and **Board Certification** sections.  

            3. **View Results**  
               - Each entry is compared with AMA data.  
               - Matches are confirmed with ✅.  
               - Discrepancies are flagged with ❌ along with explanations.  

            ### 🔍 What to Expect:
            - **OCR is used** for images/PDFs, so quality of scan may affect accuracy.  
            - **LLM explanations** provide concise reasoning for discrepancies.  
            - Both **Education** and **Board Certifications** are checked separately.  

            ### ⚠️ Notes:
            - Make sure uploaded files are **clear and readable**.  
            - Some unmatched results may require **manual review**.  
            """
        )

    elif NAV_SELECTION == "🌐 Open Compliance Application Portal":
        st.markdown(
            '[Click here to open Compliance Watchdog](https://app.compliancewatchdog.com/)',
            unsafe_allow_html=True
        )

    elif NAV_SELECTION == "🌐 Lookup AMA Profile Online":
        st.markdown(
            '[Click here to open AMA profile lookup](https://www.ama-assn.org/member-center/ama-physician-masterfile)',
            unsafe_allow_html=True
        )

    if st.button("🚪 Exit Application 🚪"):
        st.warning("Medical Compliance Checker Closed")
        st.stop()

# Upload Files
st.subheader("Upload Documents")
COMPLIANCE_APPLICATION_FILE = st.file_uploader(
    "Upload Compliance Application", type=["png", "jpg", "jpeg", "pdf", "txt", "docx"]
)
AMA_PROFILE_FILE = st.file_uploader(
    "Upload AMA Profile", type=["png", "jpg", "jpeg", "pdf", "txt", "docx"]
)

# Button to trigger verification proccess
if st.button("✅ Verify Documents ✅"):
    if COMPLIANCE_APPLICATION_FILE is None or AMA_PROFILE_FILE is None:
        st.warning("Please upload both files.")
    else:
        with st.spinner("Analyzing Sources..."):
            def SAVE_UPLOADED_FILE(UPLOADED_FILE, SUFFIX):
                with tempfile.NamedTemporaryFile(delete=False, suffix=SUFFIX) as tmp:
                    tmp.write(UPLOADED_FILE.read())
                    return tmp.name

            EXT_MAP = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "application/pdf": ".pdf",
                "text/plain": ".txt",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx"
            }

            COMPLIANCE_SUFFIX = EXT_MAP.get(COMPLIANCE_APPLICATION_FILE.type, "")
            AMA_SUFFIX = EXT_MAP.get(AMA_PROFILE_FILE.type, "")

            COMPLIANCE_PATH = SAVE_UPLOADED_FILE(COMPLIANCE_APPLICATION_FILE, COMPLIANCE_SUFFIX)
            AMA_PATH = SAVE_UPLOADED_FILE(AMA_PROFILE_FILE, AMA_SUFFIX)

            COMPLIANCE_TEXT = EXTRACT_TEXT_FROM_FILE(COMPLIANCE_PATH)
            AMA_TEXT = EXTRACT_TEXT_FROM_FILE(AMA_PATH)

            COMPLIANCE_EDUCATION_ENTRIES = EXTRACT_EDUCATION_COMPLIANCE_APPLICATION(COMPLIANCE_TEXT)
            AMA_EDUCATION_ENTRIES = EXTRACT_EDUCATION_AMA_PROFILE(AMA_TEXT)

            COMPLIANCE_BOARD_ENTRIES = EXTRACT_BOARDS_COMPLIANCE_APPLICATION(COMPLIANCE_TEXT)
            AMA_BOARD_ENTRIES = EXTRACT_BOARDS_AMA_PROFILE(AMA_TEXT)

            MATCHES = COMPARE_INFORMATION(COMPLIANCE_EDUCATION_ENTRIES, AMA_EDUCATION_ENTRIES, COMPLIANCE_BOARD_ENTRIES, AMA_BOARD_ENTRIES)

            if not COMPLIANCE_EDUCATION_ENTRIES:
                st.error("No education entries found in the compliance application.")
            elif not AMA_EDUCATION_ENTRIES:
                st.error("No education entries found in the AMA profile.")
            else:
                st.success("Comparison Complete ✅")
                st.subheader("🎓 Education Verification 🎓")

                for IDX, RESULT in enumerate(MATCHES["education"], 1):
                    APP_ENTRY = RESULT["application_entry"]
                    AMA_ENTRY = RESULT.get("matched_ama_entry", {})

                    st.markdown(f"### 🎓 Entry #{IDX} - Education Verification")

                    st.markdown("**Compliance Application Entry:**")
                    st.markdown(f"- Program: {APP_ENTRY['Program']}")
                    st.markdown(f"- Specialty: {APP_ENTRY['Specialty']}")
                    st.markdown(f"- Start Date: {APP_ENTRY['Start Date']}")
                    st.markdown(f"- End Date: {APP_ENTRY['End Date']}")

                    st.markdown("**AMA Profile Entry:**")
                    if AMA_ENTRY:
                        st.markdown(f"- Institution: {AMA_ENTRY.get('Institution', '')}")
                        st.markdown(f"- Program: {AMA_ENTRY.get('Program', '')}")
                        st.markdown(f"- Specialty: {AMA_ENTRY.get('Specialty', '')}")
                        st.markdown(f"- Start Date: {AMA_ENTRY.get('Start Date', '')}")
                        st.markdown(f"- End Date: {AMA_ENTRY.get('End Date', '')}")
                    else:
                        st.markdown("- No AMA entry found")

                    if RESULT["match"]:
                        st.success("✅ Match found")
                        st.info(f"ℹ️ Explanation: {RESULT.get('explanation', 'Exact match found.')}")
                    else:
                        st.error("❌ No match found")
                        st.warning(f"⚠️ Explanation: {RESULT.get('explanation', 'Application entry did not match any AMA entry.')}")

            if MATCHES["boards"]:
                st.subheader("📋 Board Certification Verification 📋")
                for IDX, BOARD_RESULT in enumerate(MATCHES["boards"], 1):
                    BOARD_ENTRY = BOARD_RESULT["application_entry"]

                    st.markdown(f"### 🧾 Board Entry #{IDX}")
                    st.markdown(f"**Board Name:** {BOARD_ENTRY['Board Name']}")
                    st.markdown(f"**Status:** {BOARD_ENTRY['Status']}")
                    st.markdown(f"**Expiration Dates:** {BOARD_ENTRY['Expiration Date']}")

                    if BOARD_RESULT["match"]:
                        st.success("✅ Board match found in AMA profile")
                        st.info(f"ℹ️ Explanation: {BOARD_RESULT.get('explanation', 'Board entry matches AMA profile exactly.')}")
                    else:
                        st.error("❌ No matching board certification found")
                        st.warning(f"⚠️ Explanation: {BOARD_RESULT.get('explanation', 'No matching board entry in AMA profile.')}")