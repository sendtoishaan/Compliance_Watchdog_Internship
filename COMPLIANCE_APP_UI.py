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

                    st.markdown(f"### 🎓 Entry #{IDX}")
                    st.markdown(f"**Program:** {APP_ENTRY['Program']}")
                    st.markdown(f"**Specialty:** {APP_ENTRY['Specialty']}")
                    st.markdown(f"**Start Date:** {APP_ENTRY['Start Date']}")
                    st.markdown(f"**End Date:** {APP_ENTRY['End Date']}")

                    if RESULT["match"]:
                        st.success("✅ Match found in AMA profile")
                        st.info(f"ℹ️ Explanation: {RESULT.get('explanation', 'Exact match found.')}")
                    else:
                        st.error("❌ No matching AMA record found")
                        st.warning(f"⚠️ Explanation: {RESULT.get('explanation', 'No entry in AMA profile matches this program.')}")

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