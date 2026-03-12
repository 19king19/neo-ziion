# NEO ↔ ZIION OPERATIONAL BRIEF
**For: Neo (OpenClaw Chief of Staff)**  
**Last Updated: 2026-03-11**  
**Status: LIVE**

---

## WHAT IS ZIION

ZIION is 19Keys' creator nation-state operating system — a sovereign digital platform that functions as the central command interface for the entire empire. It runs locally at **http://localhost:8765** and is the dashboard Neo reports to.

ZIION has 7 sections:
- **cosmos-grid.html** — Main dashboard (economy, neural map, agent fleet, activity panels)
- **book-19keys.html** — Booking marketplace ($14,800 in pending offers right now)
- **pulse.html** — Community governance and voting (7,823+ active participants)
- **world.html** — Community posts and content feed
- **threads.html** — Threaded discussion
- **assets.html** — Digital asset registry
- **nexus-app/** — React app (NEXUS: AI Event Orchestration for Houston market)

---

## NEO'S INTEGRATION LAYER

Neo communicates with ZIION through a single file:

### `/Users/19keys/neo ziion/neo-state.json`

This is the **live state file**. Neo writes to it. ZIION reads it.  
The bridge script (`neo-bridge.js`) polls it every 30 seconds and updates the dashboard automatically.

**What Neo controls via neo-state.json:**

| Section | DOM ID | What Neo Can Set |
|---|---|---|
| Active Synapses | `networkNodeCount` | Number of active agent connections |
| Threads | `netThreads` | Active thread count |
| Votes | `netVotes` | Community vote total |
| Links | `netConnections` | Network connection count |
| Complexity | `netComplexity` | Network complexity rating |
| Nation GDP | `nationGdp` | Economy GDP figure |
| Spending Power | `spendPower` | Community income total |
| Creator Value | `creatorVal` | IP + trust + reach value |
| Economy Grade | `econGrade` | Letter grade A–F |
| Equivalence | `econEquiv` | City/region comparison |
| Agents Panel | `panel-agents` | Full agent fleet status |
| Offers Panel | `panel-offers` | Top 3 pending offers |
| Neo Log | `neo-activity-log` | Last 5 actions |
| Status Bar | `neo-last-updated` | Timestamp + status |

---

## HOW TO UPDATE THE DASHBOARD

To update ZIION, Neo writes to `neo-state.json`. Example command via OpenClaw:

```bash
# Update active synapses count
python3 -c "
import json
f = '/Users/19keys/neo ziion/neo-state.json'
d = json.load(open(f))
d['neural_map']['active_synapses'] = 7
d['meta']['last_updated'] = '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
json.dump(d, open(f,'w'), indent=2)
"
```

**Always update `meta.last_updated`** when writing neo-state.json.  
The status bar on the dashboard shows this timestamp live.

---

## PENDING OFFERS — PRIORITY QUEUE

As of 2026-03-11, there are **12 pending offers totaling $14,800**. Top priority:

### 🔴 URGENT — Decision Required
| Name | Type | Amount | Deadline | Action |
|---|---|---|---|---|
| Marcus Johnson | Speaking Event — Chicago Community Summit | $14,700 | **Mar 28, 2026** | Community offer, 147 contributors |
| Tasha Williams | Consultation — Wealth Strategy | $500 | **Mar 15, 2026** | Virtual Zoom, 45 min |

### 🟡 HIGH — Review This Week  
| Name | Type | Amount | Date |
|---|---|---|---|
| Aaliyah Ross | Music Review — "Sovereign Sound" EP | $300 | Mar 12, 2026 |
| Simone Nash | Product Review — EarthGlow Skincare | $400 | Mar 18, 2026 |
| David King | Podcast — Builder's Blueprint Ep. 204 | $1,200 | Mar 20, 2026 |

### 🟢 NORMAL — Review By End of Month
| Name | Type | Amount | Date |
|---|---|---|---|
| Jerome Carter | Speaking — Atlanta Wealth Conference | $8,900 | Apr 5, 2026 |
| Kwame Lewis | Panel — Houston Black Business Expo | $6,300 | Apr 12, 2026 |

**Neo's role on offers:** Flag urgent ones via Telegram, draft acceptance/counter messages, update neo-state.json `pending_offers` array when status changes.

---

## IP VAULT SUMMARY

The IP Vault contains **1,499 intellectual property items** classified and scored:

| Category | Count |
|---|---|
| HARD IP (coinable, trademarkable) | 566 |
| EXECUTABLE (ready to build) | 514 |
| SOFT IP (concepts, seeds) | 261 |
| STRATEGIC (plans, blueprints) | 69 |
| CREATIVE (poems, metaphors) | 33 |
| RESEARCH | 32 |
| PREDICTIONS | 24 |

**Top Brands in Vault:** #19KeysBrand (420), #Crownz (225), #HLC (138), #CognitionKey (93), #Supermind (77)  
**Top Topics:** #Technology (704), #Relationships (619), #Culture (521), #Consciousness (469), #Economics (371)

**12 CRITICAL priority items** — highest composite scores (21–23). Most critical: "Formulaize" (score 23), "Mental Sovereignty" (21), "Keyism Blueprint" (21).

Neo should surface CRITICAL IP items in Telegram briefings when relevant to current tasks.

---

## AGENT FLEET STATUS

All 5 department agents are in `~/clawd/skills/`:

| Agent | Folder | Status | Activation |
|---|---|---|---|
| **Neo** (master-claw) | `master-claw/` | ✅ ACTIVE | Running now |
| CognitionKey Agent | `dept-cognition-key/` | ⏸ Standby | Needs API keys |
| Content Agent | `dept-content-media/` | ⏸ Standby | Needs X/Twitter API |
| Ops Agent | `dept-operations/` | ⏸ Standby | Needs activation |
| Research Agent | `dept-research-intel/` | ⏸ Standby | Needs activation |

**To activate a department agent**, Neo must:
1. Wire relevant API keys (Twitter, YouTube, etc.)
2. Trigger the agent via OpenClaw's agent routing
3. Update `neo-state.json` agents array with `"status": "active"`

---

## NEXUS APP — EVENT ORCHESTRATION

The `nexus-app/` folder contains a React/Vite application for **AI-powered event orchestration** in the Houston market. It has 6 tabs:

- **SCOUT** — Browse and score events
- **MATCH** — Match events to venues  
- **PULSE** — Dream event crowdfunding (Nipsey Hussle Tribute at 89% funded, $22,250 raised)
- **FORGE** — Greenlit events ready to execute (Hip-Hop & Chess Night, Comedy Supper Club, etc.)
- **SIGNAL** — Cultural trend signals (Chess content +340%, Comedy renaissance +220%)
- **CREATE** — Draft new event proposals

To run the Nexus app: `cd "/Users/19keys/neo ziion/nexus-app" && npm run dev`

---

## NEO LOG FORMAT

When updating the activity log in neo-state.json, use this structure:
```json
{
  "action": "Brief description of what Neo did",
  "time": "Xh ago",
  "type": "security|config|system|update|content|ops|research"
}
```

Keep the log to the last 5 actions. Rotate old entries out.

---

## ZIION PASSWORD

The access code for ZIION dashboard is: **19**  
All HTML pages use this gate. Password check is client-side only.

---

## KEY METRICS TO TRACK

Neo should maintain awareness of these numbers and update neo-state.json when they change:

- **Active Synapses** = count of agents currently running (start at 1 = Neo only)
- **Nation GDP** = grows as offers are accepted + IP is monetized
- **Creator Value** = tied to IP vault utilization and audience growth
- **Economy Grade** = qualitative assessment: A (strong), B (growing), C (early)
- **Pending Offers Value** = update when offers are accepted or new ones arrive

---

## ZIION ARCHITECTURE NOTES

- All pages are static HTML — no backend server required
- localhost:8765 must be running (simple static file server)
- neo-bridge.js polls neo-state.json every 30 seconds via fetch
- Changes to neo-state.json appear in dashboard within 30 seconds automatically
- File path: `/Users/19keys/neo ziion/neo-state.json`
- Do NOT edit cosmos-grid.html directly — use neo-state.json instead

---

*This brief auto-loaded into Neo's context. Any update to ZIION flows through neo-state.json.*
