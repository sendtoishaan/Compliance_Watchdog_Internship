from COMPLIANCE_HELPER_FUNCTIONS import OCR_IMAGE, OCR_PDF, EXTRACT_EDUCATION_COMPLIANCE_APPLICATION, EXTRACT_EDUCATION_AMA_PROFILE, COMPARE_INFORMATION


# Runs the verification proccess between the compliance application and the AMA profile 
def RUN_VERIFICATION(COMPLIANCE_APPLICATION_PATH, AMA_PROFILE_PATH):
    print("🔍 Extracting compliance application...")
    COMPLIANCE_APPLICATION_TEXT = OCR_IMAGE(COMPLIANCE_APPLICATION_PATH)
    
    COMPLIANCE_APPLICATION_ENTRIES = EXTRACT_EDUCATION_COMPLIANCE_APPLICATION(COMPLIANCE_APPLICATION_TEXT)

    print("🔍 Extracting AMA profile...")
    AMA_PROFILE_TEXT = OCR_PDF(AMA_PROFILE_PATH)
    AMA_PROFILE_ENTRIES = EXTRACT_EDUCATION_AMA_PROFILE(AMA_PROFILE_TEXT)

    print("\n🔎 Comparing entries...\n")
    MATCHES = COMPARE_INFORMATION(COMPLIANCE_APPLICATION_ENTRIES, AMA_PROFILE_ENTRIES)

    for i, result in enumerate(MATCHES, 1):
        print(f"📚 Entry #{i}")
        print(f"📝 Application: {result['application_entry']}")
        print(f"🎓 AMA Match: {result['matched_ama_entry']}")
        print(f"✅ Match: {'Yes' if result['match'] else 'No'} (Score: {result['similarity_score']:.1f})")
        print("-" * 60)


# ----------------------- MAIN PROGRAM ---------------------- #
RUN_VERIFICATION(COMPLIANCE_APPLICATION_PATH="/Users/ishaanvenkat/Downloads/image.png", AMA_PROFILE_PATH="/Users/ishaanvenkat/Downloads/doc1752269504538 (1).pdf")
