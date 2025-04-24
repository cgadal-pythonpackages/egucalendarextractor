import streamlit as st

from egucalendarextractor.core import extract_events_from_pdf, write_ics

st.title("📅 EGU PDF to Calendar (.ics)")

st.markdown(
    "This app will convert your personal programme PDF file from the EGU website to an .ics file that can be loaded by your favorite calendar app (Google calendar, etc ...)."
)

st.markdown(
    "To download your personnal programme PDF file, got to [https://meetingorganizer.copernicus.org/EGU25/personal_programme](https://meetingorganizer.copernicus.org/EGU25/personal_programme), log in and click on the Print blue button after having selected events."
)

pdf_file = st.file_uploader(
    " ",
    type="pdf",
)

if pdf_file:
    events = extract_events_from_pdf(pdf_file)
    write_ics(events, "egu_schedule.ics")
    st.success("✅ .ics file created!")
    with open("egu_schedule.ics", "rb") as f:
        st.markdown(
            "I suggest **importing this file into a newly created agenda in your calendar app**. This will make it easier to delete everything at once if needed, rather than deleting events one by one :)"
        )
        st.download_button("📥 Download .ics", f, file_name="egu_schedule.ics")
