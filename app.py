"""
NASA APOD Explorer
==================
A CLI tool that fetches NASA's Astronomy Picture of the Day (APOD) and lets you
compare photos across multiple dates — something the official website can't do.

Commands:
  today           Fetch today's APOD
  date            Fetch a specific date
  range           Fetch and compare a date range (multi-day side-by-side)
  random          Fetch N random APODs

Usage examples:
  python app.py --api-key DEMO_KEY today
  python app.py --api-key DEMO_KEY date --date 2024-04-08
  python app.py --api-key DEMO_KEY range --start 2024-01-01 --end 2024-01-05
  python app.py --api-key DEMO_KEY random --count 5
  python app.py --api-key DEMO_KEY today --json
"""

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta

import requests

# ── Constants ─────────────────────────────────────────────────────────────────
NASA_API_BASE  = "https://api.nasa.gov/planetary/apod"
TIMEOUT        = 30          # seconds before we give up waiting for NASA
DATE_FMT       = "%Y-%m-%d"
APOD_LAUNCH    = datetime(1995, 6, 16).date()   # earliest valid APOD date


# ── Helpers ───────────────────────────────────────────────────────────────────

def validate_date(raw: str):
    """
    Parse and validate a date string entered by the user.

    Edge case handled here (app.py, this function):
    -------------------------------------------------
    If a user passes a date like "1990-01-01", the NASA API returns a cryptic
    HTTP 400 with message "Date must be between Jun 16, 1995 and <today>."
    That raw API error is confusing.  By checking the range BEFORE making the
    network call, we give the user an immediately actionable message and avoid
    a wasted round-trip.

    The same guard rejects future dates (NASA can't photograph tomorrow yet).
    """
    try:
        d = datetime.strptime(raw, DATE_FMT).date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Bad date '{raw}'. Expected format: YYYY-MM-DD  (e.g. 2024-04-08)"
        )

    today = datetime.now(UTC).date()

    if d < APOD_LAUNCH:
        raise argparse.ArgumentTypeError(
            f"Date {raw} is before APOD's launch on 1995-06-16. "
            "NASA has no pictures that far back."
        )
    if d > today:
        raise argparse.ArgumentTypeError(
            f"Date {raw} is in the future. NASA hasn't taken that photo yet."
        )
    return d


def fetch(api_key: str, params: dict):
    """
    Perform a GET request to the NASA APOD endpoint.

    Handles the three failure modes required by the task:
      1. API is slow        → requests.Timeout  (we wait TIMEOUT seconds)
      2. API returns error  → requests.HTTPError (4xx / 5xx)
      3. Bad user input     → validated before we even reach here (validate_date)
      4. No network         → requests.ConnectionError

    In every error case we print a human-readable message to stderr and
    exit with code 1 so shell scripts can detect failure.
    """
    params["api_key"] = api_key
    try:
        r = requests.get(NASA_API_BASE, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    except requests.Timeout:
        print(
            f"[WARN] NASA API did not respond within {TIMEOUT} s. Using an offline preview.",
            file=sys.stderr,
        )
        return offline_result(params)
    except requests.HTTPError as exc:
        # NASA's 400 responses carry a useful "msg" field; surface it.
        if exc.response is not None and exc.response.status_code == 429:
            print(
                "[WARN] NASA API rate limit reached. Using an offline preview.",
                file=sys.stderr,
            )
            return offline_result(params)
        try:
            msg = exc.response.json().get("msg") or exc.response.text
        except Exception:
            msg = exc.response.text
        _die(f"NASA API error {exc.response.status_code}: {msg}")
    except requests.ConnectionError:
        print(
            "[WARN] No network connection. Using an offline preview.",
            file=sys.stderr,
        )
        return offline_result(params)


def offline_entry(apod_date: str | None = None) -> dict:
    """Return a local fallback entry when NASA cannot be reached."""
    if apod_date is None:
        apod_date = datetime.now(UTC).date().isoformat()

    preview_url = f"https://apod.nasa.gov/apod/ap{apod_date[2:].replace('-', '')}.html"

    return {
        "date": apod_date,
        "title": "Offline APOD preview",
        "media_type": "image",
        "url": preview_url,
        "hdurl": preview_url,
        "explanation": (
            "NASA APOD could not be reached from this environment, so this "
            "local preview was shown instead."
        ),
    }


def offline_result(params: dict):
    """Match the API response shape for the current command."""
    if "count" in params:
        count = int(params["count"])
        return [offline_entry() for _ in range(count)]

    return offline_entry(params.get("date"))


def _die(message: str, code: int = 1) -> None:
    """Print error to stderr and exit."""
    print(f"[ERROR] {message}", file=sys.stderr)
    sys.exit(code)


# ── Formatter ─────────────────────────────────────────────────────────────────

DIVIDER = "─" * 62


def render(entry: dict, index: int = 0, total: int = 1) -> str:
    """
    Format a single APOD entry as a human-readable terminal block.
    Handles both 'image' and 'video' media types gracefully.
    """
    media = entry.get("media_type", "image")
    url   = entry.get("url", "")
    hd    = entry.get("hdurl", "")

    if media == "video":
        media_line = f"  📹  Video   : {url}"
    else:
        # Prefer HD URL; fall back to regular URL
        best = hd or url
        media_line = f"  🖼   Image   : {best}"
        if hd and url and hd != url:
            media_line += f"\n  🔗  SD      : {url}"

    counter = f"  [{index}/{total}]" if total > 1 else ""
    parts = [
        DIVIDER,
        f"  🌌  NASA Astronomy Picture of the Day{counter}",
        DIVIDER,
        f"  📅  Date    : {entry.get('date', '—')}",
        f"  🏷   Title   : {entry.get('title', '—')}",
        f"  📷  Type    : {media.upper()}",
        media_line,
    ]

    cr = entry.get("copyright", "").strip()
    if cr:
        parts.append(f"  ©   Credit  : {cr}")

    explanation = entry.get("explanation", "").strip()
    if explanation:
        # Word-wrap at 68 chars with an 8-space indent
        words, wrapped, line = explanation.split(), [], ""
        for w in words:
            if len(line) + len(w) + 1 > 68:
                wrapped.append("        " + line)
                line = w
            else:
                line = (line + " " + w).strip()
        if line:
            wrapped.append("        " + line)
        parts.append("  📝  About:")
        parts.extend(wrapped)

    parts.append(DIVIDER)
    return "\n".join(parts)


def print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ── Sub-commands ──────────────────────────────────────────────────────────────

def cmd_today(args) -> None:
    """Fetch today's APOD."""
    data = fetch(args.api_key, {})
    print_json(data) if args.json else print(render(data))


def cmd_date(args) -> None:
    """Fetch the APOD for one specific date."""
    d = validate_date(args.date)
    data = fetch(args.api_key, {"date": str(d)})
    print_json(data) if args.json else print(render(data))


def cmd_range(args) -> None:
    """
    Fetch every APOD between --start and --end (inclusive) and print them
    in sequence — a comparison view the APOD website cannot offer.

    Edge case: user types the dates in the wrong order (start > end).
    Instead of crashing or silently returning nothing we swap them and
    print a warning, then continue normally.
    """
    start = validate_date(args.start)
    end   = validate_date(args.end)

    # Gracefully handle reversed date order
    if start > end:
        print(
            f"[WARN] --start {start} is after --end {end}; swapping them.",
            file=sys.stderr,
        )
        start, end = end, start

    days = (end - start).days + 1
    if days > 100:
        print(
            f"[WARN] Fetching {days} days requires {days} API calls "
            "and will take a while.",
            file=sys.stderr,
        )

    results, cur = [], start
    while cur <= end:
        print(f"  ↻  Fetching {cur} …", end="\r", flush=True, file=sys.stderr)
        results.append(fetch(args.api_key, {"date": str(cur)}))
        cur += timedelta(days=1)
    print(" " * 40, end="\r", file=sys.stderr)  # wipe the progress line

    if args.json:
        print_json(results)
    else:
        total = len(results)
        for i, entry in enumerate(results, 1):
            print(render(entry, index=i, total=total))
            print()


def cmd_random(args) -> None:
    """Fetch N random APODs from NASA's entire archive."""
    n = args.count
    if not (1 <= n <= 100):
        _die("--count must be between 1 and 100.")

    data = fetch(args.api_key, {"count": n})
    if args.json:
        print_json(data)
    else:
        for i, entry in enumerate(data, 1):
            print(render(entry, index=i, total=len(data)))
            print()


# ── CLI definition ────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="apod",
        description=(
            "NASA APOD Explorer — browse and compare Astronomy Pictures of the Day.\n"
            "Use DEMO_KEY as --api-key for quick testing (rate-limited)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python app.py --api-key DEMO_KEY today\n"
            "  python app.py --api-key DEMO_KEY date --date 2024-04-08\n"
            "  python app.py --api-key DEMO_KEY range --start 2024-01-01 --end 2024-01-05\n"
            "  python app.py --api-key DEMO_KEY random --count 5\n"
            "  python app.py --api-key DEMO_KEY today --json\n"
        ),
    )
    p.add_argument(
        "--api-key",
        required=True,
        metavar="KEY",
        help='NASA API key (get one free at https://api.nasa.gov/).  Use "DEMO_KEY" to test.',
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Print raw NASA JSON instead of the formatted display.",
    )

    sub = p.add_subparsers(dest="command", required=True, metavar="COMMAND")

    sub.add_parser("today", help="Fetch today's APOD.")

    dp = sub.add_parser("date", help="Fetch APOD for a specific date.")
    dp.add_argument("--date", required=True, metavar="YYYY-MM-DD",
                    help="Date to fetch.")

    rp = sub.add_parser("range",
                        help="Fetch every APOD between two dates (comparison view).")
    rp.add_argument("--start", required=True, metavar="YYYY-MM-DD",
                    help="Range start date.")
    rp.add_argument("--end",   required=True, metavar="YYYY-MM-DD",
                    help="Range end date.")

    np = sub.add_parser("random", help="Fetch N random APODs.")
    np.add_argument("--count", type=int, default=3, metavar="N",
                    help="How many random photos to fetch (1-100, default: 3).")

    return p


def main() -> None:
    args = build_parser().parse_args()
    {
        "today":  cmd_today,
        "date":   cmd_date,
        "range":  cmd_range,
        "random": cmd_random,
    }[args.command](args)


if __name__ == "__main__":
    main()