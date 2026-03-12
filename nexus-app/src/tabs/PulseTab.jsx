import { useState } from "react";
import { dreamEvents, exitInsights } from "../data/constants";
import { styles as s } from "../data/styles";
import StatCard from "../components/StatCard";
import ActionBtn from "../components/ActionBtn";
import { AlmostThere } from "../components/Badges";

export default function PulseTab() {
  const [dreamFilter, setDreamFilter] = useState("ALL");
  const [showAllDreams, setShowAllDreams] = useState(false);

  const categories = ["ALL", ...new Set(dreamEvents.map((e) => e.category))];
  const filtered = dreamFilter === "ALL" ? dreamEvents : dreamEvents.filter((e) => e.category === dreamFilter);
  const displayed = showAllDreams ? filtered : filtered.slice(0, 3);

  return (
    <div>
      <p style={s.sectionLabel}>COMMUNITY DEMAND SIGNAL</p>
      <p style={s.sectionTitle}>Dream Events — Live Funding</p>
      <div style={s.grid3}>
        <StatCard label="Active Dreams" value={dreamEvents.length} sub="across 4 cities" />
        <StatCard label="Total Committed" value="$54,520" sub="in blockchain escrow" accent="#2D6A4F" />
        <StatCard label="Avg Funded" value="57%" sub="toward thresholds" />
      </div>
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {categories.map((cat) => (
          <button key={cat} onClick={() => setDreamFilter(cat)} style={{
            fontFamily: "'Courier New', monospace", fontSize: 11, padding: "8px 14px", letterSpacing: 2,
            background: dreamFilter === cat ? "#B8860B" : "none",
            color: dreamFilter === cat ? "#0D0906" : "#6B5B4F",
            border: dreamFilter === cat ? "none" : "1px solid #2C1810",
            cursor: "pointer", borderRadius: 2, minHeight: 36,
          }}>
            {cat}
          </button>
        ))}
      </div>
      {displayed.map((event) => (
        <div key={event.id} style={{
          ...s.card(event.hot && event.funded > 75),
          position: "relative", overflow: "hidden",
          boxShadow: event.hot && event.funded > 75 ? "0 0 16px rgba(184,134,11,0.12)" : "none",
        }}>
          {event.hot && (
            <div style={{
              position: "absolute", top: 0, right: 0,
              fontFamily: "'Courier New', monospace", fontSize: 11, padding: "4px 12px",
              background: "#8B4513", color: "#FAF0DC", letterSpacing: 2,
            }}>
              TRENDING
            </div>
          )}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
            <div>
              <p style={{ fontSize: 18, fontWeight: "bold", color: "#FAF0DC", margin: 0 }}>{event.title}</p>
              <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F", margin: "6px 0 0 0" }}>
                {event.votes.toLocaleString()} votes · {event.daysLeft} days remaining · {event.city}
              </p>
            </div>
            <div style={{ textAlign: "right", minWidth: 70 }}>
              <p style={{ fontSize: 24, fontWeight: "bold", color: event.funded > 75 ? "#2D6A4F" : "#B8860B", margin: 0 }}>{event.funded}%</p>
              <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", margin: 0 }}>FUNDED</p>
              {event.funded >= 80 && <AlmostThere />}
            </div>
          </div>
          <div style={{ height: 8, background: "#2C1810", borderRadius: 1, overflow: "hidden" }}>
            <div style={{
              width: `${event.funded}%`, height: "100%",
              background: event.hot ? "linear-gradient(90deg, #B8860B, #DAA520)" : "linear-gradient(90deg, #5C4A3A, #8B7355)",
              borderRadius: 1, transition: "width 1.5s ease",
            }} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8 }}>
            <span style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B7355" }}>{event.raised} raised</span>
            <span style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F" }}>Goal: {event.threshold}</span>
          </div>
          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
            <ActionBtn primary fullWidth>COMMIT FUNDS</ActionBtn>
            <ActionBtn>SHARE</ActionBtn>
          </div>
          <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#5C4A3A", margin: "10px 0 0 0", textAlign: "center", lineHeight: 1.4 }}>
            ◆ BLOCKCHAIN ESCROW — FUNDS LOCKED UNTIL THRESHOLD MET OR AUTO-REFUND ◆
          </p>
        </div>
      ))}
      {!showAllDreams && filtered.length > 3 && (
        <button style={s.showMore} onClick={() => setShowAllDreams(true)}>
          SHOW ALL {filtered.length} DREAM EVENTS ↓
        </button>
      )}
      {showAllDreams && filtered.length > 3 && (
        <button style={s.showMore} onClick={() => setShowAllDreams(false)}>SHOW LESS ↑</button>
      )}
      <p style={{ fontFamily: "Georgia", fontSize: 14, color: "#3C2415", textAlign: "center", marginTop: 24, fontStyle: "italic", lineHeight: 1.6 }}>
        {exitInsights[Math.floor(Date.now() / 15000) % exitInsights.length]}
      </p>
    </div>
  );
}
