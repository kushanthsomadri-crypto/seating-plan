# extract_pdf_to_csv.py
# Simple PDF → CSV extractor for seating tables.
# It asks you for the PDF path so you don't have to move files.
import pdfplumber
import pandas as pd
import os
import re

print("Extractor — will create seating.csv in the current folder.")
default = "seating.pdf"
p = input(f"Press Enter to use './{default}' OR paste the full path to your PDF and press Enter: ").strip()
if p == "":
    pdf_path = default
else:
    pdf_path = p

if not os.path.exists(pdf_path):
    print("File not found:", pdf_path)
    print("Make sure you typed the correct path, or move the PDF into this project folder and name it 'seating.pdf'")
    raise SystemExit(1)

out_csv = "seating.csv"

def clean_cell(c):
    if c is None:
        return ""
    return str(c).strip()

rows = []

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        tables = page.extract_tables()
        if not tables:
            continue
        for table in tables:
            for r in table:
                # normalize row cells
                cells = [clean_cell(c) for c in r]
                if len(cells) >= 3:
                    # heuristic: first column seat number (digits), second enrol, third name
                    if re.search(r"\d", cells[0]) and len(cells[1]) >= 4:
                        rows.append({
                            "room": "",
                            "seat_no": cells[0],
                            "enrolment_no": cells[1],
                            "student_name": " ".join(cells[2:]).strip()
                        })
                else:
                    # fallback: try to find enrolment pattern in joined row
                    joined = " ".join(cells)
                    m = re.search(r"([A-Za-z]{1,}\d{3,})", joined)
                    if m:
                        enrol = m.group(1)
                        # first number as seat
                        ms = re.search(r"\b(\d{1,3})\b", joined)
                        seat = ms.group(1) if ms else ""
                        name = joined.replace(enrol, "").replace(seat, "").strip(" |-,:")
                        rows.append({"room": "", "seat_no": seat, "enrolment_no": enrol, "student_name": name})

# Save results
df = pd.DataFrame(rows, columns=["room","seat_no","enrolment_no","student_name"])
if df.empty:
    print("No rows found. The PDF layout might need a custom extractor. Tell me and I'll adjust.")
else:
    df.to_csv(out_csv, index=False)
    print(f"Wrote {len(df)} rows to {out_csv}")
    print("Open seating.csv in VS Code or Excel to check/fix room codes and names if needed.")
