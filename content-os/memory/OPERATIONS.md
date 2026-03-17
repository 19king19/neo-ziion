# Operations Manual — OpenClaw Autonomous Procedures

> Defines what OpenClaw does automatically vs. what requires approval.
> Referenced by the session-memory hook for operational context.

---

## Autonomous Actions (No Approval Needed)

### Every 15 Minutes
- Sync Google Drive for new uploads (audio, video, documents)
- Run Whisper transcription on any new media files
- Update status.json with pipeline state

### Every 30 Minutes
- Run Claude analysis on new transcripts
- Extract predictions, quotes, and frameworks
- Cluster themes across all analyzed content
- Publish intelligence to Obsidian vault
- Update knowledge graph links

### Every 60 Minutes
- Pull YouTube analytics (views, engagement, top videos)
- Generate analytics intelligence report
- Update performance dashboards

### Daily (6:00 AM)
- Generate Chairman's Daily Brief
- Compile overnight analytics summary
- Surface top predictions nearing verification dates
- List content opportunities based on trending themes

---

## Approval Required (Flag for 19 Keys)

- Publishing content to any external platform
- Sending messages via Telegram (except status updates)
- Modifying ZIION website files
- Changing API keys or credentials
- Creating new accounts or integrations
- Spending money or making purchases
- Sharing any content externally

---

## Error Handling

### Priority Levels
- **P0 (Critical)**: Pipeline completely down → Telegram alert immediately
- **P1 (High)**: API auth failure → Log + Telegram alert within 5 min
- **P2 (Medium)**: Individual job failure → Log, retry 3x, then alert
- **P3 (Low)**: Non-critical warning → Log only, include in daily brief

### Recovery Procedures
1. **Google Drive auth expired**: Run `python setup_google.py` to re-authenticate
2. **Whisper OOM error**: Switch to `small` model temporarily, flag in daily brief
3. **Claude API rate limit**: Back off exponentially, queue remaining items
4. **Status server crash**: Auto-restart via daemon thread, log the failure
5. **Obsidian vault write failure**: Check disk space, fallback to JSON storage

---

## Communication Channels

### Telegram (Primary)
- Bot token configured in clawdbot.json
- Use for: alerts, daily briefs, quick status updates
- Format: concise, emoji indicators (🟢 success, 🔴 error, 🟡 warning, 📊 report)

### Status API (Dashboard)
- FastAPI on port 8819
- ZIION frontend polls this for real-time module status
- Endpoints: /api/status, /api/health, /api/quotes, /api/themes, /api/vault

### Log Files
- `orchestrator.log` — Main pipeline log
- Individual module logs via Python logging

---

## Pipeline Data Flow

```
[Google Drive] ──→ vault/raw/
                        │
[YouTube API] ──→       │
                        ▼
              [Whisper Transcription]
                        │
                        ▼
               vault/transcripts/
                        │
                        ▼
              [Claude Analysis]
              ┌────────┼────────┐
              ▼        ▼        ▼
          Predictions Quotes  Themes
              │        │        │
              └────────┼────────┘
                       ▼
            vault/intelligence/
                       │
                       ▼
            [Vault Publisher]
                       │
                       ▼
             obsidian_vault/
              (Knowledge Graph)
                       │
                       ▼
            [ZIION IP Vault Page]
            [Daily Intelligence Brief]
            [Content OS Dashboard]
```

---

## Mac Mini System Info

- **Host**: keyskeys@192.168.1.198
- **OpenClaw Gateway**: localhost:18789
- **Status Server**: 0.0.0.0:8819
- **Workspace**: /Users/keyskeys/clawd
- **Python**: python3 (system)
- **Always Running**: orchestrator.py (daemon mode)
