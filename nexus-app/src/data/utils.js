// ═══ PSYCHOLOGY-DRIVEN UTILITY ═══

// [Color Psychology] Score-to-color emotional gradient
export const scoreColor = (score) => {
  if (score >= 85) return "#2D6A4F"; // Green — optimal, trust, growth
  if (score >= 70) return "#B8860B"; // Gold — strong, authority
  if (score >= 41) return "#DAA520"; // Amber — caution, optimism
  return "#CC3333";                  // Rust — danger, urgency
};

// Stable seeded pseudo-random for render-safe "random" values
// FIX: replaces Math.random() in render which caused flickering
export const seededValue = (seed, min, max) => {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  const normalized = x - Math.floor(x);
  return Math.floor(normalized * (max - min + 1)) + min;
};
