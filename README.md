# EGU Calendar Extractor

A tool to extract events from EGU-style personal programme PDFs and convert them into `.ics` calendar files.

## 🔧 Features
- Parses individual talks, sessions, and miscellaneous events (e.g. short courses)
- Detects embedded hyperlinks from the PDF
- Matches room names to color-coded square blocks
- Outputs a `.ics` file with room-based or category-based color coding
- CLI and Streamlit support

## 🚀 Usage

### [Preferred/All] Option 1: Copy `core.py` into your notebook or script

If you have python installed on your computer, you simply copy the file `egucalendarextractor/core.py` where your PDF file is, and then run

```python
from egucalendarextractor.core import extract_events_from_pdf, write_ics
events = extract_events_from_pdf("input.pdf")
write_ics(events, "output.ics")
```

### [Preferred/Linux] Option 1: Copy `core.py` into your notebook or script

Under linux (and maybe mac?), you simply copy the file `egucalendarextractor/core.py` where your PDF file is, and then run

```bash
python core.py file.pdf EGU25_schedule.ics
```

<!-- ### Option 2: As a CLI tool

```bash
python egucalendarextractor/core.py input.pdf output.ics
``` -->

### [Only if necessary] Option 3: Use with the webapp

I have hosted the code on the Streamlit Community Cloud [here](), which is free but **will not hold if there are too many simultaneous users**. Only uses this if you do not have any access to python.

## 🪪 License

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0](https://creativecommons.org/licenses/by-nc/4.0/) license.

📬 For commercial use, please contact the author.
