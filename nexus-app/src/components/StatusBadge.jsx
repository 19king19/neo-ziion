const colors = {
  GREENLIT: "#2D6A4F",
  OPTIMIZING: "#B8860B",
  PENDING: "#6B5B4F",
  FUNDED: "#1B4332",
  LIVE: "#2D6A4F",
};

export default function StatusBadge({ status }) {
  const isOptimizing = status === "OPTIMIZING";
  return (
    <span style={{
      fontFamily: "'Courier New', monospace", fontSize: 11, padding: "4px 12px",
      background: colors[status] || "#6B5B4F", color: "#FAF0DC", letterSpacing: 2, borderRadius: 2,
      display: "inline-block",
      animation: isOptimizing ? "pulse 2s ease-in-out infinite" : "none",
    }}>
      {status}
    </span>
  );
}
