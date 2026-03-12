export default function StatCard({ label, value, sub, accent }) {
  return (
    <div style={{
      background: "#141009", border: "1px solid #2C1810", padding: "16px 18px", borderRadius: 2, flex: 1,
      transition: "border-color 0.2s ease",
    }}>
      <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", letterSpacing: 3, textTransform: "uppercase", margin: "0 0 6px 0" }}>{label}</p>
      <p style={{ fontSize: 28, fontWeight: "bold", color: accent || "#B8860B", margin: "0 0 4px 0", lineHeight: 1.1, fontFamily: "'Courier New', monospace" }}>{value}</p>
      {sub && <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#5C4A3A", margin: 0, lineHeight: 1.4 }}>{sub}</p>}
    </div>
  );
}
