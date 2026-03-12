import { mockEvents } from "../data/constants";
import { seededValue } from "../data/utils";
import { scoreColor } from "../data/utils";
import { styles as s } from "../data/styles";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";

export default function MatchTab() {
  const topEventId = mockEvents.reduce((top, e) => (e.score > (top?.score || 0) ? e : top), null)?.id;

  return (
    <div>
      <p style={s.sectionLabel}>INFLUENCER DEPLOYMENT</p>
      <p style={s.sectionTitle}>Active Matches — This Week</p>
      <div style={s.grid3}>
        <StatCard label="Matched" value="14" sub="influencer-event pairs" />
        <StatCard label="Total Reach" value="11.2M" sub="combined audience" accent="#2D6A4F" />
        <StatCard label="Avg ROI" value="4.2x" sub="draw vs. compensation" />
      </div>
      {mockEvents.filter((e) => e.influencer).map((event) => (
        <div key={event.id} style={{ ...s.card(event.id === topEventId), display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div>
            <p style={{ fontSize: 16, fontWeight: "bold", color: "#FAF0DC", margin: 0 }}>{event.name}</p>
            <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F", margin: "6px 0" }}>
              {event.venue} · {event.time}
            </p>
            <StatusBadge status={event.status} />
          </div>
          <div style={{ borderLeft: "1px solid #2C1810", paddingLeft: 16 }}>
            <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#8B4513", letterSpacing: 2, margin: "0 0 4px 0" }}>MATCHED INFLUENCER</p>
            <p style={{ fontSize: 15, color: "#B8860B", fontWeight: "bold", margin: "0 0 4px 0" }}>{event.influencer}</p>
            <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F", margin: 0 }}>
              {/* FIX: seededValue instead of Math.random() */}
              Reach: {event.influencerReach} · Overlap: {seededValue(event.id * 7, 60, 89)}%
            </p>
            <div style={{ marginTop: 8, display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{
                fontFamily: "'Courier New', monospace", fontSize: 11, padding: "3px 8px",
                background: "#1A140D", border: "1px solid #3C2415", color: "#8B7355",
              }}>
                {event.influencerReach.includes("M")
                  ? "% OF DOOR"
                  : parseInt(event.influencerReach) > 30
                  ? "FREE + BAR"
                  : "FREE TICKET"}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
