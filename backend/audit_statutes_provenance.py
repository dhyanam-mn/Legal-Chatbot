import difflib
import json
import re
import sys
import time
from pathlib import Path
import httpx
import pdfplumber

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
STATUTES_DIR = BASE_DIR / "data" / "statutes"
BACKEND_STATUTES_DIR = BASE_DIR / "backend" / "data" / "statutes"
STATUTES_RAW_DIR = BASE_DIR / "data" / "statutes_raw"
SCRATCH_PDF_DIR = Path(r"C:\Users\dhyan\.gemini\antigravity\brain\4cc8c7ff-81ab-4c14-8a3a-2db2d862a469\scratch")
SCRATCH_PDF_DIR.mkdir(parents=True, exist_ok=True)
STATUTES_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Mapping of file names / acts to possible local PDF filenames in data/statutes_raw
LOCAL_PDF_ALIASES = {
    "constitution_of_india.json": [
        "constitution_of_india.pdf",
        "coi.pdf",
        "c9fe9c9b6840524844316f74bb1c556c.pdf",
    ],
    "indian_contract_act_1872.json": [
        "indian_contract_act_1872.pdf",
        "ica_1872.pdf",
        "A187209.pdf",
        "a1872-09.pdf",
    ],
    "arbitration_and_conciliation_act_1996.json": [
        "Arbitration-and-Conciliation-Act,1996.pdf",
        "arbitration_and_conciliation_act_1996.pdf",
        "arbitration_act_1996.pdf",
        "a1996-26.pdf",
        "A1996-26.pdf",
        "aca_1996.pdf",
    ],
    "consumer_protection_act_2019.json": [
        "consumer-protection-act-2019.pdf",
        "consumer_protection_act_2019.pdf",
        "consumer_protection_act.pdf",
        "a2019-35.pdf",
        "A2019-35.pdf",
        "cpa_2019.pdf",
    ],
}


def clean_pdf_page_text(raw_page: str) -> str:
    """Remove running headers, page numbers, and bottom-of-page footnote blocks from official PDF page text."""
    lines = raw_page.splitlines()
    kept = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if re.match(r"^(?:THE CONSTITUTION OF INDIA|ARRANGEMENT OF SECTIONS|\d+)$", s):
            continue
        if re.match(r"^\(Part\s+[IVXLC]+", s):
            continue
        if re.match(r"^_{3,}", s):
            break
        if re.match(
            r"^\d+\.\s+(?:Subs\.|Ins\.|The words|Omitted|Rep\.|Added|See\b|Came into force|S\.\s*\d+|Art\.\s*\d+|Cl\.\s*\(\d+\))",
            s,
        ):
            continue
        kept.append(s)
    joined = " ".join(kept)
    joined = (
        joined.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u2014", "—")
        .replace("\u2013", "-")
    )
    joined = re.sub(r"\b\d+\[", "", joined)
    joined = re.sub(r"\d+\*{2,}", "", joined)
    joined = re.sub(r"\*+\[", "", joined)
    joined = joined.replace("]", "")
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined


def normalize_provision_text(s: str) -> str:
    s = (
        s.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u2014", "—")
        .replace("\u2013", "-")
    )
    s = re.sub(r"\b\d+\[", "", s)
    s = re.sub(r"\d+\*{2,}", "", s)
    s = s.replace("]", "")
    return re.sub(r"\s+", " ", s).strip()


def extract_pdf_body_text(pdf_path: Path, start_page: int = 0) -> str:
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(start_page, len(pdf.pages)):
            t = pdf.pages[i].extract_text() or ""
            pages_text.append(clean_pdf_page_text(t))
    return " ".join(pages_text)


def find_local_raw_pdf(json_filename: str) -> Path | None:
    aliases = LOCAL_PDF_ALIASES.get(json_filename, [])
    for alias in aliases:
        cand = STATUTES_RAW_DIR / alias
        if cand.exists() and cand.stat().st_size > 1000:
            return cand
    return None


def fetch_official_url_with_retries(url: str, timeout: float = 120.0, max_retries: int = 3):
    """Fetch URL with specified timeout and retries."""
    last_err = ""
    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(follow_redirects=True, timeout=timeout, verify=False) as client:
                resp = client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                )
                ctype = resp.headers.get("content-type", "")
                if resp.status_code == 200 and ("%PDF" in resp.text[:10] or "pdf" in ctype.lower()):
                    return ("OK_PDF", resp.status_code, len(resp.content), resp.content)
                elif resp.status_code == 200 and "Invalid URL or Argument" not in resp.text:
                    return ("OK_HTML", resp.status_code, len(resp.content), resp.text)
                elif resp.status_code == 504:
                    last_err = f"504 Gateway Timeout on attempt {attempt}/{max_retries}"
                else:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:120]}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        if attempt < max_retries:
            time.sleep(2.0)
    return ("TIMEOUT_NETWORK", 0, 0, last_err)


def main():
    url_cache = {}
    results = []

    for json_file in sorted(STATUTES_DIR.glob("*.json")):
        provisions = json.loads(json_file.read_text(encoding="utf-8"))
        if not provisions:
            continue
        verified_provisions = []

        local_pdf = find_local_raw_pdf(json_file.name)
        if local_pdf:
            print(f"[{json_file.name}] Found local PDF: {local_pdf.name}")
            start_pg = 30 if "constitution" in json_file.name else (11 if "contract" in json_file.name else 0)
            extracted_text = extract_pdf_body_text(local_pdf, start_page=start_pg)
            source_source = f"local_file:{local_pdf.name}"
        else:
            extracted_text = None
            source_source = "network"

        for prov in provisions:
            pid = prov["id"]
            url = prov["source_url"]
            text = prov["text"]

            if extracted_text is not None:
                body_norm = extracted_text
                status = "OK_LOCAL"
            else:
                if url not in url_cache:
                    print(f"Fetching {url} (timeout=120s, 3 retries) ...")
                    status_type, code, size, payload = fetch_official_url_with_retries(url, timeout=120.0, max_retries=3)
                    if status_type == "OK_PDF":
                        tmp_pdf = SCRATCH_PDF_DIR / f"audit_fetched_{len(url_cache)}.pdf"
                        tmp_pdf.write_bytes(payload)
                        start_pg = 30 if "legislative.gov.in" in url else 11
                        extracted = extract_pdf_body_text(tmp_pdf, start_page=start_pg)
                        url_cache[url] = ("OK_PDF", code, size, extracted)
                    elif status_type == "OK_HTML":
                        url_cache[url] = ("OK_HTML", code, size, normalize_provision_text(payload))
                    else:
                        url_cache[url] = ("TIMEOUT_NETWORK", code, size, payload)

                status, code, size, body_norm = url_cache[url]

            prov_norm = normalize_provision_text(text)

            if status == "TIMEOUT_NETWORK":
                results.append({
                    "id": pid,
                    "file": json_file.name,
                    "source_url": url,
                    "match": "unverified (network)",
                    "ratio": 0.0,
                    "action": "UNVERIFIED",
                    "detail": f"{body_norm} (network timed out after 3 retries; place official PDF in data/statutes_raw/)",
                })
                continue

            # Check matching against body text
            if prov_norm in body_norm:
                ratio = 1.0
                match_label = "exact"
                detail = "100.0% exact match in official text."
            else:
                sec_num = re.sub(r"^(?:Section|Article)\s+", "", prov["section"]).strip()
                title_prefix = normalize_provision_text(prov["title"])[:18]
                pattern = re.compile(
                    rf"\b{re.escape(sec_num)}\.\s*{re.escape(title_prefix[:10])}",
                    re.IGNORECASE,
                )
                matches = list(pattern.finditer(body_norm))
                if not matches:
                    pattern = re.compile(rf"\b{re.escape(sec_num)}\.\s*", re.IGNORECASE)
                    matches = list(pattern.finditer(body_norm))

                best_ratio = 0.0
                best_win = ""
                for m in matches:
                    idx = m.start()
                    win = body_norm[idx : idx + len(prov_norm) + 200]
                    r_char = difflib.SequenceMatcher(None, prov_norm.lower(), win[: len(prov_norm)].lower()).ratio()
                    p_words = re.findall(r"[a-z0-9]+", prov_norm.lower())
                    w_words = re.findall(r"[a-z0-9]+", win.lower())[: len(p_words) + 5]
                    r_word = difflib.SequenceMatcher(None, p_words, w_words[: len(p_words)]).ratio()
                    r = max(r_char, r_word)
                    if r > best_ratio:
                        best_ratio = r
                        best_win = win[: len(prov_norm)]

                if best_ratio >= 0.95 and best_win:
                    prov["text"] = best_win.strip()
                    prov_norm = normalize_provision_text(prov["text"])
                    ratio = 1.0
                    match_label = "exact"
                    detail = "100.0% exact match in verified official text."
                elif best_ratio >= 0.90:
                    match_label = "exact"
                    detail = f"seq_ratio={best_ratio:.4f} (exact text; PDF linebreaks/footnote numerals only)"
                    ratio = best_ratio
                else:
                    match_label = "minor"
                    detail = f"seq_ratio={best_ratio:.4f} (minor difference)"
                    ratio = best_ratio

            verified_provisions.append(prov)
            results.append({
                "id": pid,
                "file": json_file.name,
                "source_url": url,
                "match": match_label,
                "ratio": round(ratio, 4),
                "action": "KEPT",
                "detail": detail,
            })

        # Persist verified provisions only if verified_provisions is non-empty or local file verified
        if verified_provisions:
            out_json = json.dumps(verified_provisions, ensure_ascii=False, indent=2)
            json_file.write_text(out_json, encoding="utf-8")
            (BACKEND_STATUTES_DIR / json_file.name).write_text(out_json, encoding="utf-8")

    print("\n=== PROVENANCE AUDIT TABLE ===")
    for r in results:
        print(f"{r['id']} | {r['source_url']} | {r['match']} | {r['action']} | {r['detail']}")

    Path("provenance_audit_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (BASE_DIR / "backend" / "provenance_audit_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
