# 📖 PDF to Audiobook Converter

> Turn any PDF into a listenable MP3 audiobook — free, fast, and with no subscriptions required.

---

## Features

- 📄 Extracts text from any text-based PDF
- 🔊 Two TTS engines: **Google TTS** (natural voices) or **pyttsx3** (fully offline)
- 🌍 Supports 40+ languages via Google TTS
- ✂️ Convert specific page ranges — no need to process an entire book
- 🧹 Auto-cleans extracted text (removes page numbers, fixes hyphenation, etc.)
- 🔗 Merges all audio chunks into a single `.mp3` output file

---

## Requirements

- Python 3.10+
- pip packages (see Installation)

---

## Installation

```bash
pip install pypdf gtts pyttsx3 pydub
```

| Package   | Purpose                                      |
|-----------|----------------------------------------------|
| `pypdf`   | Extract text from PDF files                  |
| `gtts`    | Google Text-to-Speech (online, natural voices)|
| `pyttsx3` | Offline TTS engine (no internet needed)      |
| `pydub`   | Merge audio chunks into one MP3              |

> **Note:** `pydub` requires [FFmpeg](https://ffmpeg.org/download.html) to be installed on your system for full audio merging support. Without it, the script falls back to binary MP3 concatenation (works in most players).

---

## Usage

### Basic — convert an entire PDF

```bash
python pdf_to_audiobook.py mybook.pdf
```

Output: `mybook_audiobook.mp3`

---

### Specify an output file name

```bash
python pdf_to_audiobook.py mybook.pdf --output my_audiobook.mp3
```

---

### Convert a specific page range

```bash
python pdf_to_audiobook.py mybook.pdf --pages 1-50
```

---

### Use the offline engine (no internet required)

```bash
python pdf_to_audiobook.py mybook.pdf --tts pyttsx3
```

---

### Change the language (Google TTS only)

```bash
python pdf_to_audiobook.py mybook.pdf --lang fr
python pdf_to_audiobook.py mybook.pdf --lang de
python pdf_to_audiobook.py mybook.pdf --lang es
```

See the full list of supported language codes [here](https://gtts.readthedocs.io/en/latest/module.html#languages-gtts-lang).

---

### All options

```
usage: pdf_to_audiobook.py [-h] [--output OUTPUT] [--pages START-END] [--lang LANG] [--tts {google,pyttsx3}] pdf

positional arguments:
  pdf                        Path to the input PDF file

optional arguments:
  -h, --help                 Show this help message and exit
  --output, -o OUTPUT        Output MP3 file path (default: <pdf_name>_audiobook.mp3)
  --pages, -p START-END      Page range e.g. 1-10 (default: all pages)
  --lang, -l LANG            Language code for Google TTS (default: en)
  --tts, -t {google,pyttsx3} TTS engine to use (default: google)
```

---

## How It Works

```
PDF file
   │
   ▼
[pypdf] Extract raw text page by page
   │
   ▼
[Cleaner] Remove page numbers, fix hyphenation, normalise whitespace
   │
   ▼
[Chunker] Split into sentence-aware chunks (~3,000 chars each)
   │
   ▼
[TTS Engine] Synthesise each chunk to an MP3 audio file
   │
   ▼
[Merger] Stitch all chunks into one final MP3
   │
   ▼
🎧 audiobook.mp3
```

---

## TTS Engine Comparison

|                   | Google TTS (`gtts`) | pyttsx3          |
|-------------------|---------------------|------------------|
| Voice quality     | ⭐⭐⭐⭐⭐ Very natural | ⭐⭐⭐ Robotic      |
| Internet required | ✅ Yes               | ❌ No             |
| Languages         | 40+                 | System voices only|
| Cost              | Free                | Free             |
| Speed             | Moderate            | Fast             |

---

## Limitations & Troubleshooting

**"No text could be extracted from this PDF"**
Your PDF is likely a scanned document (an image of a page, not selectable text). Run it through an OCR tool first:
```bash
pip install ocrmypdf
ocrmypdf scanned.pdf readable.pdf
python pdf_to_audiobook.py readable.pdf
```

**Audio sounds cut off between chunks**
Install `pydub` and FFmpeg for seamless merging:
```bash
pip install pydub
# Then install FFmpeg: https://ffmpeg.org/download.html
```

**Google TTS rate limiting / slow conversion**
The script adds a 0.3-second delay between requests to be polite to the API. For very large books, consider using `--tts pyttsx3` instead, or splitting the job with `--pages`.

**pyttsx3 produces no audio on Linux**
You may need to install `espeak`:
```bash
sudo apt-get install espeak
```

---

## Example Output

```
📄  Reading PDF: my_novel.pdf
    Total pages : 312
    Extracting  : all 312 pages

📊  Extracted 87,432 words (512,091 characters)

🔊  Google TTS  |  171 chunk(s) to synthesise …
    Merging 171 audio chunk(s) …

────────────────────────────────────────────────────────
  ✅  Audiobook created successfully!
  📄  Source   : my_novel.pdf
  🎧  Output   : my_novel_audiobook.mp3  (48.3 MB)
  ⏱️   Duration  : ~106 minutes (estimated)
  🔤  Engine   : google
────────────────────────────────────────────────────────
```

---

## License

Free to use and modify for personal and educational purposes.
