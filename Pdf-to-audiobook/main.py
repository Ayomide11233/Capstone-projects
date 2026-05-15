#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║           📖 PDF to Audiobook Converter 🎧               ║
║    Converts any PDF file into a spoken MP3 audiobook     ║
╚══════════════════════════════════════════════════════════╝

Usage:
    python pdf_to_audiobook.py <path_to_pdf> [options]

Examples:
    python pdf_to_audiobook.py book.pdf
    python pdf_to_audiobook.py book.pdf --lang en --output my_audiobook.mp3
    python pdf_to_audiobook.py book.pdf --pages 1-10
    python pdf_to_audiobook.py book.pdf --tts google
    python pdf_to_audiobook.py book.pdf --tts pyttsx3  # fully offline

Requirements (install with pip):
    pip install pypdf gtts pyttsx3 pydub

Optional (for audio playback):
    pip install playsound
"""

import argparse
import os
import re
import sys
import tempfile
import time
from pathlib import Path


# ─────────────────────────────────────────────────────────────
# 1.  DEPENDENCY CHECK
# ─────────────────────────────────────────────────────────────

def check_dependencies(tts_engine: str) -> None:
    missing = []
    try:
        import pypdf  # noqa: F401
    except ImportError:
        missing.append("pypdf")

    if tts_engine == "google":
        try:
            import gtts  # noqa: F401
        except ImportError:
            missing.append("gtts")
    elif tts_engine == "pyttsx3":
        try:
            import pyttsx3  # noqa: F401
        except ImportError:
            missing.append("pyttsx3")

    if missing:
        print(f"\n❌  Missing packages: {', '.join(missing)}")
        print(f"    Install with:  pip install {' '.join(missing)}\n")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────
# 2.  PDF TEXT EXTRACTION
# ─────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str, page_range: tuple[int, int] | None = None) -> str:
    """
    Extract and clean text from a PDF file.
    page_range: (start, end) — 1-based, inclusive.
    """
    from pypdf import PdfReader

    print(f"\n📄  Reading PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"    Total pages : {total_pages}")

    if page_range:
        start = max(0, page_range[0] - 1)          # convert to 0-based
        end   = min(total_pages, page_range[1])
        pages = reader.pages[start:end]
        print(f"    Extracting  : pages {page_range[0]}–{page_range[1]}")
    else:
        pages = reader.pages
        print(f"    Extracting  : all {total_pages} pages")

    raw_chunks = []
    for i, page in enumerate(pages, start=1):
        text = page.extract_text() or ""
        raw_chunks.append(text)
        if i % 10 == 0 or i == len(pages):
            print(f"    Progress    : {i}/{len(pages)} pages read", end="\r")

    print()
    full_text = "\n".join(raw_chunks)
    return clean_text(full_text)


def clean_text(text: str) -> str:
    """Remove artefacts that read badly when spoken aloud."""
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove lone page numbers (e.g. "  42\n")
    text = re.sub(r'^\s*\d{1,4}\s*$', '', text, flags=re.MULTILINE)
    # Replace hyphens used for line-breaking mid-word
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    # Normalise whitespace
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = text.strip()
    return text


# ─────────────────────────────────────────────────────────────
# 3.  TEXT-TO-SPEECH ENGINES
# ─────────────────────────────────────────────────────────────

MAX_CHUNK_CHARS = 3000   # gTTS limit; pyttsx3 handles longer, but chunking helps both


def split_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text into sentence-aware chunks under max_chars."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current += (" " if current else "") + sentence
        else:
            if current:
                chunks.append(current)
            # If a single sentence is too long, split on commas/newlines
            if len(sentence) > max_chars:
                parts = re.split(r'(?<=,)\s+|\n', sentence)
                sub = ""
                for part in parts:
                    if len(sub) + len(part) + 1 <= max_chars:
                        sub += (" " if sub else "") + part
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = part
                if sub:
                    current = sub
                else:
                    current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


def tts_google(text: str, output_path: str, lang: str = "en") -> None:
    """Convert text to speech using Google TTS (requires internet)."""
    from gtts import gTTS

    chunks = split_into_chunks(text)
    total  = len(chunks)
    print(f"\n🔊  Google TTS  |  {total} chunk(s) to synthesise …")

    tmp_files = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for idx, chunk in enumerate(chunks, 1):
            tmp_file = os.path.join(tmp_dir, f"chunk_{idx:04d}.mp3")
            print(f"    Synthesising chunk {idx}/{total} ({len(chunk)} chars) …", end="\r")
            tts = gTTS(text=chunk, lang=lang, slow=False)
            tts.save(tmp_file)
            tmp_files.append(tmp_file)
            time.sleep(0.3)   # polite delay

        print(f"\n    Merging {total} audio chunk(s) …")
        _merge_mp3_files(tmp_files, output_path)


def tts_pyttsx3(text: str, output_path: str) -> None:
    """Convert text to speech using pyttsx3 (fully offline)."""
    import pyttsx3

    print(f"\n🔊  pyttsx3 TTS  |  Offline engine …")
    engine = pyttsx3.init()

    # Tweak voice properties for a nicer audiobook feel
    engine.setProperty('rate', 165)     # words per minute (default ≈ 200)
    engine.setProperty('volume', 1.0)

    # Try to pick a higher-quality voice if available
    voices = engine.getProperty('voices')
    for v in voices:
        if 'english' in v.name.lower() or 'en_us' in v.id.lower():
            engine.setProperty('voice', v.id)
            break

    print(f"    Saving to: {output_path}")
    engine.save_to_file(text, output_path)
    engine.runAndWait()


def _merge_mp3_files(files: list[str], output_path: str) -> None:
    """Concatenate MP3 files. Falls back to raw binary concat if pydub missing."""
    try:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for f in files:
            combined += AudioSegment.from_mp3(f)
        combined.export(output_path, format="mp3")
    except ImportError:
        # Binary concat — works for MP3 in most players
        with open(output_path, "wb") as out:
            for f in files:
                with open(f, "rb") as src:
                    out.write(src.read())


# ─────────────────────────────────────────────────────────────
# 4.  MAIN ORCHESTRATION
# ─────────────────────────────────────────────────────────────

def parse_page_range(value: str) -> tuple[int, int]:
    """Parse '5-20' into (5, 20)."""
    match = re.match(r'^(\d+)-(\d+)$', value.strip())
    if not match:
        raise argparse.ArgumentTypeError("Page range must be e.g. '1-10'")
    start, end = int(match.group(1)), int(match.group(2))
    if start < 1 or start > end:
        raise argparse.ArgumentTypeError("Invalid page range.")
    return start, end


def build_output_path(pdf_path: str, output_arg: str | None) -> str:
    if output_arg:
        return output_arg
    stem = Path(pdf_path).stem
    return f"{stem}_audiobook.mp3"


def print_summary(pdf_path: str, output_path: str, char_count: int, engine: str) -> None:
    size_mb = os.path.getsize(output_path) / 1_048_576
    approx_minutes = char_count / (165 * 5)   # ~165 wpm, ~5 chars/word
    print("\n" + "─" * 56)
    print("  ✅  Audiobook created successfully!")
    print(f"  📄  Source   : {pdf_path}")
    print(f"  🎧  Output   : {output_path}  ({size_mb:.1f} MB)")
    print(f"  ⏱️   Duration  : ~{approx_minutes:.0f} minutes (estimated)")
    print(f"  🔤  Engine   : {engine}")
    print("─" * 56 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="📖 Convert a PDF to an MP3 audiobook.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("pdf",           help="Path to the input PDF file")
    parser.add_argument("--output",  "-o", help="Output MP3 file path (default: <pdf_name>_audiobook.mp3)")
    parser.add_argument("--pages",   "-p", type=parse_page_range, metavar="START-END",
                        help="Page range, e.g. --pages 1-10  (default: all pages)")
    parser.add_argument("--lang",    "-l", default="en",
                        help="Language code for Google TTS (default: en). E.g. fr, de, es, zh")
    parser.add_argument("--tts",     "-t", choices=["google", "pyttsx3"], default="google",
                        help="TTS engine to use (default: google). pyttsx3 = fully offline")

    args = parser.parse_args()

    # ── Validate input ──────────────────────────────────────
    if not os.path.isfile(args.pdf):
        print(f"\n❌  File not found: {args.pdf}\n")
        sys.exit(1)
    if not args.pdf.lower().endswith(".pdf"):
        print("\n⚠️   Warning: file does not have a .pdf extension. Continuing anyway …\n")

    check_dependencies(args.tts)

    output_path = build_output_path(args.pdf, args.output)

    # ── Extract text ─────────────────────────────────────────
    text = extract_text_from_pdf(args.pdf, page_range=args.pages)

    if not text.strip():
        print("\n❌  No text could be extracted from this PDF.")
        print("    It may be a scanned image PDF. Try an OCR tool first (e.g. Adobe Acrobat, OCRmyPDF).\n")
        sys.exit(1)

    char_count = len(text)
    word_count = len(text.split())
    print(f"\n📊  Extracted {word_count:,} words ({char_count:,} characters)")

    # ── Convert to speech ─────────────────────────────────────
    if args.tts == "google":
        tts_google(text, output_path, lang=args.lang)
    elif args.tts == "pyttsx3":
        tts_pyttsx3(text, output_path)

    print_summary(args.pdf, output_path, char_count, args.tts)


if __name__ == "__main__":
    main()