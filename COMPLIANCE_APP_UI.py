import streamlit as st
import tempfile

from COMPLIANCE_HELPER_FUNCTIONS import (
    OCR_IMAGE,
    OCR_PDF,
    EXTRACT_EDUCATION_COMPLAINCE_APPLICATION,
    EXTRACT_EDUCATION_AMA_PROFILE,
    COMPARE_INFORMATION,
)

st.set_page_config(page_title="Compliance Watchdog Verification", layout="centered")

st.title("🩺 Medical Compliance Checker")

# Upload Files
st.subheader("Upload Documents")
COMPLIANCE_APPLICATION_IMAGE = st.file_uploader("Upload Compliance Application (Image)", type=["png", "jpg", "jpeg"])
AMA_PROFILE_PDF = st.file_uploader("Upload AMA Profile (PDF)", type=["pdf"])

# Verify Button verifies the information from both sources
if st.button("✅ Verify Documents ✅"):
    if COMPLIANCE_APPLICATION_IMAGE is None or AMA_PROFILE_PDF is None:
        st.warning("Please upload both files.")
    else:
        with st.spinner("Analyzing Sources..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as TEMP_IMG_FILE:
                TEMP_IMG_FILE.write(COMPLIANCE_APPLICATION_IMAGE.read())
                TEMP_IMAGE_PATH = TEMP_IMG_FILE.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as TEMP_PDF_FILE:
                TEMP_PDF_FILE.write(AMA_PROFILE_PDF.read())
                TEMP_PDF_PATH = TEMP_PDF_FILE.name

            COMPLIANCE_APPLICATION_TEXT = OCR_IMAGE(TEMP_IMAGE_PATH)
            AMA_PROFILE_TEXT = OCR_PDF(TEMP_PDF_PATH)

            COMPLIANCE_APPLICATION_ENTRIES = EXTRACT_EDUCATION_COMPLAINCE_APPLICATION(COMPLIANCE_APPLICATION_TEXT)
            AMA_PROFILE_ENTRIES = EXTRACT_EDUCATION_AMA_PROFILE(AMA_PROFILE_TEXT)

            VERIFICATION_MATCHES = COMPARE_INFORMATION(COMPLIANCE_APPLICATION_ENTRIES, AMA_PROFILE_ENTRIES)

            if not COMPLIANCE_APPLICATION_ENTRIES:
                st.error("No education entries found in the compliance application.")
            elif not AMA_PROFILE_ENTRIES:
                st.error("No education entries found in the AMA profile.")
            else:
                st.success("Comparison Complete ✅")
                
                for i, result in enumerate(VERIFICATION_MATCHES, 1):
                    COMPLIANCE_APPLICATION = result['application_entry']
                    AMA_PROFILE = result['matched_ama_entry']

                    st.markdown(f"### 🎓 Entry #{i}")
                    st.markdown(f"**Program:** {COMPLIANCE_APPLICATION['Program']}")
                    st.markdown(f"**Specialty:** {COMPLIANCE_APPLICATION['Specialty']}")
                    st.markdown(f"**Start Date:** {COMPLIANCE_APPLICATION['Start Date']}")
                    st.markdown(f"**End Date:** {COMPLIANCE_APPLICATION['End Date']}")

                    if result['match']:
                        st.success("✅ Match found in AMA profile")
                    else:
                        st.error("❌ No matching AMA record found")