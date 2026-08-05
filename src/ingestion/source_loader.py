# src/ingestion/source_loader.py
import json
import os
import io
import time
from typing import List, Dict, Tuple

import requests
from pypdf import PdfReader  # standardized on pypdf (requirements.txt already pins this)


class SourceLoader:
    def __init__(self, config_path: str = "config/sources.json"):
        self.config_path = config_path
        self.sources = self._load_sources()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "DNT": "1",
        })

    def _load_sources(self) -> List[Dict]:
        with open(self.config_path, "r") as f:
            return json.load(f)["sources"]

    def fetch_all(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Returns:
            (successes, failures) -- failures is a list of
            {"id": ..., "error": ...} so callers (and your evaluation
            writeup / "known failure cases" note) can report them,
            not just see them scroll by in stdout.
        """
        results = []
        failures = []
        for source in self.sources:
            try:
                text = self.fetch_source(source)
                results.append({
                    "id": source["id"],
                    "type": source["type"],
                    "text": text,
                })
                print(f"[PASS] Successfully fetched: {source['id']}")
            except Exception as e:
                print(f"[WARN] Failed to fetch {source['id']}: {str(e)}")
                failures.append({"id": source["id"], "error": str(e)})
        return results, failures

    def fetch_source(self, source: Dict) -> str:
        if source["type"] == "url":
            return self._fetch_url(source["value"])
        elif source["type"] == "pdf":
            return self._fetch_pdf(source["value"])
        else:
            raise ValueError(f"Unsupported source type: {source['type']}")

    def _fetch_url(self, url: str, max_retries: int = 3) -> str:
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                if "text/html" in response.headers.get("Content-Type", ""):
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, "html.parser")
                    for element in soup(["script", "style", "nav", "footer", "head", "iframe"]):
                        element.decompose()
                    return soup.get_text(separator="\n", strip=True)
                else:
                    return response.text

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to fetch URL {url} after {max_retries} attempts: {str(e)}")
                time.sleep(2 ** attempt)

    def _fetch_pdf(self, pdf_path: str) -> str:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        with open(pdf_path, "rb") as f:
            pdf_reader = PdfReader(io.BytesIO(f.read()))
            text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
            if not text.strip():
                raise ValueError(f"No text extracted from PDF: {pdf_path}")
            return text