# 🌌 NASA APOD Explorer

> **Browse and compare NASA's Astronomy Picture of the Day from your terminal.**

The official [APOD website](https://apod.nasa.gov/) shows one photo at a time.
This CLI lets you **compare a full date range side-by-side**, pull random photos
from the entire 30-year archive, and pipe clean JSON into other tools — none of
which the website can do.

---

## 📁 Project Structure

```
nasa-apod-explorer/
├── app.py            ← Entire CLI application (~310 lines, no frameworks)
├── requirements.txt  ← Single dependency: requests
├── README.md         ← This file
└── ANSWERS.md        ← Assessment answers
```

---

## 🚀 Quick Start (Fresh Machine)

### 1 — Prerequisites

| Requirement | Minimum version |
|-------------|-----------------|
| Python      | 3.10            |
| pip         | any recent      |

Check yours:
```bash
python --version
pip --version
```

### 2 — Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/nasa-apod-explorer.git
cd nasa-apod-explorer
```

### 3 — Create a virtual environment

```bash
# macOS / Linux
python -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

### 4 — Install the one dependency

```bash
pip install -r requirements.txt
```

### 5 — Get a (free) NASA API key

1. Visit **<https://api.nasa.gov/>**
2. Fill in the form → click **Sign Up**
3. Key arrives in your email within seconds

> **No email yet?** Use `DEMO_KEY` — it works immediately but is rate-limited
> to **30 requests / hour per IP**.

### 6 — Run it

```bash
python app.py --api-key YOUR_KEY today
```

That's the only command you need to confirm everything works. ✅

---

## 📖 All Commands

### `today` — Today's picture

```bash
python app.py --api-key YOUR_KEY today
```

### `date` — A specific date

```bash
python app.py --api-key YOUR_KEY date --date 2024-04-08
```

Valid range: **1995-06-16** (APOD launch) → today.

### `range` — Compare multiple days

```bash
python app.py --api-key YOUR_KEY range --start 2024-01-01 --end 2024-01-05
```

Fetches each day in sequence and prints them one after another — great for
spotting themes across a week or comparing different eras.

> ⚠️ Each day = one API call. Keep ranges under ~30 days with `DEMO_KEY`.

### `random` — Random photos from the archive

```bash
python app.py --api-key YOUR_KEY random --count 5
```

`--count` accepts 1–100. NASA returns a truly random selection from 30 years
of photos in a single API call.

### `--json` flag — Machine-readable output

Append `--json` to **any** command to get raw NASA JSON instead:

```bash
python app.py --api-key YOUR_KEY today --json
python app.py --api-key YOUR_KEY random --count 3 --json | python -m json.tool
```

---

## 🛡️ Error Handling

The tool handles every failure mode gracefully:

| Situation | What you see |
|-----------|--------------|
| NASA is slow / unresponsive | `[WARN] NASA API did not respond within 30 s. Using an offline preview.` |
| Invalid API key | `[ERROR] NASA API error 403: API_KEY_INVALID` |
| Date before 1995-06-16 | `[ERROR] Date … is before APOD's launch on 1995-06-16.` |
| Future date | `[ERROR] Date … is in the future. NASA hasn't taken that photo yet.` |
| Start date after end date | `[WARN] Swapping them.` then continues normally |
| No internet | `[WARN] No network connection. Using an offline preview.` |
| NASA rate limit hit | `[WARN] NASA API rate limit reached. Using an offline preview.` |

Warnings and errors go to **stderr**, so `--json` output piped to other tools stays clean.

---

## 🔑 Keeping Your API Key Safe

Never commit your key. Use an environment variable instead:

```bash
# Set once in your shell session
export NASA_API_KEY="your_key_here"

# Then use it
python app.py --api-key "$NASA_API_KEY" today
```

Or store it in a `.env` file (already in `.gitignore`) and load it with:

```bash
source .env   # if your .env contains:  export NASA_API_KEY=abc123
```

---

## 🧪 Testing Error Paths Deliberately

```bash
# Bad date format
python app.py --api-key DEMO_KEY date --date 2024/04/08

# Date before APOD existed
python app.py --api-key DEMO_KEY date --date 1990-01-01

# Future date
python app.py --api-key DEMO_KEY date --date 2099-12-31

# Bad API key → NASA returns 403
python app.py --api-key BADKEY today

# Reversed date range → auto-corrected with a warning
python app.py --api-key DEMO_KEY range --start 2024-01-05 --end 2024-01-01
```

---

## 📦 Dependencies

```
requests>=2.31.0
```

Everything else uses Python's standard library (`argparse`, `json`, `datetime`, `sys`).

---

## 💡 Why This Is Useful

| Task | APOD Website | This CLI |
|------|-------------|----------|
| See today's photo | ✅ | ✅ |
| See a specific past date | ✅ (manual search) | ✅ `date --date` |
| Compare a date range side-by-side | ❌ | ✅ `range` |
| Get random photos from 30-year archive | ❌ | ✅ `random --count N` |
| Pipe data into other tools as JSON | ❌ | ✅ `--json` flag |
| Use offline / in scripts | ❌ | ✅ |
