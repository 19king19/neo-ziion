import { useState } from "react";
import { venueSlots } from "../data/constants";
import { seededValue } from "../data/utils";
import { styles as s } from "../data/styles";
import StatCard from "../components/StatCard";
import ScoreBar from "../components/ScoreBar";
import ActionBtn from "../components/ActionBtn";
import { BestDealBadge } from "../components/Badges";

export default function ScoutTab() {
  const [selectedVenue, setSelectedVenue] = useState(null);
  const [showAllVenues, setShowAllVenues] = useState(false);

  // [Von Restorff] Best deal = highest savings
  const bestDealIdx = venueSlots.reduce(
    (best, slot, i) => (parseInt(slot.savings) > parseInt(venueSlots[best].savings) ? i : best),
    0
  );

  const displayed = showAllVenues ? venueSlots : venueSlots.slice(0, 3);

  return (
    <div>
      <p style={s.sectionLabel}>VENUE INTELLIGENCE</p>
      <p style={s.sectionTitle}>Dead-Time Inventory — Houston</p>
      <div style={s.grid3}>
        <StatCard label="Active Venues" value="47" sub="12 new this month" />
        <StatCard label="Dead Hours/Week" value="312" sub="avg 6.6 hrs/venue" />
        <StatCard label="Avg Savings" value="74%" sub="vs. market rate" accent="#2D6A4F" />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <p style={{ ...s.sectionLabel, margin: 0 }}>AVAILABLE DEAD-TIME SLOTS</p>
        <span style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#5C4A3A" }}>{venueSlots.length} slots available</span>
      </div>
      {displayed.map((slot, i) => {
        const realIdx = venueSlots.indexOf(slot);
        const isBest = realIdx === bestDealIdx;
        return (
          <div key={slot.venue} style={{
            ...s.card(isBest),
            borderColor: selectedVenue === realIdx ? "#B8860B" : (isBest ? "#B8860B" : "#2C1810"),
          }} onClick={() => setSelectedVenue(selectedVenue === realIdx ? null : realIdx)}>
            <div style={{ display: "grid", gridTemplateColumns: "2.5fr 1fr 1fr 1fr", alignItems: "center", gap: 12 }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <p style={{ fontSize: 16, fontWeight: "bold", color: "#FAF0DC", margin: 0 }}>{slot.venue}</p>
                  {isBest && <BestDealBadge />}
                </div>
                <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F", margin: "4px 0 0 0" }}>{slot.day} · {slot.time}</p>
                <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B7355", margin: "2px 0 0 0" }}>{slot.vibe}</p>
              </div>
              <div style={{ textAlign: "center" }}>
                <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", margin: 0, textDecoration: "line-through" }}>{slot.normal}</p>
                <p style={{ fontSize: 20, fontWeight: "bold", color: "#2D6A4F", margin: "2px 0 0 0" }}>{slot.nexus}</p>
              </div>
              <div style={{ textAlign: "center" }}>
                <p style={{ fontSize: 24, fontWeight: "bold", color: "#B8860B", margin: 0 }}>{slot.savings}</p>
                <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", margin: 0 }}>SAVINGS</p>
              </div>
              <div style={{ textAlign: "right" }}>
                <ActionBtn>BOOK</ActionBtn>
              </div>
            </div>
            {selectedVenue === realIdx && (
              <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid #2C1810", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
                <div>
                  <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#8B4513", margin: "0 0 4px 0" }}>CAPACITY</p>
                  <p style={{ fontFamily: "'Courier New', monospace", fontSize: 15, color: "#FAF0DC", margin: 0 }}>{slot.capacity} ppl</p>
                </div>
                <div>
                  <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#8B4513", margin: "0 0 4px 0" }}>EQUIPMENT</p>
                  <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B7355", margin: 0 }}>{slot.equipment}</p>
                </div>
                <div>
                  <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#8B4513", margin: "0 0 4px 0" }}>NEXUS RATING</p>
                  {/* FIX: seededValue instead of Math.random() */}
                  <ScoreBar score={seededValue(realIdx + 100, 70, 95)} label="" color="#B8860B" />
                </div>
              </div>
            )}
          </div>
        );
      })}
      {!showAllVenues && venueSlots.length > 3 && (
        <button style={s.showMore} onClick={() => setShowAllVenues(true)}>
          SHOW ALL {venueSlots.length} VENUES ↓
        </button>
      )}
      {showAllVenues && (
        <button style={s.showMore} onClick={() => setShowAllVenues(false)}>SHOW LESS ↑</button>
      )}
    </div>
  );
}
