#!/usr/bin/env python3
"""
IP VAULT PROTOCOL — Automated Classification & Scoring Engine
Processes notes-data.json into a structured IP Vault database.
"""

import json
import re
import os
from collections import Counter

INPUT = "/Users/19keys/sovereign-empire-sweep/notes-data.json"
OUTPUT = "/Users/19keys/sovereign-empire-sweep/ip-vault.json"

# ═══════════════════════════════════════
# CLASSIFICATION RULES
# ═══════════════════════════════════════

CATEGORY_RULES = {
    # HARD IP
    "FRAMEWORK": {
        "parent": "HARD IP",
        "signals": ["framework", "system", "steps", "pillars", "layers", "levels", "stages",
                     "model", "methodology", "architecture", "stack", "protocol", "structure",
                     "blueprint", "matrix", "map", "hierarchy", "ladder", "spectrum", "cycle"],
        "weight": 3
    },
    "COINED TERM": {
        "parent": "HARD IP",
        "signals": ["cognition key", "mental sovereignty", "dynasty", "supermind",
                     "crownz", "high level conversations", "save yourself", "sovereign",
                     "frequency", "cognitive architecture", "vanta black"],
        "weight": 2
    },
    "SIGNATURE PHRASE": {
        "parent": "HARD IP",
        "signals": ["your frequency", "build the dynasty", "save yourself",
                     "sovereign mind", "the key is", "unlock", "activate",
                     "level up", "reprogram", "decode"],
        "weight": 2
    },
    "ORIGINAL THEORY": {
        "parent": "HARD IP",
        "signals": ["theory", "hypothesis", "because", "the reason", "what if",
                     "i believe", "my thesis", "the truth is", "most people don't realize",
                     "here's what's really happening", "the connection between"],
        "weight": 2
    },

    # SOFT IP
    "CONCEPT SEED": {
        "parent": "SOFT IP",
        "signals": ["idea", "thought", "consider", "imagine", "concept", "notion"],
        "weight": 1
    },
    "INSIGHT": {
        "parent": "SOFT IP",
        "signals": ["realize", "insight", "the key", "understand", "clarity",
                     "revelation", "aha", "it hit me", "i see now", "the problem is",
                     "people don't", "most people"],
        "weight": 1
    },
    "METAPHOR": {
        "parent": "SOFT IP",
        "signals": ["like a", "is like", "think of it as", "imagine", "metaphor",
                     "analogy", "picture this", "it's the same as", "mirror"],
        "weight": 1
    },

    # EXECUTABLE IDEAS
    "CONTENT IDEA": {
        "parent": "EXECUTABLE",
        "signals": ["episode", "podcast", "video", "content", "topic", "thumbnail",
                     "title", "series", "season", "show", "reel", "clip", "interview"],
        "weight": 2
    },
    "PRODUCT IDEA": {
        "parent": "EXECUTABLE",
        "signals": ["product", "course", "program", "app", "membership", "subscription",
                     "offering", "package", "bundle", "launch", "release", "curriculum"],
        "weight": 2
    },
    "BUSINESS IDEA": {
        "parent": "EXECUTABLE",
        "signals": ["business", "company", "revenue", "monetize", "license", "brand",
                     "venture", "startup", "enterprise", "llc", "inc", "partnership"],
        "weight": 2
    },
    "EVENT IDEA": {
        "parent": "EXECUTABLE",
        "signals": ["event", "summit", "tour", "conference", "gathering", "meetup",
                     "workshop", "retreat", "ceremony", "festival", "live"],
        "weight": 2
    },
    "PARTNERSHIP": {
        "parent": "EXECUTABLE",
        "signals": ["partner", "collab", "sponsor", "deal", "proposal", "pitch",
                     "negotiate", "contract", "agreement", "co-create"],
        "weight": 2
    },

    # PREDICTIONS
    "PREDICTION": {
        "parent": "PREDICTIONS",
        "signals": ["will happen", "by 2025", "by 2026", "by 2027", "by 2028", "by 2030",
                     "predict", "forecast", "the future", "in 5 years", "in 10 years",
                     "watch", "mark my words", "calling it now", "coming soon",
                     "the next", "shift is coming", "inevitable"],
        "weight": 2
    },

    # CREATIVE WORKS
    "POEM": {
        "parent": "CREATIVE",
        "signals": ["poem", "verse", "stanza", "rhyme", "spoken word"],
        "weight": 1
    },
    "BOOK DRAFT": {
        "parent": "CREATIVE",
        "signals": ["chapter", "book", "manuscript", "draft", "prologue", "epilogue",
                     "introduction", "foreword", "page"],
        "weight": 2
    },

    # RESEARCH
    "DATA/RESEARCH": {
        "parent": "RESEARCH",
        "signals": ["study", "research", "data", "statistic", "percent", "survey",
                     "published", "journal", "university", "found that", "according to"],
        "weight": 1
    },
    "HISTORICAL": {
        "parent": "RESEARCH",
        "signals": ["history", "historical", "ancient", "civilization", "empire",
                     "dynasty", "moors", "egypt", "africa", "ancestor", "legacy",
                     "colonial", "slavery", "liberation"],
        "weight": 1
    },

    # PERSONAL/STRATEGIC
    "STRATEGY": {
        "parent": "STRATEGIC",
        "signals": ["strategy", "plan", "goal", "target", "milestone", "kpi",
                     "roadmap", "pipeline", "funnel", "conversion", "growth",
                     "scale", "audience", "followers", "email list"],
        "weight": 2
    },
    "JOURNAL": {
        "parent": "STRATEGIC",
        "signals": ["i feel", "today i", "reflecting", "journal", "grateful",
                     "lesson", "learned", "realized", "processing", "growth"],
        "weight": 1
    },
}

# Brand detection
BRAND_TAGS = {
    "#HLC": ["hlc", "high level conversations", "high level", "podcast", "episode", "season"],
    "#CognitionKey": ["cognition key", "cognition", "cognitive", "19 keys to cognition"],
    "#DynastyClub": ["dynasty club", "dynasty", "club"],
    "#Supermind": ["supermind", "superman coffee", "wellness", "nootropic"],
    "#SaveYourself": ["save yourself", "save yourself tour", "tour"],
    "#19KeysBrand": ["19keys", "19 keys", "jibrial", "brand equity"],
    "#Crownz": ["crownz", "crown", "crowns"],
}

# Topic detection
TOPIC_TAGS = {
    "#Consciousness": ["consciousness", "cognition", "mind", "awareness", "frequency", "vibration", "meditation", "mental"],
    "#Economics": ["money", "wealth", "economic", "financial", "invest", "capital", "income", "revenue", "million", "billion"],
    "#Culture": ["culture", "community", "black", "identity", "race", "society", "people", "movement"],
    "#Technology": ["ai", "artificial intelligence", "tech", "digital", "algorithm", "crypto", "blockchain", "platform"],
    "#Health": ["health", "wellness", "body", "nutrition", "fitness", "coffee", "supplement", "gut"],
    "#Spirituality": ["spirit", "soul", "god", "divine", "energy", "cosmic", "prayer", "faith", "universe", "creator"],
    "#History": ["history", "ancient", "ancestor", "moor", "egypt", "africa", "civilization", "colonial"],
    "#Psychology": ["psychology", "mindset", "trauma", "behavior", "pattern", "belief", "reprogram", "subconscious"],
    "#Politics": ["politic", "government", "policy", "trump", "democrat", "republican", "power", "governance", "ice"],
    "#Relationships": ["relationship", "love", "family", "marriage", "partner", "men", "women", "masculine", "feminine"],
    "#Education": ["education", "school", "teach", "learn", "curriculum", "student", "knowledge"],
    "#Media": ["media", "content", "platform", "youtube", "instagram", "twitter", "tiktok", "algorithm", "viral"],
    "#Leadership": ["leader", "leadership", "authority", "vision", "mentor", "guide", "influence"],
}

# Format detection
FORMAT_TAGS = {
    "#PodcastEpisode": ["episode", "podcast", "hlc", "conversation"],
    "#BookChapter": ["chapter", "book", "manuscript", "cognition key"],
    "#CourseModule": ["course", "module", "lesson", "curriculum", "workshop"],
    "#SocialPost": ["post", "caption", "tweet", "thread"],
    "#Speech": ["speech", "keynote", "stage", "audience", "crowd"],
    "#ShortForm": ["reel", "short", "tiktok", "clip", "60 second"],
}

# Special tag detection
SPECIAL_SIGNALS = {
    "#Quotable": lambda t: len(t) < 200 and any(w in t for w in ["is", "the", "your", "every", "never", "always"]),
    "#Controversial": lambda t: any(w in t for w in ["controversial", "debate", "disagree", "unpopular", "the truth they", "won't tell you"]),
    "#EvidenceBacked": lambda t: any(w in t for w in ["study", "research", "data", "percent", "university", "published"]),
    "#Flagship": lambda t: any(w in t for w in ["cognition key", "high level conversations", "19keys", "supermind", "dynasty"]),
    "#NeedsDev": lambda t: len(t) < 80,
}


def classify_note(text):
    """Classify a note into primary and secondary categories."""
    text_lower = text.lower()
    scores = {}

    for cat, rules in CATEGORY_RULES.items():
        score = 0
        for signal in rules["signals"]:
            if signal in text_lower:
                score += rules["weight"]
        scores[cat] = score

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = ranked[0] if ranked[0][1] > 0 else ("CONCEPT SEED", 0)
    secondary = [r for r in ranked[1:3] if r[1] > 0]

    return {
        "primary": primary[0],
        "parent": CATEGORY_RULES.get(primary[0], {}).get("parent", "SOFT IP"),
        "secondary": [s[0] for s in secondary],
        "confidence": primary[1]
    }


def score_note(text, classification):
    """Score a note on 5 dimensions (1-5 each)."""
    text_lower = text.lower()
    text_len = len(text)

    # ORIGINALITY (1-5)
    originality = 2
    original_signals = ["cognition key", "19keys", "supermind", "crownz", "dynasty",
                        "sovereign", "frequency", "cognitive architecture", "mental sovereignty",
                        "high level", "framework", "paradigm"]
    orig_hits = sum(1 for s in original_signals if s in text_lower)
    if orig_hits >= 3:
        originality = 5
    elif orig_hits >= 2:
        originality = 4
    elif orig_hits >= 1:
        originality = 3

    if classification["parent"] == "HARD IP":
        originality = max(originality, 4)

    # COMMERCIAL POTENTIAL (1-5)
    commercial = 2
    commercial_signals = ["course", "product", "license", "sell", "revenue", "monetize",
                          "program", "membership", "launch", "price", "offer", "framework",
                          "brand", "partnership", "deal", "sponsor", "curriculum"]
    comm_hits = sum(1 for s in commercial_signals if s in text_lower)
    if comm_hits >= 3:
        commercial = 5
    elif comm_hits >= 2:
        commercial = 4
    elif comm_hits >= 1:
        commercial = 3

    if classification["primary"] in ["FRAMEWORK", "PRODUCT IDEA", "BUSINESS IDEA"]:
        commercial = max(commercial, 4)
    if classification["primary"] in ["COINED TERM", "SIGNATURE PHRASE"]:
        commercial = max(commercial, 3)

    # CULTURAL IMPACT (1-5)
    cultural = 2
    cultural_signals = ["movement", "culture", "generation", "community", "people",
                        "consciousness", "awaken", "shift", "revolution", "liberation",
                        "freedom", "sovereignty", "black", "diaspora", "nation"]
    cult_hits = sum(1 for s in cultural_signals if s in text_lower)
    if cult_hits >= 4:
        cultural = 5
    elif cult_hits >= 3:
        cultural = 4
    elif cult_hits >= 2:
        cultural = 3
    elif cult_hits >= 1:
        cultural = max(cultural, 2)

    # DEVELOPMENT STAGE (1-5)
    if text_len < 50:
        dev_stage = 1
    elif text_len < 100:
        dev_stage = 2
    elif text_len < 250:
        dev_stage = 3
    elif text_len < 400:
        dev_stage = 4
    else:
        dev_stage = 5

    # Boost if structured
    if any(marker in text for marker in ["1.", "2.", "3.", "- ", "•", "Step", "Phase"]):
        dev_stage = min(dev_stage + 1, 5)

    # STRATEGIC ALIGNMENT (1-5)
    alignment = 2
    brand_hits = 0
    for signals in BRAND_TAGS.values():
        if any(s in text_lower for s in signals):
            brand_hits += 1
    if brand_hits >= 3:
        alignment = 5
    elif brand_hits >= 2:
        alignment = 4
    elif brand_hits >= 1:
        alignment = 3

    if any(w in text_lower for w in ["cognition key", "high level conversations", "supermind"]):
        alignment = max(alignment, 4)

    return {
        "originality": originality,
        "commercial": commercial,
        "cultural_impact": cultural,
        "dev_stage": dev_stage,
        "strategic_alignment": alignment,
        "composite": originality + commercial + cultural + dev_stage + alignment
    }


def get_priority(composite):
    if composite >= 21:
        return {"label": "CRITICAL", "emoji": "🔴", "level": 5}
    elif composite >= 16:
        return {"label": "HIGH", "emoji": "🟠", "level": 4}
    elif composite >= 11:
        return {"label": "MEDIUM", "emoji": "🟡", "level": 3}
    elif composite >= 6:
        return {"label": "LOW", "emoji": "🟢", "level": 2}
    else:
        return {"label": "ARCHIVE", "emoji": "⚪", "level": 1}


def detect_tags(text):
    text_lower = text.lower()
    tags = {"brand": [], "topic": [], "format": [], "special": []}

    for tag, signals in BRAND_TAGS.items():
        if any(s in text_lower for s in signals):
            tags["brand"].append(tag)

    for tag, signals in TOPIC_TAGS.items():
        if any(s in text_lower for s in signals):
            tags["topic"].append(tag)

    for tag, signals in FORMAT_TAGS.items():
        if any(s in text_lower for s in signals):
            tags["format"].append(tag)

    for tag, check_fn in SPECIAL_SIGNALS.items():
        if check_fn(text_lower):
            tags["special"].append(tag)

    return tags


def generate_ip_assessment(note, classification, scores, tags):
    """Generate a brief IP assessment."""
    text_lower = note["preview"].lower()

    if classification["parent"] == "HARD IP":
        if classification["primary"] == "FRAMEWORK":
            return "Ownable framework IP — develop into proprietary system for course/book licensing."
        elif classification["primary"] == "COINED TERM":
            return "Brandable coined term — consider trademark registration and consistent deployment across content."
        elif classification["primary"] == "SIGNATURE PHRASE":
            return "Quotable signature phrase — deploy across social, merch, and stage appearances."
        elif classification["primary"] == "ORIGINAL THEORY":
            return "Original theory — validate with evidence and position as thought leadership cornerstone."
        else:
            return "Hard IP asset — protect, develop, and integrate into brand ecosystem."

    elif classification["parent"] == "EXECUTABLE":
        if classification["primary"] == "CONTENT IDEA":
            return "Content pipeline material — schedule for production and cross-promote across platforms."
        elif classification["primary"] == "PRODUCT IDEA":
            return "Product concept — validate market demand, build MVP, and integrate with existing funnels."
        elif classification["primary"] == "BUSINESS IDEA":
            return "Business opportunity — analyze revenue model, competitive landscape, and resource requirements."
        elif classification["primary"] == "EVENT IDEA":
            return "Event concept — scope logistics, sponsorship potential, and audience size targets."
        elif classification["primary"] == "PARTNERSHIP":
            return "Partnership opportunity — evaluate alignment, terms, and strategic value."
        else:
            return "Executable idea — prioritize based on current capacity and strategic alignment."

    elif classification["parent"] == "PREDICTIONS":
        return "Prediction asset — timestamp and archive. If validated, becomes powerful authority proof."

    elif classification["parent"] == "CREATIVE":
        return "Creative IP — refine for publication, performance, or integration into brand content."

    elif classification["parent"] == "RESEARCH":
        return "Research asset — catalog for use as supporting evidence in frameworks, content, and courses."

    elif classification["parent"] == "STRATEGIC":
        return "Strategic note — extract actionable items and align with current operational priorities."

    else:
        return "Soft IP — develop further to unlock commercial and cultural potential."


def process_all_notes():
    """Process all notes through the IP Vault Protocol."""
    print("Loading notes data...", flush=True)
    with open(INPUT) as f:
        data = json.load(f)

    # Build unique note list across all keywords
    note_map = {}
    for kw, notes in data["results"].items():
        for note in notes:
            nid = note["name"]
            if nid not in note_map:
                note_map[nid] = {**note, "matched_keywords": [kw]}
            else:
                if kw not in note_map[nid]["matched_keywords"]:
                    note_map[nid]["matched_keywords"].append(kw)

    all_notes = list(note_map.values())
    print(f"Processing {len(all_notes)} unique notes...", flush=True)

    vault = []
    stats = {
        "total": len(all_notes),
        "by_parent": Counter(),
        "by_category": Counter(),
        "by_priority": Counter(),
        "by_brand": Counter(),
        "by_topic": Counter(),
        "critical_notes": [],
        "high_notes": [],
        "hard_ip_count": 0,
        "framework_embryos": [],
        "theme_clusters": {},
    }

    for i, note in enumerate(all_notes):
        text = note["preview"]
        classification = classify_note(text)
        scores = score_note(text, classification)
        priority = get_priority(scores["composite"])
        tags = detect_tags(text)
        assessment = generate_ip_assessment(note, classification, scores, tags)

        entry = {
            "id": i + 1,
            "name": note["name"],
            "date": note["date"],
            "preview": text,
            "matched_keywords": note["matched_keywords"],
            "classification": classification,
            "scores": scores,
            "priority": priority,
            "tags": tags,
            "ip_assessment": assessment,
        }

        vault.append(entry)

        # Stats
        stats["by_parent"][classification["parent"]] += 1
        stats["by_category"][classification["primary"]] += 1
        stats["by_priority"][priority["label"]] += 1

        for t in tags["brand"]:
            stats["by_brand"][t] += 1
        for t in tags["topic"]:
            stats["by_topic"][t] += 1

        if classification["parent"] == "HARD IP":
            stats["hard_ip_count"] += 1

        if priority["label"] == "CRITICAL":
            stats["critical_notes"].append({"id": i+1, "name": note["name"], "score": scores["composite"]})
        elif priority["label"] == "HIGH":
            stats["high_notes"].append({"id": i+1, "name": note["name"], "score": scores["composite"]})

    # Sort critical/high by score descending
    stats["critical_notes"].sort(key=lambda x: x["score"], reverse=True)
    stats["high_notes"].sort(key=lambda x: x["score"], reverse=True)

    # Detect theme clusters from topic tags
    topic_notes = {}
    for entry in vault:
        for t in entry["tags"]["topic"]:
            if t not in topic_notes:
                topic_notes[t] = []
            topic_notes[t].append(entry["id"])
    stats["theme_clusters"] = {k: {"count": len(v), "note_ids": v[:20]} for k, v in topic_notes.items()}

    # Detect framework embryos (notes with FRAMEWORK classification + high scores)
    framework_notes = [e for e in vault if e["classification"]["primary"] == "FRAMEWORK"]
    stats["framework_embryos"] = [
        {"id": n["id"], "name": n["name"], "score": n["scores"]["composite"]}
        for n in sorted(framework_notes, key=lambda x: x["scores"]["composite"], reverse=True)[:20]
    ]

    # Sort vault by composite score descending
    vault.sort(key=lambda x: x["scores"]["composite"], reverse=True)

    output = {
        "vault": vault,
        "stats": {
            "total": stats["total"],
            "hard_ip_count": stats["hard_ip_count"],
            "by_parent": dict(stats["by_parent"]),
            "by_category": dict(stats["by_category"]),
            "by_priority": dict(stats["by_priority"]),
            "by_brand": dict(stats["by_brand"]),
            "by_topic": dict(stats["by_topic"]),
            "critical_notes": stats["critical_notes"][:25],
            "high_notes": stats["high_notes"][:50],
            "framework_embryos": stats["framework_embryos"],
            "theme_clusters": stats["theme_clusters"],
        }
    }

    print(f"Writing IP Vault ({len(vault)} entries)...", flush=True)
    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 60)
    print("IP VAULT PROTOCOL — PROCESSING COMPLETE")
    print("=" * 60)
    print(f"\nTotal Notes Processed: {stats['total']}")
    print(f"Hard IP Identified: {stats['hard_ip_count']}")
    print(f"\nPRIORITY DISTRIBUTION:")
    for p in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "ARCHIVE"]:
        count = stats["by_priority"].get(p, 0)
        print(f"  {p:12s}  {count:4d}")
    print(f"\nCATEGORY PARENTS:")
    for parent, count in stats["by_parent"].most_common():
        print(f"  {parent:15s}  {count:4d}")
    print(f"\nTOP BRAND TAGS:")
    for tag, count in stats["by_brand"].most_common(7):
        print(f"  {tag:20s}  {count:4d}")
    print(f"\nTOP TOPIC TAGS:")
    for tag, count in stats["by_topic"].most_common(10):
        print(f"  {tag:20s}  {count:4d}")
    print(f"\nFRAMEWORK EMBRYOS: {len(stats['framework_embryos'])}")
    print(f"CRITICAL PRIORITY NOTES: {len(stats['critical_notes'])}")
    print(f"\nOutput: {OUTPUT}")


if __name__ == "__main__":
    process_all_notes()
