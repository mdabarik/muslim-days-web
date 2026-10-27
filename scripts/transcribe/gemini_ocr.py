#!/usr/bin/env python3
"""Create resumable Gemini OCR evidence from the extracted Quran page images.

The scan is the only authority. Output from this tool is an unreviewed hypothesis
and must never be published without checking every glyph against the source image.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path


STATUS = "unreviewed_ocr_hypothesis_do_not_publish"
DEFAULT_MODEL = "gemini-3.8-flash"

PROMPT = """You are visually transcribing ONE scanned page of a Bengali Qariana
Quran. The attached scan is the only authority. Do not complete Quran text from
memory, another edition, online text, or linguistic expectation. Never silently
omit an unreadable word or symbol. Give the best visible reading and add an
uncertainty entry for every doubtful glyph.

Read the page top-to-bottom. A normal printed row contains: (1) a small mark band
above Arabic words, (2) a large Arabic line read right-to-left, and (3) a Bengali
translation line read left-to-right. Preserve what is PRINTED, including:

- every Arabic base letter and every visible fatha, kasra, damma, sukun, shadda,
  tanwin, standing fatha U+0670, standing kasra U+0656, inverted damma U+0657,
  madd U+0653, small meem/iqlab U+06E2, hamza form, dotless ya, and stop sign;
- every Bengali instructional mark above the Arabic, including Bengali digits or
  letters, circled signs, wedge/ring/arrow shapes, and its approximate target word;
- every ayah rosette and its printed Bengali numeral;
- Bengali spelling, punctuation, quotes, numerals, and line continuations exactly;
- header, footer, surah boxes, basmala, marginal notes, and visible furniture.

For Arabic words, use Unicode combining marks exactly as seen. Put shadda before
its vowel in Unicode order. Do not add tatweel. Number Arabic words right-to-left
across each whole row starting at 1. List mark-band signs right-to-left. Estimate
mark target and horizontal offset only when visible. If a mark cannot be encoded,
record its visible shape in shape and flag it uncertain. Do not translate,
modernize spelling, correct grammar, or claim certainty from context.

Return JSON matching the supplied schema. This is OCR evidence, not verified
Quran text. Set page_number to the number supplied in this prompt: {page_number}.
"""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["page_number", "kind", "printed_page", "furniture", "rows", "uncertain"],
    "properties": {
        "page_number": {"type": "integer"},
        "kind": {"type": "string", "enum": ["quran", "non_quran", "blank", "uncertain"]},
        "printed_page": {"type": ["string", "null"]},
        "furniture": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "text", "uncertain"],
                "properties": {
                    "kind": {"type": "string"},
                    "text": {"type": "string"},
                    "uncertain": {"type": "boolean"},
                },
            },
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["row_index", "marks", "arabic_segments", "bengali_segments", "uncertain"],
                "properties": {
                    "row_index": {"type": "integer"},
                    "marks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["printed", "shape", "target_word", "offset", "uncertain"],
                            "properties": {
                                "printed": {"type": ["string", "null"]},
                                "shape": {"type": ["string", "null"]},
                                "target_word": {"type": ["integer", "null"]},
                                "offset": {"type": ["number", "null"]},
                                "uncertain": {"type": "boolean"},
                            },
                        },
                    },
                    "arabic_segments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["words", "stop", "end_marker", "uncertain"],
                            "properties": {
                                "words": {"type": "array", "items": {"type": "string"}},
                                "stop": {"type": ["string", "null"]},
                                "end_marker": {"type": ["string", "null"]},
                                "uncertain": {"type": "boolean"},
                            },
                        },
                    },
                    "bengali_segments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["numeral", "text", "uncertain"],
                            "properties": {
                                "numeral": {"type": "string"},
                                "text": {"type": "string"},
                                "uncertain": {"type": "boolean"},
                            },
                        },
                    },
                    "uncertain": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "uncertain": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["where", "question"],
                "properties": {
                    "where": {"type": "string"},
                    "question": {"type": "string"},
                },
            },
        },
    },
}


def load_local_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def post_json(url: str, api_key: str, payload: dict, retries: int = 4) -> dict:
    encoded = json.dumps(payload, ensure_ascii=False).encode()
    for attempt in range(retries + 1):
        request = urllib.request.Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries:
                try:
                    message = json.loads(body).get("error", {}).get("message", body)
                except json.JSONDecodeError:
                    message = body
                raise RuntimeError(f"Gemini HTTP {exc.code}: {message[:1000]}") from exc
            time.sleep(min(2 ** attempt, 20))
    raise AssertionError("unreachable")


def response_text(response: dict) -> str:
    candidates = response.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {response.get('promptFeedback', {})}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts if "text" in part)
    if not text:
        raise RuntimeError("Gemini returned no text")
    return text


def validate_transcription(value: dict, page: int) -> list[str]:
    warnings = []
    if value.get("page_number") != page:
        warnings.append(f"page_number mismatch: {value.get('page_number')} != {page}")
    serialized = json.dumps(value, ensure_ascii=False)
    if "\ufffd" in serialized:
        warnings.append("Unicode replacement character is present")
    if unicodedata.normalize("NFC", serialized) != serialized:
        warnings.append("Output is not fully NFC-normalized; preserve raw output for review")
    if value.get("kind") == "quran" and not value.get("rows"):
        warnings.append("Quran page contains no rows")
    return warnings


def transcribe(page: int, image_path: Path, output_path: Path, model: str, force: bool) -> None:
    image_hash = sha256(image_path)
    if output_path.exists() and not force:
        existing = json.loads(output_path.read_text())
        if existing.get("source", {}).get("sha256") == image_hash and existing.get("model") == model:
            print(json.dumps({"page": page, "status": "already_present"}))
            return

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("Set GEMINI_API_KEY in the environment or .env.local")

    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": PROMPT.format(page_number=page)},
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": base64.b64encode(image_path.read_bytes()).decode("ascii"),
                    },
                    "mediaResolution": {"level": "MEDIA_RESOLUTION_HIGH"},
                },
            ],
        }],
        "generationConfig": {
            "maxOutputTokens": 32768,
            "responseMimeType": "application/json",
            "responseJsonSchema": SCHEMA,
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    response = post_json(url, api_key, payload)
    transcription = json.loads(response_text(response))
    warnings = validate_transcription(transcription, page)
    result = {
        "status": STATUS,
        "provider": "google-gemini",
        "model": model,
        "source": {"path": str(image_path), "sha256": image_hash, "mime_type": "image/png"},
        "request": {"media_resolution": "HIGH", "temperature": 0, "schema_version": 1},
        "usage": response.get("usageMetadata", {}),
        "model_version": response.get("modelVersion"),
        "validation_warnings": warnings,
        "transcription": transcription,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(output_path)
    print(json.dumps({
        "page": page,
        "status": STATUS,
        "rows": len(transcription.get("rows", [])),
        "uncertain": len(transcription.get("uncertain", [])),
        "warnings": warnings,
        "output": str(output_path),
    }, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("output/extracted_pages"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/ocr/gemini"))
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()
    end = args.end if args.end is not None else args.start
    if not (1 <= args.start <= end <= 752):
        raise SystemExit("Page range must be within 1..752")
    load_local_env(Path(".env.local"))
    for page in range(args.start, end + 1):
        image_path = args.input_dir / f"page_{page:04}.png"
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        output_path = args.output_dir / f"page_{page:04}.gemini.json"
        transcribe(page, image_path, output_path, args.model, args.force)
        if page != end and args.delay:
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
