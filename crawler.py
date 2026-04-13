import os
import re
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import fitz  # PyMuPDF

BASE_URL = "https://fmuniversity.nic.in/pg_syllabus.html"
PDF_DIR = "pdfs"
OUTPUT_FILE = "dataset.jsonl"

# -----------------------------
# 1. Get all PDF links
# -----------------------------
def get_pdf_links():
    try:
        res = requests.get(BASE_URL, timeout=30)
        soup = BeautifulSoup(res.text, "html.parser")

        links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "getdata" in href and "pdf" in href:
                full_url = urljoin(BASE_URL, href)
                links.add(full_url)

        print(f"Found {len(links)} PDFs")
        return list(links)

    except Exception as e:
        print("Error fetching links:", e)
        return []

# -----------------------------
# 2. Download PDFs
# -----------------------------
def download_pdfs(links):
    os.makedirs(PDF_DIR, exist_ok=True)
    paths = []

    for i, url in enumerate(links):
        file_path = os.path.join(PDF_DIR, f"{i}.pdf")

        try:
            r = requests.get(url, timeout=30)
            with open(file_path, "wb") as f:
                f.write(r.content)

            paths.append(file_path)
            print(f"Downloaded: {file_path}")

        except Exception as e:
            print(f"Failed: {url} -> {e}")

    return paths

# -----------------------------
# 3. Extract text from PDF
# -----------------------------
def extract_text(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""

        for page in doc:
            text += page.get_text()

        return text

    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

# -----------------------------
# 4. Clean text
# -----------------------------
def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# -----------------------------
# 5. Deduplicate using hash
# -----------------------------
def hash_text(text):
    return hashlib.md5(text.encode()).hexdigest()

# -----------------------------
# 6. Build dataset
# -----------------------------
def build_dataset(pdf_paths):
    seen_hashes = set()
    count = 0

    with open(OUTPUT_FILE, "w") as f:
        for path in pdf_paths:
            text = extract_text(path)

            if len(text.strip()) < 100:
                continue

            text = clean_text(text)
            h = hash_text(text)

            if h in seen_hashes:
                continue

            seen_hashes.add(h)

            data = {
                "source": os.path.basename(path),
                "text": text
            }

            f.write(json.dumps(data) + "\n")
            count += 1

    print(f"Dataset created with {count} entries")

# -----------------------------
# MAIN PIPELINE
# -----------------------------
def main():
    links = get_pdf_links()

    if not links:
        print("No links found. Exiting.")
        return

    pdf_paths = download_pdfs(links)

    if not pdf_paths:
        print("No PDFs downloaded. Exiting.")
        return

    build_dataset(pdf_paths)

if __name__ == "__main__":
    main()
