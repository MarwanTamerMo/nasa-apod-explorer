# My stupendous Answers (I'm not narcisstisc, just joking)

## 1. How to Run

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/nasa-apod-explorer.git
cd nasa-apod-explorer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run (replace DEMO_KEY with your NASA key from https://api.nasa.gov/)
python app.py --api-key DEMO_KEY today

```
To try other commands:

```bash
python app.py --api-key DEMO_KEY date --date 2024-04-08
python app.py --api-key DEMO_KEY range --start 2024-01-01 --end 2024-01-05
python app.py --api-key DEMO_KEY random --count 5
python app.py --api-key DEMO_KEY today --json
```

No build step, no database, no config files. One `pip install` and it runs.

> **Hint:** Confirm Python ≥ 3.10 is installed. The only external dependency is `requests`.

---

## 2. Stack Choice

Python was the right call for this task for three reasons. First, `requests` is
the de-facto HTTP library in Python — it handles timeouts, status codes, redirects,
and JSON deserialization in a handful of lines, and every Python developer reviewing
the code will immediately understand it.

Secondly, `why the hell not?` Python is amazing, simple, joker language as I call it meaning ready for 90% of the use cases if not all in some situations.

**What would have been a worse choice?**

Bash + curl would have been worse. JSON parsing in Bash requires `jq` as an
external dependency, date arithmetic is fragile and platform-specific (GNU date
vs. BSD date behave differently), and robust try/catch-style error handling
quickly becomes unreadable.

---

## 3. One Real Edge Case

**File:** `app.py` | **Function:** `validate_date` (lines ~30–48)

**The case:** User runs:
```bash
python app.py --api-key KEY date --date 1990-01-01
```

**Without the guard:** `requests` sends the date to NASA, which returns
`HTTP 400: Date must be between Jun 16, 1995 and <today>` — a raw API error
the user has to decode themselves, and a wasted network round-trip.

**With the guard:** `validate_date()` checks the date before any network call
and immediately prints:
```
[ERROR] Date 1990-01-01 is before APOD's launch on 1995-06-16.
        NASA has no pictures that far back.
```

Actionable, instant, no network call wasted.

> **Alternative edge case to mention (also valid):**
> In `cmd_range`, when `--start` is after `--end`, the code swaps them silently
> instead of crashing. Without this, the `while cur <= end` loop would exit
> immediately and return zero results with no error message.

---

## 4. AI Usage

| # | Tool | What I asked | What it gave me | What I changed and why |
|---|------|-------------|-----------------|------------------------|
| 1 | Perplexity AI | Build a complete Python CLI project that uses the NASA APOD API and satisfies the assessment requirements | A full project scaffold including `app.py`, `requirements.txt`, `README.md`, and a draft `ANSWERS.md` | I revised the generated code and docs to fit the assessment more precisely. In particular, I made the CLI structure clearer and tightened the explanations in the documentation so they directly map to the five required questions. |

| 2 | Perplexity AI | How should a Python CLI cleanly handle API timeout, HTTP errors, and no-internet situations using `requests`? | Example `try/except` blocks for `requests.Timeout`, `requests.HTTPError`, and `requests.ConnectionError` | The AI output used generic messages and normal `print()` calls. I changed the error output to `print(..., file=sys.stderr)` and rewrote the messages to be user-focused. I did that because stdout should stay clean for normal output and JSON piping, while stderr is the correct stream for errors. |

| 3 | Perplexity AI | What is the earliest valid APOD date and what happens if the user requests an invalid date? | Confirmation that APOD starts on `1995-06-16` and that NASA returns a 400-style error for out-of-range dates | I turned that into local validation logic in `validate_date()` instead of relying on the API to reject it. I changed it because failing early gives a faster and clearer user experience and avoids unnecessary API calls. |

I used AI mainly as a coding and drafting assistant, not as a copy-paste replacement. I reviewed the generated output, edited it, and adapted it to the exact constraints of the task.

---

## 5. Honest Gap

**Gap:** The tool has no caching. Every `range` command re-fetches data from
NASA even if you ran the same range 10 minutes ago, burning rate-limit quota.

**What I'd fix with another day:**
Add a simple on-disk cache: a `~/.apod_cache/` directory with one JSON file per
date (filename = `YYYY-MM-DD.json`). Before each `fetch()` call, check if the
file exists; if yes, load it from disk. Write to disk on every fresh API hit.
This would make repeated `range` calls instant and make `DEMO_KEY` practical for
longer ranges.

That change would make repeated range queries much faster, reduce rate-limit issues,
and even make previously fetched dates available offline.

> **Other honest gaps you could pick instead:**
> - No unit tests (would add `pytest` with mocked `requests` responses)
> - No `--save` flag to download the HD image to disk
> - No `--open` flag to launch the image in the OS default viewer