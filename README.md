# EGU Calendar Extractor

A tool to extract events from EGU-style personal programme PDFs and convert them into `.ics` calendar files that can be added in your favorite calendar app. To download your personal program, got to [https://meetingorganizer.copernicus.org/EGU25/personal_programme](https://meetingorganizer.copernicus.org/EGU25/personal_programme), log in and click on the *Print* blue button after having selected events.

## 🔧 Features
- Parses individual talks, sessions, and miscellaneous events (e.g. short courses)
- Detects corresponding EGU website links and them to the event description (*This works systematically for session blocks and individual poster or orals, but it sometimes does not work for other event types, such as the EGU Scavenger Hunt.*)
- Outputs a `.ics` file with room-based or category-based color coding (only works when the .ics file is loaded in iCalendar (Apple), and not all the time...)


## 🚀 Usage

### [Preferred/All] Option 1: Download the repository and use the webapp locally

If you have python installed on your computer, you can simply download the git repository, and install all the required python packages (see `requirements.txt`). Then, simply run the script `streamlit_app.py` and it should open a wepapp locally on your web browser.


### [Preferred/All] Option 2: Copy `core.py` into your notebook or script

If you have python installed on your computer, you simply copy the file `egucalendarextractor/core.py` where your PDF file is, and then run as python script:

```python
from egucalendarextractor.core import extract_events_from_pdf, write_ics
events = extract_events_from_pdf("input.pdf")
write_ics(events, "output.ics")
```

You will need the python packages: pymupdf, matplotlib and numpy

### [Preferred/Linux] Option 3: Copy `core.py` into your notebook or script

Under linux (and maybe mac?), you simply copy the file `egucalendarextractor/core.py` where your PDF file is, and then run in the terminal:

```bash
python core.py file.pdf EGU25_schedule.ics
```
You will need the python packages: pymupdf, matplotlib and numpy

### [Only if necessary] Option 4: Use with the webapp

I have hosted the code on the Streamlit Community Cloud [here](https://egucalendarextractor.streamlit.app/), which is free but **will not hold if there are too many simultaneous users**. Please, only uses this if you do not have any access to python.


<!-- ### Option 2: As a CLI tool

```bash
python egucalendarextractor/core.py input.pdf output.ics
``` -->

## 🪪 License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0](https://creativecommons.org/licenses/by-nc/4.0/) license.

📬 For commercial use, please contact the author.
