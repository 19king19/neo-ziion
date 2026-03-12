#!/usr/bin/env python3
"""
Sovereign Empire — Apple Notes Intelligence Sweep
Outputs structured JSON for dashboard consumption.
"""

import subprocess
import json
import os
import time

OUTPUT_DIR = "/Users/19keys/sovereign-empire-sweep"
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "notes-data.json")

KEYWORDS = [
    "framework", "cognition", "key", "paradigm", "sovereign",
    "19keys", "mastery", "high level", "crownz", "supermind"
]

def run_applescript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=300
    )
    return result.stdout.strip()

def get_note_count():
    script = 'tell application "Notes" to return count of every note'
    return int(run_applescript(script))

def get_note_batch(start, batch_size):
    script = f'''
    tell application "Notes"
        set noteList to every note
        set totalNotes to count of noteList
        set endIdx to {start} + {batch_size} - 1
        if endIdx > totalNotes then set endIdx to totalNotes
        set output to ""
        repeat with i from {start} to endIdx
            set aNote to item i of noteList
            try
                set noteName to name of aNote
                set noteDate to modification date of aNote as text
                set noteBody to plaintext of aNote
                set tid to AppleScript's text item delimiters
                set AppleScript's text item delimiters to tab
                set noteBody to text items of noteBody
                set AppleScript's text item delimiters to " "
                set noteBody to noteBody as text
                set AppleScript's text item delimiters to return
                set noteBody to text items of noteBody
                set AppleScript's text item delimiters to " "
                set noteBody to noteBody as text
                set AppleScript's text item delimiters to tid
                set output to output & "NOTE_START|" & noteName & "|" & noteDate & "|" & noteBody & "|NOTE_END" & linefeed
            end try
        end repeat
        return output
    end tell
    '''
    return run_applescript(script)

def search_batch(raw_text, keywords):
    matches = {kw: [] for kw in keywords}
    notes = raw_text.split("NOTE_END")
    for note_raw in notes:
        note_raw = note_raw.strip()
        if not note_raw.startswith("NOTE_START|"):
            continue
        parts = note_raw.split("|", 3)
        if len(parts) < 4:
            continue
        _, name, date, body = parts[0], parts[1], parts[2], parts[3]
        body_lower = body.lower()
        name_lower = name.lower()
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in body_lower or kw_lower in name_lower:
                preview = body[:500].strip()
                matches[kw].append({
                    "name": name,
                    "date": date,
                    "preview": preview
                })
    return matches

def main():
    print("SOVEREIGN EMPIRE — NOTES SCAN TO JSON", flush=True)
    total = get_note_count()
    print(f"Total notes: {total}", flush=True)

    all_matches = {kw: [] for kw in KEYWORDS}
    batch_size = 100
    processed = 0
    start_time = time.time()

    for batch_start in range(1, total + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, total)
        print(f"Scanning {batch_start}-{batch_end} / {total}...", flush=True)
        try:
            raw = get_note_batch(batch_start, batch_size)
            batch_matches = search_batch(raw, KEYWORDS)
            for kw in KEYWORDS:
                all_matches[kw].extend(batch_matches[kw])
            processed = batch_end
        except subprocess.TimeoutExpired:
            for sub_start in range(batch_start, batch_end + 1, 25):
                sub_end = min(sub_start + 24, batch_end)
                try:
                    raw = get_note_batch(sub_start, 25)
                    batch_matches = search_batch(raw, KEYWORDS)
                    for kw in KEYWORDS:
                        all_matches[kw].extend(batch_matches[kw])
                    processed = sub_end
                except Exception as e:
                    print(f"  Error {sub_start}-{sub_end}: {e}")
        except Exception as e:
            print(f"  Error {batch_start}-{batch_end}: {e}")

        # Write incremental JSON every 500 notes so dashboard can show progress
        if processed % 500 == 0 or processed >= total:
            _write_json(all_matches, processed, total, start_time)

    _write_json(all_matches, processed, total, start_time)
    elapsed = time.time() - start_time
    total_hits = sum(len(v) for v in all_matches.values())
    print(f"\nDONE — {total_hits} matches across {processed} notes in {elapsed:.0f}s", flush=True)

def _write_json(all_matches, processed, total, start_time):
    # Deduplicate by note name within each keyword
    deduped = {}
    for kw, notes in all_matches.items():
        seen = set()
        unique = []
        for n in notes:
            if n["name"] not in seen:
                seen.add(n["name"])
                unique.append(n)
        deduped[kw] = unique

    data = {
        "scan": {
            "total_notes": total,
            "scanned": processed,
            "elapsed": round(time.time() - start_time, 1),
            "complete": processed >= total
        },
        "summary": {kw: len(deduped[kw]) for kw in all_matches},
        "total_matches": sum(len(v) for v in deduped.values()),
        "keywords": list(all_matches.keys()),
        "results": deduped
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
