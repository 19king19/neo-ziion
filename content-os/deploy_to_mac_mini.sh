#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Sovereign Content OS — Mac Mini Deploy Script
# Deploys the full memory stack + content pipeline to OpenClaw
# ══════════════════════════════════════════════════════════════

MAC_MINI="keyskeys@192.168.1.198"
REMOTE_DIR="/Users/keyskeys/sovereign-content-os"
OPENCLAW_WORKSPACE="/Users/keyskeys/clawd"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║  DEPLOYING SOVEREIGN CONTENT OS          ║"
echo "║  Target: $MAC_MINI                       ║"
echo "╚══════════════════════════════════════════╝"

# ── Step 1: Deploy Content OS Pipeline ──
echo ""
echo "▸ Step 1: Syncing Content OS to Mac Mini..."
rsync -avz --exclude '__pycache__' \
           --exclude '*.pyc' \
           --exclude '.env' \
           --exclude 'node_modules' \
           "$LOCAL_DIR/" "$MAC_MINI:$REMOTE_DIR/"

echo "  ✓ Content OS synced"

# ── Step 2: Deploy Memory Files to OpenClaw Workspace ──
echo ""
echo "▸ Step 2: Deploying memory files to OpenClaw workspace..."
scp "$LOCAL_DIR/memory/CLAUDE.md" "$MAC_MINI:$OPENCLAW_WORKSPACE/CLAUDE.md"
scp "$LOCAL_DIR/memory/KNOWLEDGE-MAP.md" "$MAC_MINI:$OPENCLAW_WORKSPACE/KNOWLEDGE-MAP.md"
scp "$LOCAL_DIR/memory/OPERATIONS.md" "$MAC_MINI:$OPENCLAW_WORKSPACE/OPERATIONS.md"
echo "  ✓ Memory files deployed"

# ── Step 3: Deploy MCP Config ──
echo ""
echo "▸ Step 3: Deploying MCP server configuration..."
scp "$LOCAL_DIR/memory/mcp-config.json" "$MAC_MINI:~/.openclaw/mcp-servers.json"
echo "  ✓ MCP config deployed"

# ── Step 4: Install Python Dependencies ──
echo ""
echo "▸ Step 4: Installing Python dependencies on Mac Mini..."
ssh "$MAC_MINI" "cd $REMOTE_DIR && pip3 install -r requirements.txt"
echo "  ✓ Dependencies installed"

# ── Step 5: Create .env if not exists ──
echo ""
echo "▸ Step 5: Checking .env configuration..."
ssh "$MAC_MINI" "if [ ! -f $REMOTE_DIR/config/.env ]; then cp $REMOTE_DIR/config/.env.template $REMOTE_DIR/config/.env && echo '  ⚠ Created .env from template — fill in API keys!'; else echo '  ✓ .env already exists'; fi"

# ── Step 6: Verify Obsidian Vault ──
echo ""
echo "▸ Step 6: Verifying Obsidian vault structure..."
ssh "$MAC_MINI" "ls -la $REMOTE_DIR/obsidian_vault/ 2>/dev/null || echo '  ⚠ Vault directory not found'"

# ── Step 7: Install Cron Jobs ──
echo ""
echo "▸ Step 7: Setting up cron jobs..."
ssh "$MAC_MINI" "bash -s" << 'CRON_EOF'
# Remove old content-os cron entries
crontab -l 2>/dev/null | grep -v 'sovereign-content-os' | crontab -

# Add new cron jobs
(crontab -l 2>/dev/null; cat << 'ENTRIES'
# ── Sovereign Content OS — Scheduled Jobs ──
# Nightly consolidation at 2:00 AM
0 2 * * * cd /Users/keyskeys/sovereign-content-os && /usr/bin/python3 -c "from layer_06_autonomous.nightly_consolidation import run_consolidation; run_consolidation()" >> /Users/keyskeys/sovereign-content-os/cron.log 2>&1
# Heartbeat monitor — ensure orchestrator is running (every 5 min)
*/5 * * * * cd /Users/keyskeys/sovereign-content-os && /usr/bin/python3 -c "from layer_06_autonomous.heartbeat_monitor import run_heartbeat; run_heartbeat()" >> /Users/keyskeys/sovereign-content-os/heartbeat_cron.log 2>&1
ENTRIES
) | crontab -
echo "  ✓ Cron jobs installed"
CRON_EOF

# ── Step 8: Create search index directory ──
echo ""
echo "▸ Step 8: Creating search index directory..."
ssh "$MAC_MINI" "mkdir -p $REMOTE_DIR/search_index $REMOTE_DIR/codex_tasks"
echo "  ✓ Index directories created"

echo ""
echo "══════════════════════════════════════════"
echo "  DEPLOYMENT COMPLETE"
echo ""
echo "  Next steps:"
echo "  1. SSH into Mac Mini: ssh $MAC_MINI"
echo "  2. Fill in API keys: nano $REMOTE_DIR/config/.env"
echo "  3. Add Twitter keys if posting: nano $REMOTE_DIR/config/.env"
echo "  4. Start daemon: cd $REMOTE_DIR && python3 orchestrator.py"
echo "  5. Verify status: curl http://localhost:8819/api/health"
echo "  6. Test search: curl http://localhost:8819/api/search?q=sovereignty"
echo "  7. Check heartbeat: curl http://localhost:8819/api/heartbeat"
echo "══════════════════════════════════════════"
