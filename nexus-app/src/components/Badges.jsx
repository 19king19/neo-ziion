// [Zeigarnik] Tab badge for incomplete items
export function TabBadge({ count }) {
  if (count === undefined || count === null) return null;
  return (
    <span style={{
      fontFamily: "'Courier New', monospace", fontSize: 9, minWidth: 18, height: 18,
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      background: typeof count === "string" ? "#B8860B" : "#2D6A4F",
      color: "#0D0906", borderRadius: 9, fontWeight: "bold", marginLeft: 6,
    }}>
      {count}
    </span>
  );
}

// [Von Restorff] Best deal badge
export function BestDealBadge() {
  return (
    <span style={{
      fontFamily: "'Courier New', monospace", fontSize: 11, padding: "3px 10px",
      background: "#B8860B", color: "#0D0906", letterSpacing: 2, fontWeight: "bold",
      borderRadius: 1, display: "inline-block",
    }}>
      BEST DEAL
    </span>
  );
}

// [Zeigarnik] Almost-there label for high-funded dreams
export function AlmostThere() {
  return (
    <span style={{
      fontFamily: "'Courier New', monospace", fontSize: 11, color: "#B8860B",
      fontWeight: "bold", letterSpacing: 2,
      animation: "pulse 1.5s ease-in-out infinite",
    }}>
      ALMOST THERE
    </span>
  );
}
