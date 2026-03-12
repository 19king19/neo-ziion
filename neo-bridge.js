/**
 * NEO ↔ ZIION BRIDGE v1.0
 * ─────────────────────────────────────────────────────────────────────────
 * Reads neo-state.json and hydrates the ZIION dashboard with live Neo data.
 * Neo (OpenClaw) writes to neo-state.json. This script reads it.
 * Polls every 30 seconds. Runs on page load.
 * ─────────────────────────────────────────────────────────────────────────
 */

const NEO_STATE_URL = '/neo-state.json';
const POLL_INTERVAL = 30000; // 30 seconds

// ── Status class maps ──────────────────────────────────────────────────────
const STATUS_CLASS = {
  ready:    'ready',
  active:   'ready',
  standby:  'critical',
  error:    'critical',
  working:  'in-progress',
  complete: 'near-complete',
};

const STATUS_LABEL = {
  ready:    'Active',
  active:   'Active',
  standby:  'Standby',
  error:    'Error',
  working:  'Working',
  complete: 'Complete',
};

const LOG_ICONS = {
  security: '🛡',
  config:   '⚙',
  system:   '🔄',
  update:   '↑',
  default:  '◆',
};

// ── Main hydration function ────────────────────────────────────────────────
async function hydrateFromNeo() {
  try {
    const res = await fetch(`${NEO_STATE_URL}?t=${Date.now()}`);
    if (!res.ok) throw new Error(`neo-state.json returned ${res.status}`);
    const state = await res.json();

    hydrateEconomy(state.economy);
    hydrateNeuralMap(state.neural_map);
    hydrateAgentsPanel(state.agents);
    hydrateOffersPanel(state.pending_offers, state.offers_summary);
    hydrateNeoLog(state.neo_log);
    updateTimestamp(state.meta);
    if (state.social_totals)   hydrateSocialTotals(state.social_totals);
    if (state.revenue_potential) hydrateRevenuePotential(state.revenue_potential);
    if (state.conversion_stats)  hydrateConversionStats(state.conversion_stats);
    if (state.nation_value)    hydrateNationValue(state.nation_value);

  } catch (err) {
    console.warn('[Neo Bridge] Could not load neo-state.json:', err.message);
  }
}

// ── Economy Banner ─────────────────────────────────────────────────────────
function hydrateEconomy(econ) {
  if (!econ) return;
  setEl('nationGdp',    econ.nation_gdp    || '$4.2M');
  setEl('spendPower',   econ.spending_power || '$87.2M');
  setEl('creatorVal',   econ.creator_value  || '$1.8M');
  setEl('econEquiv',    econ.equivalence    || 'Mid-Size City');
  setEl('econGrade',    econ.economy_grade  || 'A');

  // GDP change color
  const gdpSubEl = document.querySelector('#nationGdp ~ .econ-sub .green-accent');
  if (gdpSubEl && econ.nation_gdp_change) {
    gdpSubEl.textContent = econ.nation_gdp_change;
    gdpSubEl.style.color = econ.nation_gdp_positive ? '#4ade80' : '#f87171';
  }

  // IP Vault stats injected into Creator Value sub
  const crownSubEl = document.querySelector('#creatorVal')?.closest('.econ-item')?.querySelector('.econ-sub');
  if (crownSubEl && econ.ip_vault_total) {
    crownSubEl.textContent = `${econ.ip_vault_total.toLocaleString()} IP assets`;
  }
}

// ── Neural Map / Active Synapses ───────────────────────────────────────────
function hydrateNeuralMap(map) {
  if (!map) return;
  setEl('networkNodeCount', map.active_synapses ?? 5);
  setEl('netThreads',       map.threads       ?? 3);
  setEl('netVotes',         (map.votes ?? 0).toLocaleString());
  setEl('netConnections',   (map.connections ?? 0).toLocaleString());
  setEl('netComplexity',    map.complexity    ?? '2.4×');
}

// ── Agents Team Panel ──────────────────────────────────────────────────────
function hydrateAgentsPanel(agents) {
  if (!agents || !agents.length) return;
  const panel = document.getElementById('panel-agents');
  if (!panel) return;

  const grid = panel.querySelector('.agents-grid') || panel;

  grid.innerHTML = agents.map(agent => {
    const statusClass = STATUS_CLASS[agent.status] || 'critical';
    const statusLabel = STATUS_LABEL[agent.status] || agent.status_label || 'Standby';
    const filesVal = agent.files ?? 0;
    const tasksVal = agent.tasks_complete ?? 0;
    const uptimeVal = agent.uptime ?? '—';
    const progressPct = agent.uptime && agent.uptime !== '—'
      ? parseInt(agent.uptime) : (agent.status === 'ready' || agent.status === 'active' ? 96 : 0);

    return `
      <div class="agent-card" data-agent-id="${agent.id}">
        <div class="agent-card-header">
          <div class="agent-icon ${agent.icon_class || 'research'}">${agent.icon || '◆'}</div>
          <div>
            <div class="agent-name">${agent.name}</div>
            <div class="agent-role">${agent.role}</div>
          </div>
        </div>
        <div class="agent-stats">
          <div class="agent-stat">
            <span class="agent-stat-value">${filesVal}</span>
            <span class="agent-stat-label">Skills</span>
          </div>
          <div class="agent-stat">
            <span class="agent-stat-value">${tasksVal}</span>
            <span class="agent-stat-label">Done</span>
          </div>
          <div class="agent-stat">
            <span class="agent-stat-value">${uptimeVal}</span>
            <span class="agent-stat-label">Load</span>
          </div>
        </div>
        <div class="agent-progress-bar">
          <div class="agent-progress-fill ${statusClass}" style="width:${progressPct}%"></div>
        </div>
        <div class="agent-desc">${agent.desc}</div>
        <div class="agent-meta" style="justify-content:space-between;align-items:center;">
          <span class="agent-tag" style="font-size:9px;opacity:.6;">${agent.last_action_time !== '—' ? agent.last_action : 'Inactive'}</span>
          <span class="agent-status ${statusClass}">
            <span class="agent-status-dot"></span> ${statusLabel}
          </span>
        </div>
      </div>
    `;
  }).join('');
}

// ── Offers Panel ───────────────────────────────────────────────────────────
function hydrateOffersPanel(offers, summary) {
  const panel = document.getElementById('panel-offers');
  if (!panel) return;

  // Status palette (shared with localStorage offers)
  const SC = {
    pending:  { bg: 'rgba(251,191,36,0.12)', color: '#fbbf24', label: 'Pending' },
    accepted: { bg: 'rgba(74,222,128,0.12)',  color: '#4ade80', label: 'Accepted' },
    declined: { bg: 'rgba(248,113,113,0.12)', color: '#f87171', label: 'Declined' }
  };
  function fmtDate(iso) {
    try { return new Date(iso).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' }); }
    catch(e) { return iso; }
  }

  // Allow Accept/Decline buttons to update status and re-render
  window.setOfferStatus = function(id, status) {
    try {
      var arr = JSON.parse(localStorage.getItem('ziion_public_offers') || '[]');
      arr = arr.map(function(o) { return o.id === id ? Object.assign({}, o, { status: status }) : o; });
      localStorage.setItem('ziion_public_offers', JSON.stringify(arr));
      hydrateOffersPanel(offers, summary);
    } catch(e) {}
  };

  // ── Section 1: Live incoming offers from public-book.html ──
  var live = [];
  try { live = JSON.parse(localStorage.getItem('ziion_public_offers') || '[]'); } catch(e) {}

  var liveHTML = '';
  if (live.length) {
    liveHTML = '<div style="font-size:9px;letter-spacing:2px;color:rgba(213,255,90,0.6);margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid rgba(213,255,90,0.1);">INCOMING — BUILD WITH 19KEYS</div>';
    liveHTML += live.map(function(o) {
      var s = SC[o.status] || SC.pending;
      var desc = o.desc ? o.desc.substring(0, 90) + (o.desc.length > 90 ? '…' : '') : '';
      return '<div class="data-card" style="position:relative;">' +
        '<div class="data-row">' +
          '<div class="data-title">' + (o.service || 'Offer') + '</div>' +
          '<div style="background:' + s.bg + ';color:' + s.color + ';border:1px solid ' + s.color + '33;padding:3px 10px;border-radius:3px;font-size:9px;letter-spacing:1px;font-weight:600;text-transform:uppercase;">' + s.label + '</div>' +
        '</div>' +
        '<div class="data-meta" style="margin-bottom:4px;">From ' + (o.name || '—') + ' · ' + (o.offer || '—') + ' · ' + fmtDate(o.timestamp) + '</div>' +
        (o.email ? '<div class="data-meta" style="opacity:0.5;">' + o.email + (o.org ? ' · ' + o.org : '') + '</div>' : '') +
        (desc ? '<div class="data-meta" style="margin-top:6px;opacity:0.65;font-style:italic;">"' + desc + '"</div>' : '') +
        '<div style="display:flex;gap:8px;margin-top:10px;">' +
          '<button onclick="setOfferStatus(' + o.id + ',\'accepted\')" style="font-size:9px;letter-spacing:1px;padding:4px 12px;background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.3);color:#4ade80;cursor:pointer;border-radius:2px;">ACCEPT</button>' +
          '<button onclick="setOfferStatus(' + o.id + ',\'declined\')" style="font-size:9px;letter-spacing:1px;padding:4px 12px;background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.3);color:#f87171;cursor:pointer;border-radius:2px;">DECLINE</button>' +
          '<a href="mailto:' + (o.email || '') + '?subject=Re:%20' + encodeURIComponent((o.service || 'Your Offer') + ' — Build with 19Keys') + '" style="font-size:9px;letter-spacing:1px;padding:4px 12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:rgba(255,255,255,0.5);text-decoration:none;border-radius:2px;">REPLY</a>' +
        '</div>' +
      '</div>';
    }).join('');
    liveHTML += '<div style="margin:12px 0 8px;height:1px;background:rgba(255,255,255,0.05);"></div>';
  }

  // ── Section 2: Neo-state pipeline offers ──
  var neoHTML = '';
  if (offers && offers.length) {
    neoHTML = offers.map(function(o) {
      var isUrgent = o.priority === 'urgent';
      var borderStyle = isUrgent ? 'border-color:rgba(251,191,36,0.25);' : '';
      return '<div class="data-card" style="' + borderStyle + '">' +
        '<div class="data-row">' +
          '<div class="data-title">' + o.type + '</div>' +
          '<div class="data-offer-badge pending">Pending</div>' +
        '</div>' +
        '<div class="data-meta">From ' + o.name +
          (o.badge ? ' · <span style="color:#fbbf24;font-size:10px;">' + o.badge + '</span>' : '') +
          ' · <strong>' + o.amount + '</strong> · ' + o.date +
          (isUrgent ? ' · <span style="color:#f87171;font-size:10px;">⚡ URGENT</span>' : '') +
        '</div>' +
      '</div>';
    }).join('');
  }

  var summaryNote = summary
    ? '<div class="data-empty-note" style="margin-top:12px;"><strong style="color:rgba(255,255,255,0.5);">' + summary.total_count + ' total offers · $' + summary.total_value.toLocaleString() + ' value</strong><br>Manage all in <a href="book-19keys.html">Book 19Keys</a></div>'
    : '<div class="data-empty-note" style="margin-top:8px;">Manage bookings in <a href="book-19keys.html">Book 19Keys</a></div>';

  panel.innerHTML = liveHTML + neoHTML + (neoHTML ? summaryNote : (live.length ? '' : summaryNote));
}

// ── Neo Activity Log ───────────────────────────────────────────────────────
function hydrateNeoLog(log) {
  if (!log || !log.length) return;
  const logEl = document.getElementById('neo-activity-log');
  if (!logEl) return;

  logEl.innerHTML = log.map(entry => {
    const icon = LOG_ICONS[entry.type] || LOG_ICONS.default;
    return `
      <div style="display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
        <span style="font-size:11px;opacity:.4;flex-shrink:0;margin-top:1px;">${icon}</span>
        <span style="font-size:12px;color:rgba(255,255,255,.6);flex:1;">${entry.action}</span>
        <span style="font-size:10px;opacity:.3;flex-shrink:0;">${entry.time}</span>
      </div>
    `;
  }).join('');
}

// ── Social Totals + Daily Growth ──────────────────────────────────────────
function hydrateSocialTotals(totals) {
  if (!totals) return;

  function fmtTotal(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(2).replace(/\.?0+$/, '') + 'M+';
    if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K+';
    return n.toLocaleString();
  }

  function fmtGrowth(n) {
    const sign = n >= 0 ? '+' : '';
    if (Math.abs(n) >= 1000) return sign + (n / 1000).toFixed(1) + 'K today';
    return sign + n.toLocaleString() + ' today';
  }

  // Stats bar
  setEl('statNationTotal', fmtTotal(totals.combined_raw));
  setEl('statDailyGrowth', '+' + (totals.total_daily_growth || 0).toLocaleString());
  setEl('statGrowthRate', '+' + (totals.growth_rate_pct || 0) + '%');

  // Nation value strip
  setEl('nvTotalCitizens', fmtTotal(totals.combined_raw));
  setEl('nvDailyGrowthSub', '+' + (totals.total_daily_growth || 0).toLocaleString() + ' today');

  // Individual platform growth deltas
  const platforms = totals.platforms || {};
  const platformMap = {
    instagram: 'igGrowth',
    youtube:   'ytGrowth',
    x:         'xGrowth',
    threads:   'threadsGrowth',
    tiktok:    'tiktokGrowth'
  };

  Object.entries(platformMap).forEach(([platform, elId]) => {
    const el = document.getElementById(elId);
    if (!el || !platforms[platform]) return;
    const delta = platforms[platform].daily_growth || 0;
    el.textContent = fmtGrowth(delta);
    el.className = 'social-growth ' + (delta > 0 ? 'positive' : delta < 0 ? 'negative' : 'neutral');
  });

  // Also update individual follower counts if present
  const countMap = {
    instagram: 'igCount',
    youtube:   'ytCount',
    x:         'xCount',
    threads:   'threadsCount',
    tiktok:    'tiktokCount'
  };

  Object.entries(countMap).forEach(([platform, elId]) => {
    const el = document.getElementById(elId);
    if (!el || !platforms[platform]?.count) return;
    const n = platforms[platform].count;
    el.textContent = n >= 1e6 ? (n / 1e6).toFixed(3).replace(/0+$/, '').replace(/\.$/, '') + 'M'
                   : n >= 1e3 ? (n / 1e3).toFixed(1) + 'K'
                   : n.toLocaleString();
  });
}

// ── Revenue Potential ──────────────────────────────────────────────────────
function hydrateRevenuePotential(rev) {
  if (!rev) return;
  setEl('nvRevPotential', rev.monthly_label || '$55K–$80K');
  setEl('nvSponsorRate', rev.sponsorship_label || '$15K–$40K per post');
  setEl('nvCoursePipeline', rev.course_label ? '$' + (rev.course_projected / 1000).toFixed(0) + 'K' : '$394K');
  const speakingEl = document.getElementById('nvSpeakingPipeline');
  if (speakingEl) speakingEl.textContent = '$' + (rev.speaking_pipeline || 0).toLocaleString();
}

// ── Nation Total Value ──────────────────────────────────────────────────────
function hydrateNationValue(nv) {
  if (!nv) return;
  setEl('nvNationValue', nv.label || '$8.4M');
  setEl('nvValueGrade', nv.grade || 'A-Tier');
}

// ── Conversion Stats ────────────────────────────────────────────────────────
function hydrateConversionStats(conv) {
  if (!conv) return;

  function setConv(valueId, barId, subId, value, barPct, sub) {
    setEl(valueId, value + '%');
    const bar = document.getElementById(barId);
    if (bar) bar.style.width = Math.min(barPct, 100) + '%';
    if (sub && subId) setEl(subId, sub);
  }

  setConv('convLinkCTR',       'convLinkBar',       null, conv.link_ctr_pct || 3.2,     (conv.link_ctr_pct || 3.2) * 10);
  setConv('convProfileFollow', 'convProfileBar',    null, conv.profile_to_follow_pct || 8.7, (conv.profile_to_follow_pct || 8.7) * 10);
  setConv('convBooking',       'convBookingBar',    null, conv.booking_conversion_pct || 12.4, (conv.booking_conversion_pct || 12.4) * 7);
  setConv('convEngagement',    'convEngagementBar', null, conv.content_engagement_pct || 4.1, (conv.content_engagement_pct || 4.1) * 10);
  setConv('convOfferAccept',   'convOfferBar',      null, conv.offer_acceptance_pct || 68, conv.offer_acceptance_pct || 68);

  const reachEl = document.getElementById('convMonthlyReach');
  if (reachEl) {
    const r = conv.monthly_active_reach || 0;
    reachEl.textContent = r >= 1e6 ? (r / 1e6).toFixed(1) + 'M' : r >= 1e3 ? (r / 1e3).toFixed(0) + 'K' : r.toLocaleString();
  }

  if (conv.last_synced) {
    try {
      const d = new Date(conv.last_synced);
      setEl('convLastSync', timeAgo(d));
    } catch (_) {}
  }
}

// ── Meta Timestamp ─────────────────────────────────────────────────────────
function updateTimestamp(meta) {
  const el = document.getElementById('neo-last-updated');
  if (!el || !meta) return;
  try {
    const d = new Date(meta.last_updated);
    el.textContent = `Neo updated ${timeAgo(d)} · ${meta.status || 'operational'}`;
  } catch (_) {}
}

// ── Helpers ────────────────────────────────────────────────────────────────
function setEl(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function timeAgo(date) {
  const seconds = Math.floor((Date.now() - date) / 1000);
  if (seconds < 60)   return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400)return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  hydrateFromNeo();
  setInterval(hydrateFromNeo, POLL_INTERVAL);
  console.log('[Neo Bridge] Initialized — polling neo-state.json every 30s');
});
