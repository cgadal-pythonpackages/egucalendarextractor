import streamlit as st

from egucalendarextractor.core import extract_events_from_pdf, write_ics

st.title("📅 EGU PDF to Calendar (.ics)")

pdf_file = st.file_uploader("Upload your personal programme PDF", type="pdf")

if pdf_file:
    events = extract_events_from_pdf(pdf_file)
    write_ics(events, "egu_schedule.ics")
    st.success("✅ .ics file created!")
    with open("egu_schedule.ics", "rb") as f:
        st.download_button("📥 Download .ics", f, file_name="egu_schedule.ics")
