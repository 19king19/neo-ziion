export default function ActionBtn({ children, onClick, primary, disabled, fullWidth }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{
      fontFamily: "'Courier New', monospace", fontSize: 12, letterSpacing: 2, fontWeight: primary ? "bold" : "normal",
      padding: "14px 24px", minHeight: 48,
      cursor: disabled ? "default" : "pointer",
      border: primary ? "none" : "1px solid #3C2415",
      background: primary ? (disabled ? "#5C4A3A" : "#B8860B") : "transparent",
      color: primary ? "#0D0906" : "#8B7355",
      transition: "all 0.15s ease",
      borderRadius: 2, opacity: disabled ? 0.5 : 1,
      width: fullWidth ? "100%" : "auto",
      textTransform: "uppercase",
    }}>
      {children}
    </button>
  );
}
