import { signals } from "../data/constants";
import { scoreColor } from "../data/utils";
import { styles as s } from "../data/styles";
import StatCard from "../components/StatCard";

export default function SignalTab() {
  return (
    <div>
      <p style={s.sectionLabel}>NOVELTY & SENTIMENT SCANNER</p>
      <p style={s.sectionTitle}>Cultural Intelligence Feed</p>
      <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F", marginBottom: 16, lineHeight: 1.5 }}>
        Scanning: Public discourse, social platforms, podcast transcripts, search trends, news sentiment
      </p>
      <div style={s.grid3}>
        <StatCard label="Signals Tracked" value="2,847" sub="this week" />
        <StatCard label="Actionable" value="23" sub="event opportunities" accent="#2D6A4F" />
        <StatCard label="Top Velocity" value="+340%" sub="chess content" />
      </div>
      {signals.map((sig) => (
        <div key={sig.topic} style={s.card(sig.score > 90)}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <p style={{ fontSize: 17, fontWeight: "bold", color: "#FAF0DC", margin: 0 }}>{sig.topic}</p>
                <span style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#2D6A4F", fontWeight: "bold" }}>{sig.trend}</span>
                <span style={{
                  fontFamily: "'Courier New', monospace", fontSize: 11, padding: "3px 8px",
                  background: sig.velocity === "accelerating" ? "rgba(45,106,79,0.15)" : "rgba(139,115,85,0.15)",
                  color: sig.velocity === "accelerating" ? "#2D6A4F" : "#8B7355",
                  border: `1px solid ${sig.velocity === "accelerating" ? "#2D6A4F" : "#3C2415"}`,
                  letterSpacing: 1, borderRadius: 2,
                }}>
                  {sig.velocity.toUpperCase()}
                </span>
              </div>
              <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F", margin: "6px 0 0 0" }}>
                Source: {sig.source} · Sentiment: {sig.sentiment}
              </p>
            </div>
            <div style={{ textAlign: "right", minWidth: 50 }}>
              <p style={{ fontSize: 26, fontWeight: "bold", color: scoreColor(sig.score), margin: 0, fontFamily: "'Courier New', monospace" }}>{sig.score}</p>
              <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", margin: 0 }}>RELEVANCE</p>
            </div>
          </div>
          <p style={{ fontSize: 14, color: "#8B7355", margin: 0, fontStyle: "italic", lineHeight: 1.6 }}>
            ↳ {sig.relevance}
          </p>
        </div>
      ))}
    </div>
  );
}
