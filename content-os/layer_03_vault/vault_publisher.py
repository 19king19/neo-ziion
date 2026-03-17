"""
Sovereign Content OS — Vault Publisher

Converts Content OS intelligence outputs into an Obsidian-compatible
markdown vault.  Reads JSON artifacts from ``vault/intelligence/`` and
writes structured markdown notes — complete with YAML frontmatter,
Obsidian ``[[wikilinks]]``, and tags — into an ``obsidian_vault/``
directory.

Usage::

    from layer_03_vault.vault_publisher import VaultPublisher

    publisher = VaultPublisher()
    stats = publisher.publish_all()
    print(stats)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import VAULT_INTELLIGENCE, OBSIDIAN_VAULT_PATH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Templates (embedded so the module is self-contained)
# ---------------------------------------------------------------------------

_TEMPLATE_PREDICTION = """\
---
type: prediction
tags:
  - "#sovereign-content-os"
  - "#prediction"
date: "{{date}}"
source: "{{source}}"
confidence: "{{confidence}}"
---

# {{title}}

> **Prediction** — _{{date}}_

{{body}}

---
_Source: {{source}}_
"""

_TEMPLATE_QUOTE = """\
---
type: quote
tags:
  - "#sovereign-content-os"
  - "#quote"
  - "#{{speaker_tag}}"
date: "{{date}}"
speaker: "{{speaker}}"
source: "{{source}}"
---

# Quote — {{speaker}}

> {{text}}

— **{{speaker}}**, _{{source}}_

---
**Related:** {{related_links}}
"""

_TEMPLATE_ANALYSIS = """\
---
type: analysis
tags:
  - "#sovereign-content-os"
  - "#analysis"
date: "{{date}}"
source_file: "{{source_file}}"
---

# Analysis — {{title}}

{{body}}

---
_Generated on {{date}} from {{source_file}}_
"""

_TEMPLATE_THEME = """\
---
type: theme
tags:
  - "#sovereign-content-os"
  - "#theme"
  - "#{{theme_tag}}"
date: "{{date}}"
---

# Theme — {{title}}

{{body}}

---
**Related Notes:** {{related_links}}
"""


# ---------------------------------------------------------------------------
# Vault Publisher
# ---------------------------------------------------------------------------

class VaultPublisher:
    """Publish Content OS intelligence artifacts to an Obsidian vault.

    Parameters
    ----------
    intelligence_dir : Path | str | None
        Directory containing intelligence JSON files.  Defaults to the
        ``VAULT_INTELLIGENCE`` setting.
    vault_dir : Path | str | None
        Root of the Obsidian vault to create / update.  Defaults to
        ``OBSIDIAN_VAULT_PATH``.
    """

    # Sub-directories inside the Obsidian vault
    _FOLDERS: list[str] = [
        ".obsidian",
        "00 — Dashboard",
        "01 — Predictions",
        "02 — Quotes",
        "03 — Themes",
        "04 — Content Analysis",
        "05 — YouTube Analytics",
        "06 — Content Ideas",
        "_templates",
    ]

    def __init__(
        self,
        intelligence_dir: Path | str | None = None,
        vault_dir: Path | str | None = None,
    ) -> None:
        self.intelligence_dir = Path(intelligence_dir or VAULT_INTELLIGENCE)
        self.vault_dir = Path(vault_dir or OBSIDIAN_VAULT_PATH)
        self._now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        logger.info(
            "VaultPublisher initialised — intelligence=%s  vault=%s",
            self.intelligence_dir,
            self.vault_dir,
        )

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def initialize_vault(self) -> None:
        """Create the Obsidian vault directory structure, config, and
        templates.  Safe to call repeatedly — existing files are *not*
        overwritten.
        """
        logger.info("Initialising Obsidian vault at %s", self.vault_dir)

        for folder in self._FOLDERS:
            (self.vault_dir / folder).mkdir(parents=True, exist_ok=True)

        self._write_obsidian_config()
        self._write_templates()
        logger.info("Vault structure ready.")

    def _write_obsidian_config(self) -> None:
        """Write a minimal ``.obsidian/app.json`` so Obsidian recognises
        the directory as a vault."""
        config_path = self.vault_dir / ".obsidian" / "app.json"
        if config_path.exists():
            return

        config = {
            "strictLineBreaks": False,
            "showFrontmatter": True,
            "livePreview": True,
            "readableLineLength": True,
            "defaultViewMode": "preview",
        }
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        logger.debug("Wrote Obsidian config: %s", config_path)

    def _write_templates(self) -> None:
        """Persist note templates into ``_templates/``."""
        tpl_dir = self.vault_dir / "_templates"
        templates = {
            "prediction.md": _TEMPLATE_PREDICTION,
            "quote.md": _TEMPLATE_QUOTE,
            "analysis.md": _TEMPLATE_ANALYSIS,
            "theme.md": _TEMPLATE_THEME,
        }
        for name, content in templates.items():
            path = tpl_dir / name
            if not path.exists():
                path.write_text(content, encoding="utf-8")
                logger.debug("Wrote template: %s", path)

    # ------------------------------------------------------------------
    # Publishing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_obsidian_filename(text: str) -> str:
        """Sanitise arbitrary text into a safe Obsidian-friendly filename.

        - Strips characters illegal on common filesystems.
        - Collapses whitespace.
        - Truncates to 120 characters for readability.
        """
        safe = re.sub(r'[\\/:*?"<>|#^[\]{}]', "", text)
        safe = re.sub(r"\s+", " ", safe).strip()
        return safe[:120] if safe else "Untitled"

    @staticmethod
    def _frontmatter(data: dict[str, Any]) -> str:
        """Return a YAML frontmatter block from *data*.

        Values are written as simple scalars; lists become YAML sequences.
        """
        lines = ["---"]
        for key, value in data.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f'  - "{item}"')
            else:
                lines.append(f'{key}: "{value}"')
        lines.append("---")
        return "\n".join(lines)

    def _read_json(self, filename: str) -> Any | None:
        """Read and parse a JSON file from the intelligence directory.

        Returns ``None`` (and logs a warning) when the file is missing or
        malformed.
        """
        path = self.intelligence_dir / filename
        if not path.exists():
            logger.warning("Intelligence file not found: %s", path)
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse %s: %s", path, exc)
            return None

    def _write_note(self, folder: str, filename: str, content: str) -> Path:
        """Write a markdown note into the vault, returning its path."""
        safe_name = self._to_obsidian_filename(filename)
        if not safe_name.endswith(".md"):
            safe_name += ".md"

        path = self.vault_dir / folder / safe_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.debug("Wrote note: %s", path)
        return path

    # ------------------------------------------------------------------
    # Publishers
    # ------------------------------------------------------------------

    def publish_analyses(self) -> int:
        """Convert analysis JSON files to Obsidian markdown notes.

        Returns the number of notes written.
        """
        count = 0
        analysis_files = sorted(self.intelligence_dir.glob("*_analysis*.json"))

        if not analysis_files:
            # Fall back: look for any JSON that is not one of the known
            # aggregate files.
            known = {"quote_bank.json", "theme_map.json", "youtube_analytics.json"}
            analysis_files = sorted(
                p
                for p in self.intelligence_dir.glob("*.json")
                if p.name not in known
            )

        for path in analysis_files:
            data = self._read_json(path.name)
            if data is None:
                continue

            title = data.get("title", path.stem.replace("_", " ").title())
            source_file = path.name

            # Build body from common analysis keys
            body_parts: list[str] = []

            if "summary" in data:
                body_parts.append(f"## Summary\n\n{data['summary']}\n")

            if "key_points" in data:
                body_parts.append("## Key Points\n")
                for point in data["key_points"]:
                    body_parts.append(f"- {point}")
                body_parts.append("")

            if "predictions" in data:
                body_parts.append("## Predictions\n")
                for pred in data["predictions"]:
                    if isinstance(pred, dict):
                        pred_title = pred.get("title", pred.get("prediction", ""))
                        confidence = pred.get("confidence", "")
                        body_parts.append(
                            f"- {pred_title}"
                            + (f" _(confidence: {confidence})_" if confidence else "")
                        )
                        # Cross-link to Predictions folder
                        pred_filename = self._to_obsidian_filename(pred_title)
                        body_parts.append(f"  - See [[{pred_filename}]]")
                    else:
                        body_parts.append(f"- {pred}")
                body_parts.append("")

            if "themes" in data:
                body_parts.append("## Themes\n")
                for theme in data["themes"]:
                    theme_name = theme if isinstance(theme, str) else theme.get("name", str(theme))
                    body_parts.append(f"- [[{self._to_obsidian_filename(theme_name)}]]")
                body_parts.append("")

            if "quotes" in data:
                body_parts.append("## Notable Quotes\n")
                for quote in data["quotes"]:
                    if isinstance(quote, dict):
                        text = quote.get("text", quote.get("quote", ""))
                        speaker = quote.get("speaker", "Unknown")
                        body_parts.append(f"> {text}\n> — _{speaker}_\n")
                    else:
                        body_parts.append(f"> {quote}\n")
                body_parts.append("")

            # Catch-all for extra keys
            rendered_keys = {
                "title", "summary", "key_points", "predictions",
                "themes", "quotes", "source", "date",
            }
            for key, value in data.items():
                if key in rendered_keys:
                    continue
                if isinstance(value, (str, int, float)):
                    body_parts.append(f"## {key.replace('_', ' ').title()}\n\n{value}\n")

            body = "\n".join(body_parts) if body_parts else json.dumps(data, indent=2)

            fm = self._frontmatter({
                "type": "analysis",
                "tags": ["#sovereign-content-os", "#analysis"],
                "date": data.get("date", self._now),
                "source_file": source_file,
            })

            content = (
                f"{fm}\n\n"
                f"# Analysis — {title}\n\n"
                f"{body}\n\n"
                f"---\n_Generated on {self._now} from {source_file}_\n"
            )

            self._write_note("04 — Content Analysis", f"{title} Analysis", content)

            # Also publish any inline predictions as standalone notes
            for pred in data.get("predictions", []):
                if isinstance(pred, dict):
                    self._publish_single_prediction(pred, source_file)

            count += 1

        logger.info("Published %d analysis notes.", count)
        return count

    def _publish_single_prediction(
        self, pred: dict[str, Any], source: str
    ) -> None:
        """Write one prediction as a standalone note in ``01 — Predictions``."""
        title = pred.get("title", pred.get("prediction", "Untitled Prediction"))
        confidence = pred.get("confidence", "N/A")
        body = pred.get("reasoning", pred.get("details", ""))
        timeframe = pred.get("timeframe", "")

        fm = self._frontmatter({
            "type": "prediction",
            "tags": ["#sovereign-content-os", "#prediction"],
            "date": self._now,
            "source": source,
            "confidence": str(confidence),
        })

        body_text = ""
        if body:
            body_text += f"{body}\n\n"
        if timeframe:
            body_text += f"**Timeframe:** {timeframe}\n\n"
        body_text += f"**Confidence:** {confidence}\n"

        content = (
            f"{fm}\n\n"
            f"# {title}\n\n"
            f"> **Prediction** — _{self._now}_\n\n"
            f"{body_text}\n"
            f"---\n_Source: {source}_\n"
        )
        self._write_note("01 — Predictions", title, content)

    # ------------------------------------------------------------------

    def publish_quotes(self) -> int:
        """Convert ``quote_bank.json`` to individual quote notes.

        Returns the number of notes written.
        """
        data = self._read_json("quote_bank.json")
        if data is None:
            return 0

        quotes: list[dict[str, Any]] = []
        if isinstance(data, list):
            quotes = data
        elif isinstance(data, dict):
            quotes = data.get("quotes", [])

        count = 0
        for quote in quotes:
            if isinstance(quote, str):
                quote = {"text": quote, "speaker": "Unknown", "source": ""}

            text = quote.get("text", quote.get("quote", ""))
            speaker = quote.get("speaker", "Unknown")
            source = quote.get("source", "")
            tags_list = quote.get("tags", [])
            if isinstance(tags_list, str):
                tags_list = [tags_list]

            speaker_tag = re.sub(r"\W+", "-", speaker.lower()).strip("-")
            snippet = text[:80].rstrip()

            # Build related links from tags
            related = ", ".join(
                f"[[{self._to_obsidian_filename(t)}]]" for t in tags_list
            ) or "—"

            fm = self._frontmatter({
                "type": "quote",
                "tags": ["#sovereign-content-os", "#quote", f"#{speaker_tag}"] + [
                    f"#{re.sub(r'\\W+', '-', t.lower()).strip('-')}" for t in tags_list
                ],
                "date": self._now,
                "speaker": speaker,
                "source": source,
            })

            content = (
                f"{fm}\n\n"
                f"# Quote — {speaker}\n\n"
                f"> {text}\n\n"
                f"— **{speaker}**"
                + (f", _{source}_" if source else "")
                + "\n\n---\n"
                f"**Related:** {related}\n"
            )

            self._write_note("02 — Quotes", f"{speaker} — {snippet}", content)
            count += 1

        logger.info("Published %d quote notes.", count)
        return count

    # ------------------------------------------------------------------

    def publish_themes(self) -> int:
        """Convert ``theme_map.json`` to theme notes with backlinks.

        Returns the number of notes written.
        """
        data = self._read_json("theme_map.json")
        if data is None:
            return 0

        themes: list[dict[str, Any]] = []
        if isinstance(data, list):
            themes = data
        elif isinstance(data, dict):
            themes = data.get("themes", [])

        count = 0
        for theme in themes:
            if isinstance(theme, str):
                theme = {"name": theme}

            name = theme.get("name", theme.get("theme", "Untitled Theme"))
            description = theme.get("description", "")
            occurrences = theme.get("occurrences", theme.get("count", 0))
            related = theme.get("related_themes", theme.get("related", []))
            sources = theme.get("sources", [])

            theme_tag = re.sub(r"\W+", "-", name.lower()).strip("-")

            related_links = ", ".join(
                f"[[{self._to_obsidian_filename(r)}]]"
                for r in (related if isinstance(related, list) else [related])
            ) or "—"

            fm = self._frontmatter({
                "type": "theme",
                "tags": ["#sovereign-content-os", "#theme", f"#{theme_tag}"],
                "date": self._now,
                "occurrences": str(occurrences),
            })

            body_parts = []
            if description:
                body_parts.append(f"{description}\n")
            if occurrences:
                body_parts.append(f"**Occurrences:** {occurrences}\n")
            if sources:
                body_parts.append("### Sources\n")
                for src in sources:
                    if isinstance(src, str):
                        body_parts.append(f"- [[{self._to_obsidian_filename(src)}]]")
                    elif isinstance(src, dict):
                        src_name = src.get("title", src.get("name", str(src)))
                        body_parts.append(
                            f"- [[{self._to_obsidian_filename(src_name)}]]"
                        )
                body_parts.append("")

            body = "\n".join(body_parts)

            content = (
                f"{fm}\n\n"
                f"# Theme — {name}\n\n"
                f"{body}\n"
                f"---\n**Related Notes:** {related_links}\n"
            )

            self._write_note("03 — Themes", name, content)
            count += 1

        logger.info("Published %d theme notes.", count)
        return count

    # ------------------------------------------------------------------

    def publish_youtube(self) -> int:
        """Convert ``youtube_analytics.json`` to analytics notes.

        Creates a *Channel Overview* note plus one note per video.
        Returns the total number of notes written.
        """
        data = self._read_json("youtube_analytics.json")
        if data is None:
            return 0

        count = 0

        # ---- Channel overview ----
        channel = data.get("channel", data.get("channel_info", data))
        channel_name = channel.get("name", channel.get("title", "Channel"))
        subscribers = channel.get("subscribers", channel.get("subscriber_count", "N/A"))
        total_views = channel.get("total_views", channel.get("view_count", "N/A"))
        video_count = channel.get("video_count", "N/A")

        fm = self._frontmatter({
            "type": "youtube-analytics",
            "tags": ["#sovereign-content-os", "#youtube", "#analytics"],
            "date": self._now,
            "channel": channel_name,
        })

        overview_body = (
            f"## {channel_name}\n\n"
            f"| Metric | Value |\n"
            f"|--------|-------|\n"
            f"| Subscribers | {subscribers} |\n"
            f"| Total Views | {total_views} |\n"
            f"| Videos | {video_count} |\n"
            f"| Last Updated | {self._now} |\n"
        )

        # Top videos table
        videos = data.get("videos", data.get("top_videos", []))
        if videos:
            overview_body += "\n## Top Videos\n\n"
            overview_body += "| Title | Views | Likes |\n"
            overview_body += "|-------|-------|-------|\n"
            for vid in videos[:10]:
                v_title = vid.get("title", "Untitled")
                v_views = vid.get("views", vid.get("view_count", "—"))
                v_likes = vid.get("likes", vid.get("like_count", "—"))
                safe = self._to_obsidian_filename(v_title)
                overview_body += f"| [[{safe}]] | {v_views} | {v_likes} |\n"

        content = (
            f"{fm}\n\n"
            f"# YouTube — Channel Overview\n\n"
            f"{overview_body}\n"
            f"---\n_Updated {self._now}_\n"
        )
        self._write_note("05 — YouTube Analytics", "Channel Overview", content)
        count += 1

        # ---- Individual video notes ----
        for vid in videos:
            v_title = vid.get("title", "Untitled")
            v_views = vid.get("views", vid.get("view_count", "—"))
            v_likes = vid.get("likes", vid.get("like_count", "—"))
            v_comments = vid.get("comments", vid.get("comment_count", "—"))
            v_date = vid.get("published_at", vid.get("date", "—"))
            v_url = vid.get("url", vid.get("video_url", ""))
            v_description = vid.get("description", "")

            fm_vid = self._frontmatter({
                "type": "youtube-video",
                "tags": ["#sovereign-content-os", "#youtube", "#video"],
                "date": str(v_date),
                "views": str(v_views),
                "likes": str(v_likes),
            })

            vid_body = (
                f"| Metric | Value |\n"
                f"|--------|-------|\n"
                f"| Views | {v_views} |\n"
                f"| Likes | {v_likes} |\n"
                f"| Comments | {v_comments} |\n"
                f"| Published | {v_date} |\n"
            )
            if v_url:
                vid_body += f"\n**URL:** {v_url}\n"
            if v_description:
                vid_body += f"\n## Description\n\n{v_description[:500]}\n"

            vid_content = (
                f"{fm_vid}\n\n"
                f"# {v_title}\n\n"
                f"{vid_body}\n"
                f"---\n"
                f"**Back:** [[Channel Overview]]\n"
            )
            self._write_note("05 — YouTube Analytics", v_title, vid_content)
            count += 1

        logger.info("Published %d YouTube analytics notes.", count)
        return count

    # ------------------------------------------------------------------

    def publish_dashboard(self) -> int:
        """Generate the main Dashboard / Map of Content note.

        Scans the vault for existing notes and builds a linked index.
        Returns ``1`` on success.
        """
        sections: list[str] = []

        sections.append(
            f"# Sovereign Content OS — Dashboard\n\n"
            f"> _Map of Content — last updated {self._now}_\n\n"
            f"---\n"
        )

        # Helper to gather links from a subfolder
        def _section(heading: str, folder: str, emoji: str = "") -> str:
            folder_path = self.vault_dir / folder
            notes = sorted(folder_path.glob("*.md")) if folder_path.exists() else []
            prefix = f"{emoji} " if emoji else ""
            block = f"\n## {prefix}{heading}\n\n"
            if notes:
                block += f"_{len(notes)} note{'s' if len(notes) != 1 else ''}_\n\n"
                for note in notes:
                    link_name = note.stem
                    block += f"- [[{link_name}]]\n"
            else:
                block += "_No notes yet._\n"
            return block

        sections.append(_section("Predictions", "01 — Predictions"))
        sections.append(_section("Quotes", "02 — Quotes"))
        sections.append(_section("Themes", "03 — Themes"))
        sections.append(_section("Content Analysis", "04 — Content Analysis"))
        sections.append(_section("YouTube Analytics", "05 — YouTube Analytics"))
        sections.append(_section("Content Ideas", "06 — Content Ideas"))

        sections.append(
            "\n---\n\n"
            "## Quick Links\n\n"
            "- [[Channel Overview]] — YouTube performance snapshot\n"
            "- [Sovereign Content OS repo](https://github.com/sovereign-content-os)\n\n"
            f"---\n_Generated by Sovereign Content OS on {self._now}_\n"
        )

        fm = self._frontmatter({
            "type": "dashboard",
            "tags": ["#sovereign-content-os", "#dashboard", "#moc"],
            "date": self._now,
        })

        content = fm + "\n\n" + "\n".join(sections)
        self._write_note("00 — Dashboard", "Dashboard", content)
        logger.info("Dashboard published.")
        return 1

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def publish_all(self) -> dict[str, int]:
        """Run every publisher and return a stats dictionary.

        Returns
        -------
        dict
            Keys are publisher names; values are note counts.
        """
        logger.info("=== Vault publish_all started ===")
        self.initialize_vault()

        stats: dict[str, int] = {}
        stats["analyses"] = self.publish_analyses()
        stats["quotes"] = self.publish_quotes()
        stats["themes"] = self.publish_themes()
        stats["youtube"] = self.publish_youtube()
        stats["dashboard"] = self.publish_dashboard()
        stats["total"] = sum(stats.values())

        logger.info("=== Vault publish_all finished — %s ===", stats)
        return stats
