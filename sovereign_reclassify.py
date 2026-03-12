#!/usr/bin/env python3
"""
IP VAULT — SOVEREIGN RECLASSIFICATION ENGINE
Chairman's Protocol: Ruthless triage, honest scoring, real valuation.
"""

import json
import re
import os
from collections import Counter

INPUT = "/Users/19keys/sovereign-empire-sweep/notes-data.json"
OUTPUT = "/Users/19keys/sovereign-empire-sweep/ip-vault-v2.json"

# ═══════════════════════════════════════
# PHASE 1: TRIAGE — NOISE DETECTION
# ═══════════════════════════════════════

def is_noise(text):
    """Chairman's filter: Would this mean anything to an investor or trademark attorney?"""
    t = text.strip()
    t_lower = t.lower()

    # Fragment — less than 2 substantive sentences
    sentences = [s.strip() for s in re.split(r'[.!?\n]', t) if len(s.strip()) > 10]
    if len(sentences) < 2 and len(t) < 80:
        return True, "FRAGMENT"

    # URL dump — mostly links with no commentary
    urls = re.findall(r'https?://\S+', t)
    non_url_text = re.sub(r'https?://\S+', '', t).strip()
    if urls and len(non_url_text) < 50:
        return True, "DEAD_LINK"

    # Hashtag collection only
    if re.match(r'^[\s#\w]+$', t) and t.count('#') >= 3 and len(t) < 200:
        words_without_hash = re.sub(r'#\w+', '', t).strip()
        if len(words_without_hash) < 30:
            return True, "NOISE"

    # Pure scheduling / logistics
    logistics_signals = [
        "waiting on", "schedule", "follow up", "call with", "meeting at",
        "remind me to", "to do:", "todo:", "checklist", "need to call",
        "send email to", "waiting for response", "booked for"
    ]
    logistics_hits = sum(1 for s in logistics_signals if s in t_lower)
    # Only flag as noise if it's PREDOMINANTLY logistics with no ideas
    if logistics_hits >= 2 and len(t) < 200:
        return True, "OPERATIONS"

    # Raw contact info / leads
    contact_signals = ["phone:", "email:", "address:", "@gmail", "@yahoo",
                       "cell:", "office:", "ext.", "contact info"]
    if sum(1 for s in contact_signals if s in t_lower) >= 2:
        return True, "OPERATIONS"

    # Price list / rate card with no strategic context
    price_signals = ["fee", "rate", "price", "cost", "invoice", "payment"]
    price_hits = sum(1 for s in price_signals if s in t_lower)
    idea_signals = ["because", "framework", "system", "strategy", "the key",
                    "principle", "concept", "theory", "insight", "i believe"]
    idea_hits = sum(1 for s in idea_signals if s in t_lower)
    if price_hits >= 3 and idea_hits == 0 and len(t) < 300:
        return True, "OPERATIONS"

    return False, None


def detect_mixed_content(text):
    """Detect if a note mixes real IP with noise (CRM data, bios, etc.)."""
    t_lower = text.lower()
    flags = []

    # Bio paste detection
    bio_markers = [
        "19keys is a visionary",
        "cultural architect",
        "co-founder of supermind",
        "one of the most influential",
        "independent media networks",
        "high level conversations and"
    ]
    if sum(1 for b in bio_markers if b in t_lower) >= 3:
        flags.append("CONTAINS_BIO_PASTE")

    # CRM data mixed in
    crm_markers = ["lead", "friend and family", "consulting fee", "transaction fee",
                   "carry fee", "open another"]
    if sum(1 for c in crm_markers if c in t_lower) >= 2:
        flags.append("CONTAINS_CRM_DATA")

    return flags


# ═══════════════════════════════════════
# PHASE 2: TIER CLASSIFICATION
# ═══════════════════════════════════════

def classify_tier(text, name):
    """Assign tier 1-6 with proper category. Chairman's standards."""
    t = text.strip()
    t_lower = t.lower()
    name_lower = name.lower()

    # ---- TIER 1: HARD IP ----
    # Must be: original to 19Keys + protectable + commercial application

    # COINED TERM: A specific invented word/phrase naming an original concept
    # Must be a discrete nameable term WITH its definition/methodology
    coined_candidates = [
        "formulaize", "keyism", "cognitive wealth", "mental sovereignty",
        "cognition key", "the cognitive wealth key", "supermind",
        "dynasty architecture", "sovereign mind", "cognitive architecture",
        "people are non-fungible", "non-fungible people"
    ]
    has_coined = any(c in t_lower for c in coined_candidates)
    has_definition = any(w in t_lower for w in [
        "means", "defined as", "is when", "refers to", "the concept of",
        "methodology", "this is", "i define", "what i mean by"
    ])
    has_structure = any(w in t_lower for w in [
        "step 1", "step 2", "pillar", "layer", "level", "dimension",
        "component", "phase 1", "phase 2", "stage 1", "stage 2",
        "1.", "2.", "3.", "first,", "second,", "third,"
    ])

    # ORIGINAL FRAMEWORK: Multi-step system with clear components
    framework_signals = [
        "framework", "system", "model", "methodology", "protocol",
        "architecture", "blueprint", "matrix", "stack", "assessment"
    ]
    has_framework_word = any(f in t_lower for f in framework_signals)

    # Does it actually DEFINE the framework (not just mention it)?
    defines_framework = has_framework_word and has_structure and len(t) > 200

    # ORIGINAL THEORY: Clear thesis statement
    theory_signals = [
        "i believe", "my thesis", "the truth is", "most people don't realize",
        "here's what's really happening", "the real reason", "what nobody sees",
        "the fundamental problem", "the key insight", "the paradigm shift"
    ]
    has_theory = any(ts in t_lower for ts in theory_signals) and len(t) > 150

    # SIGNATURE PHRASE: Memorable, quotable, ownable
    # Must be specific and philosophical, not generic motivation
    generic_motivation = [
        "level up", "grind", "hustle", "boss up", "stay focused",
        "never give up", "believe in yourself", "work hard"
    ]
    is_generic = any(g in t_lower for g in generic_motivation) and not has_coined

    # Check for quotable original statements
    is_short_powerful = len(t) < 200 and len(t) > 20 and not is_generic
    has_philosophical_weight = any(w in t_lower for w in [
        "sovereignty", "consciousness", "frequency", "paradigm", "cognition",
        "non-fungible", "the mind is", "your mind", "the government of",
        "stateless nation", "cognitive", "dynasty", "sovereign"
    ])
    is_signature = is_short_powerful and has_philosophical_weight and not is_noise(t)[0]

    # PROPRIETARY METHODOLOGY: Specific process that could be licensed
    methodology_signals = [
        "assessment", "diagnostic", "certification", "evaluation",
        "methodology", "process", "technique", "protocol"
    ]
    has_methodology = any(m in t_lower for m in methodology_signals) and has_structure

    # --- TIER 1 DECISION ---
    if defines_framework:
        return 1, "HARD IP", "ORIGINAL FRAMEWORK"
    if has_coined and (has_definition or len(t) > 150) and not is_noise(t)[0]:
        return 1, "HARD IP", "COINED TERM"
    if has_methodology and len(t) > 200:
        return 1, "HARD IP", "PROPRIETARY METHODOLOGY"
    if has_theory and len(t) > 200:
        return 1, "HARD IP", "ORIGINAL THEORY"
    if is_signature:
        return 1, "HARD IP", "SIGNATURE PHRASE"

    # ---- TIER 2: EXECUTABLE IP ----
    # Deployable assets — structured enough to act on

    content_blueprint = any(w in t_lower for w in [
        "episode outline", "script", "video concept", "series concept",
        "content plan", "show outline", "episode:", "topic:"
    ]) and len(t) > 150

    product_design = any(w in t_lower for w in [
        "course", "program", "membership", "curriculum", "module",
        "offering", "product", "subscription"
    ]) and any(w in t_lower for w in [
        "target", "audience", "price", "deliver", "format", "launch",
        "module", "lesson", "week 1", "week 2"
    ]) and len(t) > 150

    business_model = any(w in t_lower for w in [
        "revenue", "monetize", "business model", "pricing", "funnel",
        "licensing", "franchise", "equity", "valuation"
    ]) and len(t) > 150

    event_concept = any(w in t_lower for w in [
        "summit", "conference", "tour", "event", "gathering", "retreat"
    ]) and any(w in t_lower for w in [
        "format", "agenda", "speaker", "venue", "ticket", "program",
        "schedule", "day 1", "day 2", "session"
    ]) and len(t) > 150

    partnership_strat = any(w in t_lower for w in [
        "partnership", "collaborate", "co-create", "joint venture",
        "sponsor", "deal", "proposal"
    ]) and any(w in t_lower for w in [
        "value", "mutual", "terms", "deliverable", "scope"
    ]) and len(t) > 100

    campaign = any(w in t_lower for w in [
        "campaign", "launch", "movement", "initiative", "challenge"
    ]) and any(w in t_lower for w in [
        "channel", "audience", "goal", "timeline", "phase"
    ]) and len(t) > 150

    if content_blueprint:
        return 2, "EXECUTABLE IP", "CONTENT BLUEPRINT"
    if product_design:
        return 2, "EXECUTABLE IP", "PRODUCT DESIGN"
    if business_model:
        return 2, "EXECUTABLE IP", "BUSINESS MODEL"
    if event_concept:
        return 2, "EXECUTABLE IP", "EVENT CONCEPT"
    if partnership_strat:
        return 2, "EXECUTABLE IP", "PARTNERSHIP STRATEGY"
    if campaign:
        return 2, "EXECUTABLE IP", "CAMPAIGN CONCEPT"

    # Catch broader executable content
    has_exec_signals = any(w in t_lower for w in [
        "episode", "podcast", "content", "launch", "build", "create",
        "course", "product", "event", "partnership", "deal", "tour"
    ])
    has_exec_structure = len(t) > 200 and (has_structure or "•" in t or "- " in t)
    if has_exec_signals and has_exec_structure:
        return 2, "EXECUTABLE IP", "CONTENT BLUEPRINT"

    # ---- TIER 3: STRATEGIC INTELLIGENCE ----
    market_thesis = any(w in t_lower for w in [
        "predict", "forecast", "by 2025", "by 2026", "by 2027", "by 2028",
        "by 2030", "the future", "will happen", "shift is coming",
        "mark my words", "in 5 years", "in 10 years", "the next wave",
        "watch what happens", "calling it"
    ]) and len(t) > 80

    competitive_insight = any(w in t_lower for w in [
        "competitor", "landscape", "positioning", "market", "niche",
        "industry", "vs", "compared to", "advantage", "differentiat"
    ]) and len(t) > 100

    audience_insight = any(w in t_lower for w in [
        "audience", "community", "followers", "listener", "viewer",
        "demographic", "psychographic", "customer", "they want", "they need"
    ]) and any(w in t_lower for w in [
        "insight", "realize", "understand", "psychology", "behavior",
        "pattern", "need", "desire", "pain point"
    ]) and len(t) > 100

    strategic_memo = any(w in t_lower for w in [
        "strategy", "roadmap", "plan", "priority", "focus",
        "pivot", "direction", "next quarter", "this year"
    ]) and len(t) > 150

    # General insight/observation with substance
    has_insight = any(w in t_lower for w in [
        "the problem is", "most people", "the reason", "i realized",
        "the difference between", "what most miss", "the real", "the truth"
    ]) and len(t) > 100

    if market_thesis:
        return 3, "STRATEGIC INTELLIGENCE", "MARKET THESIS"
    if competitive_insight:
        return 3, "STRATEGIC INTELLIGENCE", "COMPETITIVE INSIGHT"
    if audience_insight:
        return 3, "STRATEGIC INTELLIGENCE", "AUDIENCE INSIGHT"
    if strategic_memo:
        return 3, "STRATEGIC INTELLIGENCE", "STRATEGIC MEMO"
    if has_insight:
        return 3, "STRATEGIC INTELLIGENCE", "STRATEGIC MEMO"

    # ---- TIER 4: CREATIVE ASSETS ----
    book_draft = any(w in t_lower for w in [
        "chapter", "manuscript", "book", "prologue", "epilogue"
    ]) and len(t) > 200

    poem_spoken = any(w in t_lower for w in [
        "poem", "verse", "spoken word"
    ]) or (len(t) < 300 and t.count('\n') > 5 and not has_structure)

    manifesto = any(w in t_lower for w in [
        "manifesto", "declaration", "principles", "we believe", "i declare",
        "our mission", "our vision", "we stand for"
    ]) and len(t) > 150

    if book_draft:
        return 4, "CREATIVE ASSETS", "BOOK DRAFT"
    if manifesto:
        return 4, "CREATIVE ASSETS", "MANIFESTO"
    if poem_spoken and len(t) > 50:
        return 4, "CREATIVE ASSETS", "POEM / SPOKEN WORD"

    # ---- TIER 5: RAW MATERIAL ----
    # Has some substance but not developed enough
    has_any_substance = len(t) > 80 and any(w in t_lower for w in [
        "idea", "thought", "concept", "consider", "what if", "maybe",
        "could", "should", "opportunity", "potential", "interesting",
        "note to self", "remember", "explore", "research", "look into"
    ])

    has_research = any(w in t_lower for w in [
        "study", "research", "data", "statistic", "according to",
        "published", "journal", "found that", "source:", "reference"
    ])

    is_journal = any(w in t_lower for w in [
        "i feel", "today i", "reflecting", "grateful", "lesson learned",
        "processing", "journey"
    ])

    if has_research:
        return 5, "RAW MATERIAL", "RESEARCH NOTE"
    if is_journal:
        return 5, "RAW MATERIAL", "JOURNAL ENTRY"
    if has_any_substance:
        return 5, "RAW MATERIAL", "CONCEPT SEED"

    # If it has reasonable length but didn't match anything specific
    if len(t) > 150:
        # Check if it's a transcript (common pattern)
        transcript_signals = ["um,", "uh,", "you know,", "i mean,", "like,",
                              "right?", "yeah,", "man,", "bro,"]
        is_transcript = sum(1 for s in transcript_signals if s in t_lower) >= 3
        if is_transcript:
            return 5, "RAW MATERIAL", "TRANSCRIPT"
        return 5, "RAW MATERIAL", "CONCEPT SEED"

    if len(t) > 50:
        return 5, "RAW MATERIAL", "CONCEPT SEED"

    # ---- TIER 6: NOISE ----
    return 6, "NOISE", "FRAGMENT"


# ═══════════════════════════════════════
# PHASE 3: SCORING (Chairman's Standards)
# ═══════════════════════════════════════

def score_note(text, tier, tier_label, category):
    """Score with integrity. Target average: 11-13/25."""
    if tier >= 5:
        # Tier 5-6 don't get full scores
        return {
            "originality": 1, "commercial_value": 1, "cultural_weight": 1,
            "development_stage": 1, "brand_alignment": 1, "composite": 5
        }

    t_lower = text.lower()
    text_len = len(text)

    # ORIGINALITY (1-5)
    # 5 = concept literally cannot be found attributed to anyone else
    originality = 2  # baseline: most things have moderate originality

    truly_original = [
        "cognition key", "cognitive wealth key", "formulaize", "keyism",
        "people are non-fungible", "non-fungible people",
        "cognitive wealth", "sovereign mind media"
    ]
    somewhat_original = [
        "mental sovereignty", "dynasty architecture", "supermind",
        "cognitive architecture", "crownz", "save yourself"
    ]

    if any(t in t_lower for t in truly_original):
        originality = 4  # Not 5 unless the note DEFINES the concept
        # Check if it actually defines it
        if any(w in t_lower for w in ["means", "defined as", "is when", "refers to", "methodology"]):
            originality = 5
    elif any(t in t_lower for t in somewhat_original):
        originality = 3

    # Reduce for generic content
    generic_signals = ["level up", "grind", "hustle", "boss up", "mindset", "manifest"]
    if sum(1 for g in generic_signals if g in t_lower) >= 2:
        originality = max(1, originality - 1)

    # COMMERCIAL VALUE (1-5)
    # 5 = must name the specific revenue mechanism
    commercial = 2  # baseline

    direct_revenue = [
        "course", "program", "license", "certification", "franchise",
        "subscription", "membership", "ticket", "sponsorship"
    ]
    revenue_hits = sum(1 for r in direct_revenue if r in t_lower)

    if revenue_hits >= 2 and text_len > 200:
        commercial = 4
    elif revenue_hits >= 1 and text_len > 150:
        commercial = 3

    if tier == 1 and category == "ORIGINAL FRAMEWORK":
        commercial = max(commercial, 3)
    if tier == 1 and category == "PROPRIETARY METHODOLOGY":
        commercial = max(commercial, 4)

    # Check for specific revenue mechanism mentioned
    has_specific_mechanism = any(w in t_lower for w in [
        "price point", "pricing", "$", "revenue model", "monetization",
        "licensing deal", "per seat", "per user", "annual fee"
    ])
    if has_specific_mechanism and commercial >= 3:
        commercial = min(5, commercial + 1)

    # CULTURAL WEIGHT (1-5)
    # 5 = paradigm-shifting for sovereignty movement
    cultural = 2  # baseline

    cultural_power = [
        "paradigm", "sovereignty", "liberation", "nation", "diaspora",
        "stateless", "self-determination", "black america", "our people",
        "generational", "collective", "revolution", "awaken"
    ]
    cultural_relevant = [
        "community", "culture", "identity", "consciousness",
        "black", "african", "melanin", "ancestor"
    ]

    power_hits = sum(1 for c in cultural_power if c in t_lower)
    relevant_hits = sum(1 for c in cultural_relevant if c in t_lower)

    if power_hits >= 3:
        cultural = 5
    elif power_hits >= 2:
        cultural = 4
    elif power_hits >= 1 or relevant_hits >= 2:
        cultural = 3
    elif relevant_hits >= 1:
        cultural = 2
    else:
        cultural = 1

    # DEVELOPMENT STAGE (1-5)
    # 5 = could be published/filed/sold TOMORROW based on what's in the note
    if text_len < 80:
        dev_stage = 1
    elif text_len < 150:
        dev_stage = 2
    elif text_len < 300:
        dev_stage = 3
    else:
        dev_stage = 3  # Start at 3 for long notes

    # Boost for structure
    has_clear_structure = (
        any(marker in text for marker in ["1.", "2.", "3."]) or
        any(marker in text for marker in ["Step ", "Phase ", "Stage ", "Pillar "]) or
        text.count("•") >= 3 or
        text.count("- ") >= 3
    )
    if has_clear_structure and text_len > 200:
        dev_stage = min(4, dev_stage + 1)

    # Fully developed check
    has_intro_body_structure = text_len > 400 and has_clear_structure
    if has_intro_body_structure:
        dev_stage = 4

    # Only 5 if it's genuinely ready to deploy
    if text_len > 450 and has_clear_structure and tier <= 2:
        dev_stage = 5

    # Reduce for mixed content
    mixed = detect_mixed_content(text)
    if mixed:
        dev_stage = max(1, dev_stage - 1)

    # BRAND ALIGNMENT (1-5)
    # 5 = core to CWK, HLC, Supermind, or sovereignty philosophy
    alignment = 2  # baseline

    core_brand = ["cognition key", "cognitive wealth key", "high level conversations",
                  "supermind", "save yourself", "dynasty club"]
    brand_adjacent = ["19keys", "19 keys", "crownz", "vanta black", "sovereign"]

    core_hits = sum(1 for c in core_brand if c in t_lower)
    adj_hits = sum(1 for a in brand_adjacent if a in t_lower)

    if core_hits >= 2:
        alignment = 5
    elif core_hits >= 1:
        alignment = 4
    elif adj_hits >= 2:
        alignment = 3
    elif adj_hits >= 1:
        alignment = 2
    else:
        alignment = 1

    composite = originality + commercial + cultural + dev_stage + alignment

    return {
        "originality": originality,
        "commercial_value": commercial,
        "cultural_weight": cultural,
        "development_stage": dev_stage,
        "brand_alignment": alignment,
        "composite": composite
    }


# ═══════════════════════════════════════
# PHASE 4: PRIORITY ASSIGNMENT
# ═══════════════════════════════════════

def assign_priority(tier, scores):
    composite = scores["composite"]
    if tier == 1 and composite >= 20:
        return "CRITICAL"
    if tier == 1 and composite >= 15:
        return "HIGH"
    if tier == 2 and composite >= 20:
        return "HIGH"
    if tier == 2 and composite >= 12:
        return "MEDIUM"
    if tier in [3, 4] and composite >= 15:
        return "MEDIUM"
    if tier in [3, 4]:
        return "LOW"
    if tier >= 5:
        return "ARCHIVE"
    return "LOW"


# ═══════════════════════════════════════
# PHASE 5: MONETARY VALUATION
# ═══════════════════════════════════════

def valuate(tier, category, scores):
    """Assign valuation tier for Tier 1-2 assets only."""
    if tier > 2:
        return None, None

    composite = scores["composite"]

    if tier == 1:
        if composite >= 20:
            return "PLATINUM", "$100K+"
        if composite >= 17:
            return "GOLD", "$25K-$100K"
        if composite >= 14:
            return "SILVER", "$5K-$25K"
        if composite >= 11:
            return "BRONZE", "$1K-$5K"
        return "COPPER", "Under $1K"

    if tier == 2:
        if composite >= 20:
            return "GOLD", "$25K-$100K"
        if composite >= 16:
            return "SILVER", "$5K-$25K"
        if composite >= 12:
            return "BRONZE", "$1K-$5K"
        return "COPPER", "Under $1K"


# ═══════════════════════════════════════
# PHASE 6: FLAGS
# ═══════════════════════════════════════

def assign_flags(text, tier, category, scores):
    flags = []
    mixed = detect_mixed_content(text)

    if mixed:
        flags.append("NEEDS_CLEANUP")

    if tier == 1 and scores["development_stage"] <= 2:
        flags.append("NEEDS_DEVELOPMENT")

    if tier == 1 and scores["composite"] >= 18:
        flags.append("LEGAL_ACTION")

    if tier >= 5:
        flags.append("ARCHIVE")

    if not flags:
        flags.append("CLEAN")

    return flags


# ═══════════════════════════════════════
# PHASE 7: BRAND & TOPIC TAGGING
# ═══════════════════════════════════════

BRAND_TAGS = {
    "#CWK": ["cognition key", "cognitive wealth", "cwk"],
    "#HLC": ["hlc", "high level conversations", "high level conversation", "podcast", "episode"],
    "#Supermind": ["supermind", "superman coffee", "cognitive performance"],
    "#DynastyClub": ["dynasty club", "dynasty"],
    "#SaveYourself": ["save yourself", "tour"],
    "#CrownZ": ["crownz", "crown", "crowns"],
    "#19Keys": ["19keys", "19 keys", "jibrial"],
    "#VantaBlack": ["vanta black", "vantablack"],
    "#DigitalNation": ["digital nation", "zion", "platform"],
}

TOPIC_TAGS = {
    "#Consciousness": ["consciousness", "cognition", "mind", "awareness", "frequency", "mental"],
    "#Economics": ["money", "wealth", "economic", "financial", "invest", "capital", "revenue"],
    "#Culture": ["culture", "community", "black", "identity", "race", "diaspora"],
    "#Technology": ["ai", "artificial intelligence", "tech", "digital", "algorithm", "crypto"],
    "#Wellness": ["health", "wellness", "nutrition", "fitness", "coffee", "supplement"],
    "#Spirituality": ["spirit", "soul", "god", "divine", "energy", "prayer", "faith"],
    "#History": ["history", "ancient", "ancestor", "moor", "egypt", "africa", "civilization"],
    "#Psychology": ["psychology", "mindset", "trauma", "behavior", "subconscious"],
    "#Politics": ["politic", "government", "policy", "power", "governance"],
    "#Relationships": ["relationship", "love", "family", "marriage", "masculine", "feminine"],
    "#Education": ["education", "school", "teach", "learn", "curriculum"],
    "#Media": ["media", "content", "youtube", "instagram", "algorithm", "viral"],
    "#Leadership": ["leader", "leadership", "authority", "vision", "influence"],
    "#Sovereignty": ["sovereign", "sovereignty", "self-determination", "liberation", "nation"],
}


def detect_tags(text):
    t_lower = text.lower()
    tags = {"brand": [], "topic": []}
    for tag, signals in BRAND_TAGS.items():
        if any(s in t_lower for s in signals):
            tags["brand"].append(tag)
    for tag, signals in TOPIC_TAGS.items():
        if any(s in t_lower for s in signals):
            tags["topic"].append(tag)
    return tags


# ═══════════════════════════════════════
# IP ASSESSMENT
# ═══════════════════════════════════════

def generate_assessment(note, tier, tier_label, category, scores, flags):
    """One-sentence honest assessment."""
    t_lower = note["preview"].lower()
    composite = scores["composite"]

    if tier == 6:
        return "No IP value. Operational content, fragment, or noise."

    if tier == 5:
        return f"Raw material — {category.lower()}. May contain seeds of IP but needs significant development before it has value."

    if "NEEDS_CLEANUP" in flags:
        return f"Contains a {category.lower()} mixed with non-IP content (CRM data, bios, or logistics). Extract the IP and discard the noise."

    if tier == 1:
        if composite >= 20:
            return f"High-value {category.lower()} — consider immediate trademark/copyright protection and integration into CWK revenue engine."
        elif composite >= 15:
            return f"Solid {category.lower()} with development potential. Build out the structure and deploy across brand ecosystem."
        else:
            return f"{category} classification but needs more development to realize its commercial potential."

    if tier == 2:
        return f"Deployable {category.lower()} — structured enough to execute. Prioritize based on current strategic priorities."

    if tier == 3:
        return f"Strategic intelligence — informs decisions but is not standalone IP. Use to sharpen positioning and content strategy."

    if tier == 4:
        return f"Creative asset — copyrightable expression. Refine for publication or integration into brand content."

    return "Classified."


# ═══════════════════════════════════════
# MAIN PROCESSING
# ═══════════════════════════════════════

def main():
    print("=" * 60)
    print("IP VAULT — SOVEREIGN RECLASSIFICATION ENGINE")
    print("Chairman's Protocol")
    print("=" * 60)
    print()

    with open(INPUT) as f:
        data = json.load(f)

    # Build unique note list
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
    print(f"Total notes to process: {len(all_notes)}")
    print()

    vault = []
    stats = {
        "total": len(all_notes),
        "by_tier": Counter(),
        "by_tier_label": Counter(),
        "by_category": Counter(),
        "by_priority": Counter(),
        "by_brand": Counter(),
        "by_topic": Counter(),
        "hard_ip_count": 0,
        "noise_count": 0,
        "score_sum": 0,
        "scored_count": 0,
        "valuation_tiers": Counter(),
    }

    for i, note in enumerate(all_notes):
        text = note["preview"]

        # Phase 1: Triage
        noise, noise_type = is_noise(text)
        if noise:
            entry = {
                "id": i + 1,
                "name": note["name"],
                "date": note["date"],
                "preview": text,
                "matched_keywords": note["matched_keywords"],
                "tier": 6,
                "tier_label": "NOISE",
                "category": noise_type or "FRAGMENT",
                "priority": "ARCHIVE",
                "scores": {"originality":0,"commercial_value":0,"cultural_weight":0,"development_stage":0,"brand_alignment":0,"composite":0},
                "valuation_tier": None,
                "estimated_value": None,
                "flags": ["ARCHIVE"],
                "tags": detect_tags(text),
                "ip_assessment": "No IP value. Operational content, fragment, or noise.",
            }
            vault.append(entry)
            stats["by_tier"][6] += 1
            stats["by_tier_label"]["NOISE"] += 1
            stats["by_category"][noise_type or "FRAGMENT"] += 1
            stats["by_priority"]["ARCHIVE"] += 1
            stats["noise_count"] += 1
            continue

        # Phase 2: Classify
        tier, tier_label, category = classify_tier(text, note["name"])

        # Phase 3: Score
        scores = score_note(text, tier, tier_label, category)

        # Phase 4: Priority
        priority = assign_priority(tier, scores)

        # Phase 5: Valuate
        val_tier, val_range = valuate(tier, category, scores)

        # Phase 6: Flags
        flags = assign_flags(text, tier, category, scores)

        # Tags
        tags = detect_tags(text)

        # Assessment
        assessment = generate_assessment(note, tier, tier_label, category, scores, flags)

        entry = {
            "id": i + 1,
            "name": note["name"],
            "date": note["date"],
            "preview": text,
            "matched_keywords": note["matched_keywords"],
            "tier": tier,
            "tier_label": tier_label,
            "category": category,
            "priority": priority,
            "scores": scores,
            "valuation_tier": val_tier,
            "estimated_value": val_range,
            "flags": flags,
            "tags": tags,
            "ip_assessment": assessment,
        }
        vault.append(entry)

        # Stats
        stats["by_tier"][tier] += 1
        stats["by_tier_label"][tier_label] += 1
        stats["by_category"][category] += 1
        stats["by_priority"][priority] += 1
        if tier == 1:
            stats["hard_ip_count"] += 1
        if tier <= 4:
            stats["score_sum"] += scores["composite"]
            stats["scored_count"] += 1
        if val_tier:
            stats["valuation_tiers"][val_tier] += 1
        for t in tags["brand"]:
            stats["by_brand"][t] += 1
        for t in tags["topic"]:
            stats["by_topic"][t] += 1

    # Sort by tier then score
    vault.sort(key=lambda x: (-x["tier"] if x["tier"] == 6 else x["tier"], -x["scores"]["composite"]))
    # Actually: tier ascending (1 first), then score descending within tier
    vault.sort(key=lambda x: (x["tier"], -x["scores"]["composite"]))

    # Compute averages
    avg_score = stats["score_sum"] / max(stats["scored_count"], 1)

    # Critical assets
    critical = [e for e in vault if e["priority"] == "CRITICAL"]
    high = [e for e in vault if e["priority"] == "HIGH"]
    platinum = [e for e in vault if e["valuation_tier"] == "PLATINUM"]
    gold_val = [e for e in vault if e["valuation_tier"] == "GOLD"]

    output = {
        "vault": vault,
        "stats": {
            "total": stats["total"],
            "by_tier": {
                "1_hard_ip": stats["by_tier"].get(1, 0),
                "2_executable": stats["by_tier"].get(2, 0),
                "3_strategic": stats["by_tier"].get(3, 0),
                "4_creative": stats["by_tier"].get(4, 0),
                "5_raw_material": stats["by_tier"].get(5, 0),
                "6_noise": stats["by_tier"].get(6, 0),
            },
            "by_category": dict(stats["by_category"].most_common()),
            "by_priority": dict(stats["by_priority"]),
            "by_brand": dict(stats["by_brand"].most_common()),
            "by_topic": dict(stats["by_topic"].most_common()),
            "hard_ip_count": stats["hard_ip_count"],
            "hard_ip_pct": round(stats["hard_ip_count"] / stats["total"] * 100, 1),
            "noise_count": stats["noise_count"],
            "noise_pct": round(stats["noise_count"] / stats["total"] * 100, 1),
            "avg_score": round(avg_score, 1),
            "scored_count": stats["scored_count"],
            "valuation_tiers": dict(stats["valuation_tiers"]),
            "critical_assets": [{"id":e["id"],"name":e["name"],"score":e["scores"]["composite"],"category":e["category"]} for e in critical],
            "high_assets": [{"id":e["id"],"name":e["name"],"score":e["scores"]["composite"],"category":e["category"]} for e in high[:30]],
            "platinum_assets": [{"id":e["id"],"name":e["name"],"score":e["scores"]["composite"],"value":e["estimated_value"]} for e in platinum],
            "gold_assets": [{"id":e["id"],"name":e["name"],"score":e["scores"]["composite"],"value":e["estimated_value"]} for e in gold_val[:20]],
        }
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print report
    print("VAULT AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total Notes Processed: {stats['total']}")
    print()
    print("TIER DISTRIBUTION:")
    tier_names = {1: "Hard IP", 2: "Executable IP", 3: "Strategic Intel", 4: "Creative Assets", 5: "Raw Material", 6: "Noise/Archive"}
    for t in range(1, 7):
        count = stats["by_tier"].get(t, 0)
        pct = round(count / stats["total"] * 100, 1)
        bar = "█" * int(pct / 2)
        print(f"  Tier {t} ({tier_names[t]:16s}): {count:4d}  ({pct:5.1f}%)  {bar}")
    print()
    print("PRIORITY DISTRIBUTION:")
    for p in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "ARCHIVE"]:
        count = stats["by_priority"].get(p, 0)
        print(f"  {p:12s}: {count:4d}")
    print()
    print(f"SCORING INTEGRITY:")
    print(f"  Average score (Tier 1-4): {avg_score:.1f}/25  (target: 11-13)")
    print(f"  Hard IP: {stats['hard_ip_count']} ({round(stats['hard_ip_count']/stats['total']*100,1)}%)  (target: 15-20%)")
    print(f"  Noise filtered: {stats['noise_count']} ({round(stats['noise_count']/stats['total']*100,1)}%)")
    print()
    print("VALUATION TIERS:")
    for vt in ["PLATINUM", "GOLD", "SILVER", "BRONZE", "COPPER"]:
        count = stats["valuation_tiers"].get(vt, 0)
        print(f"  {vt:10s}: {count:4d}")
    print()
    if critical:
        print(f"CRITICAL ASSETS ({len(critical)}):")
        for c in critical:
            print(f"  [{c['scores']['composite']}/25] {c['category']:25s} {c['name'][:60]}")
    print()
    if platinum:
        print(f"PLATINUM ASSETS ({len(platinum)}):")
        for p in platinum:
            print(f"  [{p['scores']['composite']}/25] {p['estimated_value']:>10s}  {p['name'][:55]}")
    print()
    print(f"TOP BRAND DISTRIBUTION:")
    for tag, count in stats["by_brand"].most_common(7):
        print(f"  {tag:20s}: {count:4d}")
    print()
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()
