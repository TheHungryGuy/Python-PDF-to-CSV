import os
import time
import requests
import pandas as pd
from io import BytesIO, StringIO
from html.parser import HTMLParser

DATALAB_API_URL = "https://www.datalab.to/api/v1/marker"
HEADERS = {"X-API-Key": os.getenv("DATALAB_API_KEY")}


class TableHTMLParser(HTMLParser):
    """Parses an HTML table string into a list of rows (each row is a list of strings)."""
    def __init__(self):
        super().__init__()
        self.rows = []
        self._current_row = None
        self._current_cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._current_row = []
        elif tag in ("td", "th") and self._current_row is not None:
            self._current_cell = ""

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._current_cell is not None:
            self._current_row.append(self._current_cell.strip())
            self._current_cell = None
        elif tag == "tr" and self._current_row is not None:
            if self._current_row:
                self.rows.append(self._current_row)
            self._current_row = None

    def handle_data(self, data):
        if self._current_cell is not None:
            self._current_cell += data


def parse_html_table(html: str) -> pd.DataFrame:
    parser = TableHTMLParser()
    parser.feed(html)
    if not parser.rows:
        return None
    headers = parser.rows[0]
    data = parser.rows[1:]
    return pd.DataFrame(data, columns=headers)


def extract_blocks(node: dict, collected: list):
    """Recursively walk the JSON tree and collect Table blocks."""
    if node.get("block_type") == "Table":
        collected.append(node)
    for child in node.get("children", []):
        extract_blocks(child, collected)


def convert_PDF_to_CSV(file_bytes: bytes, original_filename: str) -> tuple:
    base_filename = os.path.splitext(original_filename)[0]

    # Submit the PDF to the API
    response = requests.post(
        DATALAB_API_URL,
        files={"file": (original_filename, BytesIO(file_bytes), "application/pdf")},
        data={"output_format": "json", "mode": "balanced"},
        headers=HEADERS,
    )
    response.raise_for_status()
    check_url = response.json()["request_check_url"]

    # Poll until complete
    result = None
    for i in range(300):
        poll = requests.get(check_url, headers=HEADERS).json()
        if poll["status"] == "complete":
            result = poll
            break
        elif poll["status"] == "failed":
            raise RuntimeError(f"Datalab conversion failed: {poll.get('error')}")
        time.sleep(2)

    if result is None:
        raise TimeoutError("Datalab API did not complete in time.")

    # find all table blocks from the children tree
    table_blocks = []
    for top_node in result.get("json", {}).get("children", []):
        extract_blocks(top_node, table_blocks)

    if not table_blocks:
        raise ValueError("No tables found in the document.")

    
    dataframes = []
    for block in table_blocks:
        df = parse_html_table(block.get("html", ""))
        if df is not None and not df.empty:
            dataframes.append(df)

    if not dataframes:
        raise ValueError("Tables were found but could not be parsed.")

    combined_frames = []
    for i, df in enumerate(dataframes):
        combined_frames.append(df)
        if i < len(dataframes) - 1:
            combined_frames.append(pd.DataFrame([[""] * df.shape[1]], columns=df.columns))

    combined_df = pd.concat(combined_frames, ignore_index=True)

    csv_buffer = StringIO()
    combined_df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    return csv_data, base_filename