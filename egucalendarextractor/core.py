import os
import re
import uuid
from datetime import datetime
from io import BytesIO

import fitz  # PyMuPDF
import matplotlib.colors as mcolors
import numpy as np

ENCODING_ISSUES_SUBS = {
    "\x01": "ff",
    "\x02": "ff",
    "\x03": "fl",
    "\x04": "fi",
}

CSS4_colors = {
    key: 255 * np.array(mcolors.to_rgb(key)) for key in mcolors.CSS4_COLORS.keys()
}


def extract_links_from_pdf(doc):
    link_map = {}
    for page_num, page in enumerate(doc):
        links = page.get_links()
        text = page.get_text("dict")

        for link in links:
            if "uri" in link.keys():
                if link["uri"]:
                    # Find closest text to the link rectangle
                    rect = link["from"]
                    x0, y0, x1, y1 = rect
                    label = None

                    for block in text["blocks"]:
                        if "lines" not in block:
                            continue
                        for line in block["lines"]:
                            for span in line["spans"]:
                                sx0, sy0, sx1, sy1 = span["bbox"]
                                # Check for overlap with link rect
                                if (
                                    sx0 >= x0 - 2
                                    and sx1 <= x1 + 2
                                    and sy0 >= y0 - 2
                                    and sy1 <= y1 + 2
                                ):
                                    label = span["text"].strip()
                                    break
                            if label:
                                break
                        if label:
                            break

                    if label:
                        link_map[label] = link["uri"]
                        # print(f"🔗 Found link for '{label}': {link['uri']}")

    return link_map


def extract_individual_events(text, link_map):
    events = []
    pattern = re.compile(
        r"(EGU25-\d+).*?\|\s.*?\|\s*(Orals|Posters on site|Posters virtual|PICO).*?\n"
        r"(.*?)\n"
        r"([^\n]+?)\n"
        r"(Mon|Tue|Wed|Thu|Fri), (\d{2} \w{3}), (\d{2}:\d{2})\u2013(\d{2}:\d{2}) \(CEST\).*?\n"
        r" (Room .*?|Hall .*?|vPoster spot .*?)\n",
        re.DOTALL,
    )

    for match in pattern.finditer(text):
        session_id, session_type, title, authors, _, date, start, end, location = (
            match.groups()
        )

        start_dt = datetime.strptime(f"{date} 2025 {start}", "%d %b %Y %H:%M")
        end_dt = datetime.strptime(f"{date} 2025 {end}", "%d %b %Y %H:%M")

        link = link_map.get(
            session_id, f"https://meetingorganizer.copernicus.org/EGU25/{session_id}"
        )
        category = "Poster" if "Poster" in session_type else "Talk"
        description = f"Authors: {authors}\\nSession ID: {session_id}\\nLink: {link}"

        events.append(
            {
                "uid": str(uuid.uuid4()),
                "title": title,
                "start": start_dt,
                "end": end_dt,
                "location": location.strip(),
                "description": description,
                "category": category,
            }
        )

    return events


def extract_session_blocks(text, link_map):
    session_pattern = re.compile(
        r"^([A-Z]{2,4}\d+\.\d+)\n(.*?)\n.*?Convener:.*?(?:\nCo-conveners:.*?)?(.*?)(?=\n[A-Z]{2,4}\d+\.\d+|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    sessions = []
    for match in session_pattern.finditer(text):
        session_id, title, body = match.groups()

        subevent_pattern = re.compile(
            r"(Orals|Posters on site|Posters virtual).*?\|\s*(?:Attendance\s*)?(Mon|Tue|Wed|Thu|Fri), (\d{2} \w{3}), (\d{2}:\d{2})\u2013(\d{2}:\d{2}) \(CEST\).*?\n(.*?)\n",
            re.DOTALL,
        )
        for sub in subevent_pattern.finditer(body):
            sub_type, _, date, start, end, loc = sub.groups()
            start_dt = datetime.strptime(f"{date} 2025 {start}", "%d %b %Y %H:%M")
            end_dt = datetime.strptime(f"{date} 2025 {end}", "%d %b %Y %H:%M")
            link = link_map.get(
                session_id,
                f"https://meetingorganizer.copernicus.org/EGU25/session/{session_id}",
            )
            description = f"Session ID: {session_id}\\nLink: {link}"
            sessions.append(
                {
                    "uid": str(uuid.uuid4()),
                    "title": f"[Session] {session_id} – {sub_type}: {title.strip()}",
                    "start": start_dt,
                    "end": end_dt,
                    "location": loc.strip(),
                    "description": description,
                    "category": "Session",
                }
            )
    return sessions


def parse_fallback_blocks(text):
    fallback_pattern = re.compile(
        r"^(?P<title>[^\n]+)\n"
        r"(?:(?P<organizers>Organized by[^\n]*?(?:\|[^\n]*)?)\n)?"
        r"(?:Location: (?P<location>[^\n]+)\n)?"
        r"[★\s]*"
        r"(?P<start_day>Sun|Mon|Tue|Wed|Thu|Fri|Sat), (?P<start_date>\d{2} \w{3}), (?P<start_time>\d{2}:\d{2})"
        r"(?:–(?:(?P<end_day>Sun|Mon|Tue|Wed|Thu|Fri|Sat), )?"
        r"(?:(?P<end_date>\d{2} \w{3}), )?"
        r"(?P<end_time>\d{2}:\d{2}))? CEST",
        re.MULTILINE,
    )

    events = []
    seen_titles = set()

    for match in fallback_pattern.finditer(text):
        gd = match.groupdict()
        title = gd["title"].strip()

        if title in seen_titles:
            continue
        seen_titles.add(title)

        location = gd.get("location") or "TBD"
        organizers = gd.get("organizers") or ""

        start_dt = datetime.strptime(
            f"{gd['start_date']} 2025 {gd['start_time']}", "%d %b %Y %H:%M"
        )

        if gd["end_date"]:
            end_dt = datetime.strptime(
                f"{gd['end_date']} 2025 {gd['end_time']}", "%d %b %Y %H:%M"
            )
        elif gd["end_time"]:
            end_dt = datetime.strptime(
                f"{gd['start_date']} 2025 {gd['end_time']}", "%d %b %Y %H:%M"
            )
        else:
            end_dt = start_dt

        events.append(
            {
                "uid": str(uuid.uuid4()),
                "title": title,
                "start": start_dt,
                "end": end_dt,
                "location": location.strip(),
                "description": organizers.strip() + "\\nAuto-detected special entry.",
                "category": "Special Event",
            }
        )

    return events


def extract_misc_events(text, link_map):
    misc_events = []
    seen_titles = set()
    ALL_MISC_PREFIXES = set()

    # --- Pattern 1: Standard SC/MAL/GDB-style with ID ---
    standard_pattern = re.compile(
        r"^([A-Z]{2,4}\s?\d+(?:\.\d+)?(?:[A-Z]?)?)\n"  # Event ID
        r"(.*?)\n"  # Title
        r"(.*?(?:Convener:.*?(?:\nCo-conveners?:.*?)?)?)?"  # Optional convener
        r"[★|\s]*\s*(Mon|Tue|Wed|Thu|Fri),\s*(\d{2} \w{3}),\s*(\d{2}:\d{2})–(\d{2}:\d{2}) \(CEST\)\n"
        r"(Room.*?)\n",
        re.DOTALL | re.MULTILINE,
    )

    for match in standard_pattern.finditer(text):
        eid, title, conveners, day, date, start, end, room = match.groups()
        start_dt = datetime.strptime(f"{date} 2025 {start}", "%d %b %Y %H:%M")
        end_dt = datetime.strptime(f"{date} 2025 {end}", "%d %b %Y %H:%M")

        prefix = re.match(r"[A-Z]+", eid.replace(" ", "")).group()
        ALL_MISC_PREFIXES.add(prefix)
        category = {
            "SC": "Short Course",
            "MAL": "Medal & Award Lectures and Celebrations",
            "GDB": "Great Debate",
            "US": "Union Symposia",
            "EOS": "Education and Outreach Sessions",
            "NET": "Networking",
            "FAM": "Feedback and admin meetings",
            "PC": "Press conferences",
        }.get(prefix, "Other")

        clean_id = eid.replace(" ", "")
        link = (
            link_map.get(eid)
            or link_map.get(clean_id)
            or next(
                (v for k, v in link_map.items() if eid in k or clean_id in k),
                f"https://meetingorganizer.copernicus.org/EGU25/{clean_id}",
            )
        )

        description_parts = [f"Event ID: {eid}"]
        if conveners:
            description_parts.append(conveners.strip())
        description_parts.append(f"Link: {link}")
        description = "\\n".join(description_parts)

        misc_events.append(
            {
                "uid": str(uuid.uuid4()),
                "title": f"{eid} – {title.strip()}",
                "start": start_dt,
                "end": end_dt,
                "location": room.strip(),
                "description": description,
                "category": category,
            }
        )

    misc_events += parse_fallback_blocks(text)
    return misc_events


def color_diff(color1, color2):
    color1, color2 = np.array(color1), np.array(color2)
    r = 0.5 * (color1[0] - color2[0])
    delta = color1 - color2
    delta_c = np.sqrt(
        (2 + r / 256) * delta[0] ** 2 + 4 * delta[1] + (2 + (255 - r) / 256 * delta[2])
    )
    return delta_c


def get_colorname(detected_color):
    # find the closest named color
    color_diffs = np.array(
        [[key, color_diff(detected_color, color)] for key, color in CSS4_colors.items()]
    )
    color_name = color_diffs[:, 0][np.argmin(color_diffs[:, 1])]
    return color_name


def extract_room_colors(doc, substring_list=["Room", "Hall", "vPoster spot"]):
    room_colors = {}

    for page_num, page in enumerate(doc):
        shapes = page.get_drawings()
        text_blocks = page.get_text("dict")["blocks"]
        rectangular_shapes = np.array(
            [shape for shape in shapes if (shape["items"][0][0] == "re")]
        )
        rect_shapes_zcenters = np.array(
            [
                0.5 * (shape["rect"][1] + shape["rect"][3])
                for shape in rectangular_shapes
            ]
        )
        # print(f"\n🔍 Page {page_num + 1}")
        # print("Found shapes:", len(shapes))

        for block in text_blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    room_text = span["text"].strip()
                    bbox = span["bbox"]
                    if not any(substring in room_text for substring in substring_list):
                        continue
                    # print(f"🧩 Checking room text: '{room_text}' at {bbox}")
                    text_z_center = 0.5 * (bbox[1] + bbox[3])
                    # find closest shape
                    shape = rectangular_shapes[
                        np.argmin(np.abs(rect_shapes_zcenters - text_z_center))
                    ]
                    # print(shape)
                    color_source = (
                        shape.get("color") or shape.get("fill") or shape.get("stroke")
                    )
                    if color_source is None:
                        continue
                    color_rgb = tuple(int(c * 255) for c in color_source)
                    room_colors[room_text] = color_rgb
                    # print(color_source)
                    # print(f"🎨 Found color block near '{room_text}': {color_rgb}")

    return room_colors


def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def format_event_ics(event):
    dt_fmt = "%Y%m%dT%H%M%S"
    ics = f"""BEGIN:VEVENT
UID:{event["uid"]}
DTSTAMP:{datetime.utcnow().strftime(dt_fmt)}Z
DTSTART;TZID=Europe/Vienna:{event["start"].strftime(dt_fmt)}
DTEND;TZID=Europe/Vienna:{event["end"].strftime(dt_fmt)}
SUMMARY:{event["title"]}
LOCATION:{event["location"]}
DESCRIPTION:{event["description"]}
CATEGORIES:{event["category"]}
"""

    # Optional: add Apple Calendar color if available
    if "color" in event:
        # ics += f"X-APPLE-CALENDAR-COLOR:{event['color']}\n"
        ics += f"COLOR:{event['color']}\n"

    ics += "END:VEVENT"
    return ics


def fix_encoding(text):
    for key, val in ENCODING_ISSUES_SUBS.items():  # fixing some encoding issues
        text = text.replace(key, val)


def write_ics(events, output_path):
    header = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Conference Schedule
X-WR-TIMEZONE:Europe/Vienna
"""
    footer = "END:VCALENDAR"
    content = header + "\n".join(format_event_ics(e) for e in events) + "\n" + footer
    fix_encoding(content)
    with open(output_path, "w") as f:
        f.write(content)
    print(f"✅ ICS file written to: {output_path}")


def deduplicate_sessions(sessions):
    seen = set()
    unique_sessions = []
    for session in sessions:
        session_key = tuple(sorted((k, v) for k, v in session.items() if k != "uid"))
        if session_key not in seen:
            seen.add(session_key)
            unique_sessions.append(session)
    return unique_sessions


def apply_colors(events, room_colors):
    for event in events:
        room = event["location"]
        if room in room_colors:
            # event["color"] = rgb_to_hex(room_colors[room])
            event["color"] = get_colorname(room_colors[room])
        else:
            event["color"] = "#999999"  # fallback grey
    return events


def extract_events_from_pdf(pdf_input):
    if isinstance(pdf_input, BytesIO):
        doc = fitz.open(stream=pdf_input, filetype="pdf")
    elif isinstance(pdf_input, str) and os.path.exists(pdf_input):
        doc = fitz.open(pdf_input)
    else:
        raise ValueError("Input must be a valid file path or a BytesIO object.")
    #
    #
    room_colors = extract_room_colors(doc)
    link_map = extract_links_from_pdf(doc)
    #
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    individual = extract_individual_events(text, link_map)
    sessions = deduplicate_sessions(extract_session_blocks(text, link_map))
    misc = extract_misc_events(text, link_map)
    #
    all_events = apply_colors(individual + sessions + misc, room_colors)
    return all_events


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract conference events from PDF and write to .ics"
    )
    parser.add_argument("pdf_file", help="Path to input PDF")
    parser.add_argument("output_ics", help="Output path for .ics file")
    args = parser.parse_args()

    events = extract_events_from_pdf(args.pdf_file)
    write_ics(events, args.output_ics)
