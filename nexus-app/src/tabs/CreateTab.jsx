import { Fragment, useState, useEffect, useCallback, useRef } from "react";
import { venueSlots, categoryGroups } from "../data/constants";
import { scoreColor } from "../data/utils";
import { styles as s } from "../data/styles";
import ActionBtn from "../components/ActionBtn";
import { BestDealBadge } from "../components/Badges";

export default function CreateTab({ onDraftChange }) {
  const [createStep, setCreateStep] = useState(0);
  const [eventDraft, setEventDraft] = useState({
    name: "", category: "", categoryGroup: "", venue: "", ticketPrice: 30, capacity: 100,
  });
  const [liveScore, setLiveScore] = useState(null);
  const [celebrating, setCelebrating] = useState(false);
  const [celebrateScore, setCelebrateScore] = useState(0);
  const celebrationRef = useRef(null);

  const bestDealIdx = venueSlots.reduce(
    (best, slot, i) => (parseInt(slot.savings) > parseInt(venueSlots[best].savings) ? i : best),
    0
  );

  // Live scoring
  useEffect(() => {
    if (eventDraft.name) {
      const nameScore = Math.min(eventDraft.name.length * 3, 30);
      const categoryScore = eventDraft.category ? 20 : 0;
      const venueScore = eventDraft.venue ? 25 : 0;
      const priceScore = eventDraft.ticketPrice > 0 ? Math.min(eventDraft.ticketPrice / 2, 25) : 0;
      setLiveScore(Math.min(Math.round(nameScore + categoryScore + venueScore + priceScore), 100));
      if (eventDraft.name.length > 2) onDraftChange?.(true);
    } else {
      setLiveScore(null);
    }
  }, [eventDraft, onDraftChange]);

  // FIX: Clean up celebration interval on unmount
  const triggerCelebration = useCallback(() => {
    setCelebrating(true);
    setCelebrateScore(0);
    let count = 0;
    celebrationRef.current = setInterval(() => {
      count += 3;
      setCelebrateScore(Math.min(count, liveScore || 80));
      if (count >= (liveScore || 80)) {
        clearInterval(celebrationRef.current);
        setTimeout(() => setCelebrating(false), 3000);
      }
    }, 30);
  }, [liveScore]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (celebrationRef.current) clearInterval(celebrationRef.current);
    };
  }, []);

  const steps = ["CONCEPT", "VENUE", "ECONOMICS", "LAUNCH"];
  const progressPct = Math.round(((createStep + 1) / steps.length) * 100);

  if (celebrating) {
    return (
      <div style={{ textAlign: "center", padding: "60px 20px" }}>
        <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", letterSpacing: 4, marginBottom: 12 }}>EVENT LAUNCHED</p>
        <p style={{ fontSize: 80, fontWeight: "bold", color: scoreColor(celebrateScore), margin: 0, fontFamily: "'Courier New', monospace", transition: "color 0.3s" }}>
          {celebrateScore}
        </p>
        <p style={{ fontFamily: "'Courier New', monospace", fontSize: 14, color: "#B8860B", letterSpacing: 4, margin: "12px 0", fontWeight: "bold" }}>
          ◆ LIVE ◆
        </p>
        <p style={{ fontSize: 20, color: "#FAF0DC", fontWeight: "bold", margin: "16px 0 8px" }}>{eventDraft.name}</p>
        <p style={{ fontFamily: "'Courier New', monospace", fontSize: 13, color: "#6B5B4F" }}>{eventDraft.venue} · {eventDraft.category}</p>
        <p style={{ fontFamily: "Georgia", fontSize: 15, color: "#8B7355", fontStyle: "italic", marginTop: 32 }}>
          Dead space becomes living culture — through you.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Resume draft banner */}
      {eventDraft.name && createStep === 0 && (
        <div style={{ background: "rgba(184,134,11,0.08)", border: "1px solid #3C2415", padding: "12px 16px", marginBottom: 16, borderRadius: 2, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#B8860B" }}>
            ◆ DRAFT IN PROGRESS: {eventDraft.name}
          </span>
          <ActionBtn onClick={() => setCreateStep(1)}>RESUME →</ActionBtn>
        </div>
      )}

      <p style={s.sectionLabel}>EVENT FORGE</p>
      <p style={s.sectionTitle}>Create New Event</p>

      {/* Step indicator */}
      <div style={{ display: "flex", gap: 0, marginBottom: 8 }}>
        {steps.map((step, i) => (
          <div key={step} style={{ flex: 1, textAlign: "center" }}>
            <div style={{ height: 4, background: i <= createStep ? "linear-gradient(90deg, #B8860B, #DAA520)" : "#2C1810", transition: "background 0.3s" }} />
            <p
              style={{
                fontFamily: "'Courier New', monospace", fontSize: 11, letterSpacing: 2, margin: "8px 0 0 0",
                color: i <= createStep ? "#B8860B" : "#5C4A3A", cursor: i <= createStep ? "pointer" : "default",
              }}
              onClick={() => i <= createStep && setCreateStep(i)}
            >
              {step}
            </p>
          </div>
        ))}
      </div>
      <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#5C4A3A", textAlign: "right", margin: "0 0 20px 0" }}>
        {progressPct}% COMPLETE
      </p>

      {/* Live score */}
      {liveScore !== null && (
        <div style={{ position: "fixed", top: 130, right: 24, background: "#141009", border: "1px solid #2C1810", padding: "14px 18px", borderRadius: 2, zIndex: 10, textAlign: "center" }}>
          <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", margin: "0 0 4px 0", letterSpacing: 2 }}>LIVE SCORE</p>
          <p style={{ fontSize: 35, fontWeight: "bold", color: scoreColor(liveScore), margin: 0, fontFamily: "'Courier New', monospace" }}>{liveScore}</p>
        </div>
      )}

      {/* Step 0: Concept */}
      {createStep === 0 && (
        <div style={{ maxWidth: 600 }}>
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B4513", letterSpacing: 2, display: "block", marginBottom: 8 }}>EVENT NAME</label>
            <input style={s.input} placeholder="e.g., Hip-Hop & Chess Night" value={eventDraft.name}
              onChange={(e) => setEventDraft({ ...eventDraft, name: e.target.value })} />
          </div>
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B4513", letterSpacing: 2, display: "block", marginBottom: 8 }}>CATEGORY</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {categoryGroups.map((g) => (
                <div key={g.group}>
                  <button
                    onClick={() => setEventDraft({ ...eventDraft, categoryGroup: g.group, category: "" })}
                    style={{
                      fontFamily: "'Courier New', monospace", fontSize: 13, padding: "12px 16px",
                      width: "100%", textAlign: "left", cursor: "pointer", borderRadius: 2,
                      background: eventDraft.categoryGroup === g.group ? "rgba(184,134,11,0.1)" : "#141009",
                      border: eventDraft.categoryGroup === g.group ? "1px solid #B8860B" : "1px solid #2C1810",
                      color: eventDraft.categoryGroup === g.group ? "#B8860B" : "#8B7355",
                      letterSpacing: 2, fontWeight: "bold", minHeight: 48,
                    }}
                  >
                    {g.group.toUpperCase()}
                  </button>
                  {eventDraft.categoryGroup === g.group && (
                    <div style={{ marginTop: 4 }}>
                      {g.items.map((item) => (
                        <button key={item}
                          onClick={() => setEventDraft({ ...eventDraft, category: item })}
                          style={{
                            fontFamily: "'Courier New', monospace", fontSize: 12, padding: "8px 12px",
                            width: "100%", textAlign: "left", cursor: "pointer", borderRadius: 1,
                            background: eventDraft.category === item ? "#B8860B" : "none",
                            color: eventDraft.category === item ? "#0D0906" : "#6B5B4F",
                            border: "none", borderBottom: "1px solid #1A1208",
                          }}
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
          <div style={{ marginBottom: 28 }}>
            <label style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B4513", letterSpacing: 2, display: "block", marginBottom: 8 }}>DESCRIBE YOUR VISION</label>
            <textarea style={{ ...s.input, height: 100, resize: "vertical" }} placeholder="What makes this event unique? Who is it for?" />
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <ActionBtn primary disabled={!eventDraft.name || !eventDraft.category} onClick={() => setCreateStep(1)}>
              NEXT: SELECT VENUE →
            </ActionBtn>
          </div>
        </div>
      )}

      {/* Step 1: Venue */}
      {createStep === 1 && (
        <div>
          <p style={{ fontFamily: "'Courier New', monospace", fontSize: 13, color: "#8B7355", marginBottom: 14, lineHeight: 1.5 }}>
            AI-matched venues based on your concept. Showing dead-time deals only.
          </p>
          {venueSlots.map((slot, i) => (
            <div key={slot.venue} style={{
              ...s.card(i === bestDealIdx),
              borderColor: eventDraft.venue === slot.venue ? "#B8860B" : (i === bestDealIdx ? "#B8860B" : "#2C1810"),
            }} onClick={() => setEventDraft({ ...eventDraft, venue: slot.venue, capacity: slot.capacity })}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <p style={{ fontSize: 16, fontWeight: "bold", color: "#FAF0DC", margin: 0 }}>{slot.venue}</p>
                    {i === bestDealIdx && <BestDealBadge />}
                  </div>
                  <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F", margin: "4px 0 0 0" }}>
                    {slot.day} · {slot.time} · Cap: {slot.capacity}
                  </p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <p style={{ fontSize: 20, fontWeight: "bold", color: "#2D6A4F", margin: 0 }}>{slot.nexus}</p>
                  <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#B8860B", margin: 0 }}>{slot.savings} OFF</p>
                </div>
              </div>
            </div>
          ))}
          <div style={{ display: "flex", gap: 8, marginTop: 16, justifyContent: "space-between" }}>
            <ActionBtn onClick={() => setCreateStep(0)}>← BACK</ActionBtn>
            <ActionBtn primary disabled={!eventDraft.venue} onClick={() => setCreateStep(2)}>NEXT: ECONOMICS →</ActionBtn>
          </div>
        </div>
      )}

      {/* Step 2: Economics */}
      {createStep === 2 && (
        <div style={{ maxWidth: 600 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
            <div>
              <label style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B4513", letterSpacing: 2, display: "block", marginBottom: 8 }}>TICKET PRICE ($)</label>
              <input type="number" style={s.input} value={eventDraft.ticketPrice}
                onChange={(e) => setEventDraft({ ...eventDraft, ticketPrice: parseInt(e.target.value) || 0 })} />
            </div>
            <div>
              <label style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B4513", letterSpacing: 2, display: "block", marginBottom: 8 }}>CAPACITY</label>
              <input type="number" style={s.input} value={eventDraft.capacity}
                onChange={(e) => setEventDraft({ ...eventDraft, capacity: parseInt(e.target.value) || 0 })} />
            </div>
          </div>
          <div style={{ background: "#141009", border: "1px solid #2C1810", padding: 18, borderRadius: 2, marginBottom: 24 }}>
            <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B4513", letterSpacing: 2, margin: "0 0 14px 0" }}>LIVE PROFITABILITY MODEL</p>
            {(() => {
              const revenue = eventDraft.ticketPrice * eventDraft.capacity * 0.75;
              const venueCost = parseInt(venueSlots.find((v) => v.venue === eventDraft.venue)?.nexus?.replace(/[^0-9]/g, "") || "500");
              const costs = venueCost + 300 + 200 + 150 + 100;
              const platformFee = revenue * 0.08;
              const profit = revenue - costs - platformFee;
              const breakeven = Math.ceil(costs / (eventDraft.ticketPrice || 1));
              return (
                <div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                    {[
                      ["Projected Revenue (75% fill):", `$${revenue.toLocaleString()}`],
                      ["Total Costs:", `-$${costs.toLocaleString()}`],
                      ["Platform Fee (8%):", `-$${Math.round(platformFee).toLocaleString()}`],
                    ].map(([l, v]) => (
                      <Fragment key={l}>
                        <span style={{ fontFamily: "'Courier New', monospace", fontSize: 13, color: "#8B7355" }}>{l}</span>
                        <span style={{ fontFamily: "'Courier New', monospace", fontSize: 13, color: "#FAF0DC", textAlign: "right" }}>{v}</span>
                      </Fragment>
                    ))}
                  </div>
                  <div style={{ borderTop: "1px solid #3C2415", marginTop: 10, paddingTop: 10, display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontFamily: "'Courier New', monospace", fontSize: 14, color: profit > 0 ? "#2D6A4F" : "#CC3333", fontWeight: "bold" }}>
                      {profit > 0 ? "PROJECTED PROFIT" : "PROJECTED LOSS"}
                    </span>
                    <span style={{ fontFamily: "'Courier New', monospace", fontSize: 18, color: profit > 0 ? "#2D6A4F" : "#CC3333", fontWeight: "bold" }}>
                      ${Math.abs(Math.round(profit)).toLocaleString()}
                    </span>
                  </div>
                  <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F", margin: "10px 0 0 0" }}>
                    Breakeven: {breakeven} tickets · Profit zone: {profit > 0 ? "GREEN" : "RED"}
                  </p>
                </div>
              );
            })()}
          </div>
          <div style={{ display: "flex", gap: 8, justifyContent: "space-between" }}>
            <ActionBtn onClick={() => setCreateStep(1)}>← BACK</ActionBtn>
            <ActionBtn primary onClick={() => setCreateStep(3)}>REVIEW & LAUNCH →</ActionBtn>
          </div>
        </div>
      )}

      {/* Step 3: Launch Review */}
      {createStep === 3 && (
        <div style={{ maxWidth: 600 }}>
          <div style={{ background: "#141009", border: "1px solid #2C1810", padding: 22, borderRadius: 2, marginBottom: 24 }}>
            <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B4513", letterSpacing: 2, margin: "0 0 16px 0" }}>EVENT SUMMARY</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[
                ["Name:", eventDraft.name || "Untitled"],
                ["Category:", eventDraft.category || "None"],
                ["Venue:", eventDraft.venue || "None"],
                ["Ticket Price:", `$${eventDraft.ticketPrice}`],
                ["Capacity:", `${eventDraft.capacity}`],
              ].map(([l, v]) => (
                <Fragment key={l}>
                  <span style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F" }}>{l}</span>
                  <span style={{ fontFamily: "'Courier New', monospace", fontSize: 13, color: "#FAF0DC" }}>{v}</span>
                </Fragment>
              ))}
            </div>
            {liveScore !== null && (
              <div style={{ marginTop: 20, textAlign: "center" }}>
                <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", margin: "0 0 6px 0" }}>NEXUS SCORE</p>
                <p style={{ fontSize: 52, fontWeight: "bold", color: scoreColor(liveScore), margin: 0, fontFamily: "'Courier New', monospace" }}>{liveScore}</p>
                <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: scoreColor(liveScore), margin: "6px 0 0 0", fontWeight: "bold" }}>
                  {liveScore >= 75 ? "GREEN ZONE — READY TO LAUNCH" : liveScore >= 50 ? "YELLOW ZONE — OPTIMIZATION RECOMMENDED" : "RED ZONE — ADJUSTMENTS REQUIRED"}
                </p>
              </div>
            )}
          </div>
          <div style={{ display: "flex", gap: 8, justifyContent: "space-between" }}>
            <ActionBtn onClick={() => setCreateStep(2)}>← BACK</ActionBtn>
            <ActionBtn primary disabled={!eventDraft.name} onClick={triggerCelebration}>
              ◆ LAUNCH EVENT
            </ActionBtn>
          </div>
        </div>
      )}
    </div>
  );
}
