#!/usr/bin/env python3
"""
Sovereign Empire — Apple Notes Intelligence Sweep
Single-pass search: fetches each note once, checks all keywords.
Outputs results to both terminal and file.
"""

import subprocess
import json
import os
import time

OUTPUT_DIR = "/Users/19keys/sovereign-empire-sweep"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "notes-search-results.md")

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
    """Fetch a batch of notes as tab-separated name|body pairs."""
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
                -- Replace tabs and newlines in body for safe transport
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
    """Search a batch of note text for keywords, return matches."""
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
                preview = body[:300].strip()
                matches[kw].append({
                    "name": name,
                    "date": date,
                    "preview": preview
                })
    return matches

def main():
    print("=" * 60)
    print("SOVEREIGN EMPIRE — APPLE NOTES INTELLIGENCE SWEEP")
    print("=" * 60)
    print()

    print("Getting note count...")
    total = get_note_count()
    print(f"Total notes: {total}")
    print()

    all_matches = {kw: [] for kw in KEYWORDS}
    batch_size = 100
    processed = 0

    start_time = time.time()

    for batch_start in range(1, total + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, total)
        print(f"Scanning notes {batch_start}-{batch_end} of {total}...", flush=True)

        try:
            raw = get_note_batch(batch_start, batch_size)
            batch_matches = search_batch(raw, KEYWORDS)

            for kw in KEYWORDS:
                all_matches[kw].extend(batch_matches[kw])

            processed = batch_end
        except subprocess.TimeoutExpired:
            print(f"  Timeout on batch {batch_start}-{batch_end}, retrying with smaller batch...")
            # Retry with smaller batches
            for sub_start in range(batch_start, batch_end + 1, 25):
                sub_end = min(sub_start + 24, batch_end)
                try:
                    raw = get_note_batch(sub_start, 25)
                    batch_matches = search_batch(raw, KEYWORDS)
                    for kw in KEYWORDS:
                        all_matches[kw].extend(batch_matches[kw])
                    processed = sub_end
                except Exception as e:
                    print(f"  Error on {sub_start}-{sub_end}: {e}")
        except Exception as e:
            print(f"  Error on batch {batch_start}-{batch_end}: {e}")

    elapsed = time.time() - start_time

    # Build output
    lines = []
    lines.append("# Sovereign Empire — Apple Notes Intelligence Sweep")
    lines.append("")
    lines.append(f"**Notes scanned:** {processed} / {total}")
    lines.append(f"**Keywords:** {', '.join(KEYWORDS)}")
    lines.append(f"**Scan time:** {elapsed:.1f}s")
    lines.append("")

    total_matches = sum(len(v) for v in all_matches.values())
    lines.append(f"## Summary — {total_matches} total matches")
    lines.append("")
    lines.append("| Keyword | Matches |")
    lines.append("|---------|---------|")
    for kw in KEYWORDS:
        lines.append(f"| {kw} | {len(all_matches[kw])} |")
    lines.append("")

    for kw in KEYWORDS:
        if not all_matches[kw]:
            continue
        lines.append(f"---")
        lines.append(f"## \"{kw}\" — {len(all_matches[kw])} matches")
        lines.append("")

        # Deduplicate by note name
        seen = set()
        for match in all_matches[kw]:
            if match["name"] in seen:
                continue
            seen.add(match["name"])
            lines.append(f"### {match['name']}")
            lines.append(f"*Modified: {match['date']}*")
            lines.append("")
            lines.append(f"> {match['preview']}")
            lines.append("")

    output_text = "\n".join(lines)

    # Write to file
    with open(OUTPUT_FILE, "w") as f:
        f.write(output_text)

    # Print summary to terminal
    print()
    print("=" * 60)
    print(f"SCAN COMPLETE — {total_matches} total matches across {processed} notes")
    print("=" * 60)
    print()
    for kw in KEYWORDS:
        count = len(all_matches[kw])
        bar = "#" * min(count, 40)
        print(f"  {kw:15s} {count:4d}  {bar}")
    print()
    print(f"Full results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
