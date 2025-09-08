import pdfplumber
import pandas as pd
import re
from io import BytesIO, StringIO
import os

# Regex rules
single_letter = re.compile(r"^[A-Za-z]$")
single_letter_inside = re.compile(r"\b[A-Za-z]\b")
date_year_month = re.compile(r"^(\d{4}-\d{2}-)")
date_day = re.compile(r"^\d{2}")
reference_pattern = re.compile(r"[A-Za-z]{2,5}\d+")
amount_pattern = re.compile(r"[+-]\$[\d,]+\.\d{2}")
balance_pattern = re.compile(r"\$[\d,]+\.\d{2}")
file_name_pattern = re.compile(r"([^/\\]+)(?=\.[^.]+$)")

def convert_PDF_to_CSV(file_bytes: bytes, original_filename: str) -> tuple:
    """Converts PDF bytes to CSV string and returns both the data and base filename"""
    
    # Extract base filename without extension
    base_filename = os.path.splitext(original_filename)[0]
    
    pdf_text = []

    # Use BytesIO to create a file-like object from bytes
    with BytesIO(file_bytes) as pdf_file:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_text.extend(text.splitlines())

    cleaned_text = []
    for line in pdf_text:
        new_line = single_letter_inside.sub("", line).strip()
        if new_line:
            cleaned_text.append(new_line)
    pdf_text = cleaned_text

    df = pd.DataFrame(columns=["Date", "Description", "Reference", "Amount", "Balance"])

    Date = ""
    Description = ""
    Reference = ""
    Amount = ""
    Balance = ""

    start_processing = False

    for line in pdf_text:
        # check if we've reached the marker line
        if not start_processing:
            if "transaction history" in line.lower():
                start_processing = True
            continue  # skip until found
        date_match = date_year_month.match(line)
        if date_match:
            Date = date_match.group()
            line = date_year_month.sub("", line).strip()
            Description = line

        ref_match = reference_pattern.search(line)
        if ref_match:
            Reference = ref_match.group()
            line = reference_pattern.sub("", line).strip()
        amt_match = amount_pattern.search(line)
        if amt_match:
            Amount = amt_match.group()
            line = amount_pattern.sub("", line).strip()
        bal_match = balance_pattern.search(line)
        if bal_match:
            Balance = bal_match.group()
            line = balance_pattern.sub("", line).strip()
            if line:
                Description = line
        day_match = date_day.search(line)
        if day_match:
            Date += day_match.group()
            line = date_day.sub("", line)
            Description += line

            # All the Data from the transaction should be grabbed so add to df
            row = {
                "Date": Date,
                "Description": Description,
                "Reference": Reference,
                "Amount": Amount,
                "Balance": Balance,
            }
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    # Data cleaning
    df["Amount"] = pd.to_numeric(
        df["Amount"].str.replace(r"[,$]", "", regex=True), errors="coerce"
    )
    df["Balance"] = pd.to_numeric(
        df["Balance"].str.replace(r"[,$]", "", regex=True), errors="coerce"
    )
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Convert DataFrame to CSV string in memory
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    return csv_data, base_filename