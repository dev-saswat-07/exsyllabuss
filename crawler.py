import os
import re
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import fitz

BASE_URL = "https://fmuniversity.nic.in/pg_syllabus.html"
PDF_DIR = "pdfs"
OUTPUT_FILE = "dataset.jsonl"

def get_pdf_links():
    res = requests.get(BASE_URL, timeout=30)
    soup = BeautifulSoup(res.text, "html.parser")

    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "getdata" in href and "pdf" in href:
            links.add(urljoin(BASE_URL, href))

    return list(links)

def download_pdfs(links):
    os.makedirs(PDF_DIR, exist_ok=True)
    paths = []

    for i, url in enumerate(links):
        path = os.path.join(PDF_DIR, f"{i}.pdf")
        try:
            r = requests.get(url, timeout=30)
            with open(path, "wb") as f:
                f.write(r.content)
            paths.append(path)
        except:
            pass

    return paths

def extract_text(path):
    try:
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except:
        return ""

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def hash_text(text):
    return hashlib.md5(text.encode()).hexdigest()

def build_dataset(paths):
    seen = set()

    with open(OUTPUT_FILE, "w") as f:
        for path in paths:
            text = extract_text(path)

            if len(text) < 100:
                continue

            text = clean(text)
            h = hash_text(text)

            if h in seen:
                continue
            seen.add(h)

            f.write(json.dumps({"text": text}) + "\n")

def main():
    links = get_pdf_links()
    paths = download_pdfs(links)
    build_dataset(paths)

if __name__ == "__main__":
    main()
