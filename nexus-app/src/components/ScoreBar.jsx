export default function ScoreBar({ score, label, color }) {
  return (
    <div style={{ marginBottom: 12 }}>
      {label && (
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
          <span style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#8B7355", letterSpacing: 1, textTransform: "uppercase" }}>{label}</span>
          <span style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: color || "#B8860B", fontWeight: "bold" }}>{score}</span>
        </div>
      )}
      <div style={{ height: 6, background: "#2C1810", borderRadius: 1, overflow: "hidden" }}>
        <div style={{
          width: `${Math.min(score, 100)}%`, height: "100%",
          background: `linear-gradient(90deg, ${color || "#B8860B"}, ${color || "#DAA520"})`,
          borderRadius: 1,
          transition: "width 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)"
        }} />
      </div>
    </div>
  );
}
