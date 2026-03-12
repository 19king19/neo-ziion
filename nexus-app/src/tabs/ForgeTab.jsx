import { Fragment, useState, useMemo } from "react";
import { mockEvents, exitInsights } from "../data/constants";
import { scoreColor, seededValue } from "../data/utils";
import { styles as s } from "../data/styles";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import ScoreBar from "../components/ScoreBar";

export default function ForgeTab() {
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAllEvents, setShowAllEvents] = useState(false);

  const filteredEvents = useMemo(
    () =>
      mockEvents.filter(
        (e) =>
          !searchQuery ||
          e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          e.venue.toLowerCase().includes(searchQuery.toLowerCase()) ||
          e.category.toLowerCase().includes(searchQuery.toLowerCase())
      ),
    [searchQuery]
  );

  const topEventId = filteredEvents.reduce((top, e) => (e.score > (top?.score || 0) ? e : top), null)?.id;

  const groupedEvents = {
    GREENLIT: filteredEvents.filter((e) => e.status === "GREENLIT"),
    OPTIMIZING: filteredEvents.filter((e) => e.status === "OPTIMIZING"),
  };

  const displayed = showAllEvents ? filteredEvents : filteredEvents.slice(0, 3);

  const renderEventCard = (event) => (
    <div
      key={event.id}
      style={{
        ...s.card(event.id === topEventId),
        borderColor: selectedEvent?.id === event.id ? "#B8860B" : event.id === topEventId ? "#B8860B" : "#2C1810",
      }}
      onClick={() => setSelectedEvent(selectedEvent?.id === event.id ? null : event)}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: selectedEvent?.id === event.id ? 16 : 0 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <p style={{ fontSize: 16, fontWeight: "bold", color: "#FAF0DC", margin: 0 }}>{event.name}</p>
            <StatusBadge status={event.status} />
          </div>
          <p style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#6B5B4F", margin: "6px 0 0 0" }}>
            {event.venue} · {event.time} · {event.category}
          </p>
        </div>
        <div style={{ textAlign: "right" }}>
          <p style={{ fontSize: 32, fontWeight: "bold", color: scoreColor(event.score), margin: 0, lineHeight: 1, fontFamily: "'Courier New', monospace" }}>{event.score}</p>
          <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", margin: 0 }}>NEXUS SCORE</p>
        </div>
      </div>
      {selectedEvent?.id === event.id && (
        <div style={{ borderTop: "1px solid #2C1810", paddingTop: 14 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
            <div>
              <ScoreBar score={event.demand > 400 ? 92 : event.demand > 200 ? 71 : 55} label="Demand Signal" color="#2D6A4F" />
              <ScoreBar score={parseInt(event.venueDiscount) > 70 ? 88 : 65} label="Venue Efficiency" color="#B8860B" />
              <ScoreBar score={event.influencerReach.includes("M") ? 95 : parseInt(event.influencerReach) > 30 ? 72 : 48} label="Influencer Leverage" color="#DAA520" />
              <ScoreBar score={parseInt(event.profitFloor.replace(/[^0-9]/g, "")) > 4000 ? 90 : 68} label="Profit Floor" color="#2D6A4F" />
            </div>
            <div>
              <ScoreBar score={event.novelty} label="Novelty Index" color="#8B4513" />
              {/* FIX: seededValue instead of Math.random() */}
              <ScoreBar score={seededValue(event.id * 13, 65, 85)} label="Cultural Timing" color="#5C4A3A" />
              <ScoreBar score={event.category === "Hybrid" ? 94 : event.demand < 200 ? 88 : 62} label="Connection Density" color="#6B5B4F" />
              <div style={{ marginTop: 10, padding: 12, background: "#0D0906", border: "1px solid #2C1810", borderRadius: 2 }}>
                <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#6B5B4F", margin: "0 0 8px 0" }}>PROJECTED P&L</p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
                  {[
                    ["Venue:", `${event.venueDiscount} off`],
                    ["Demand:", `${event.demand} signals`],
                    ["Breakeven:", `${event.breakeven} tickets`],
                    ["Capacity:", `${event.capacity} max`],
                  ].map(([l, v]) => (
                    <Fragment key={l}>
                      <span style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B7355" }}>{l}</span>
                      <span style={{ fontFamily: "'Courier New', monospace", fontSize: 12, color: "#8B7355", textAlign: "right" }}>{v}</span>
                    </Fragment>
                  ))}
                </div>
                <div style={{ borderTop: "1px solid #2C1810", marginTop: 8, paddingTop: 8, display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontFamily: "'Courier New', monospace", fontSize: 13, color: "#2D6A4F", fontWeight: "bold" }}>Floor:</span>
                  <span style={{ fontFamily: "'Courier New', monospace", fontSize: 15, color: "#2D6A4F", fontWeight: "bold" }}>{event.profitFloor}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div>
      <p style={s.sectionLabel}>EVENT PROFITABILITY ENGINE</p>
      <p style={s.sectionTitle}>Active Event Pipeline — Scored</p>
      <div style={{ marginBottom: 16 }}>
        <input
          placeholder="Search events, venues, categories..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ ...s.input, maxWidth: 420 }}
        />
      </div>
      <div style={s.grid3}>
        <StatCard label="Pipeline Events" value={filteredEvents.length} />
        <StatCard label="Greenlit" value={filteredEvents.filter((e) => e.status === "GREENLIT").length} accent="#2D6A4F" />
        <StatCard label="Avg Score" value={Math.round(filteredEvents.reduce((a, e) => a + e.score, 0) / filteredEvents.length)} />
      </div>

      {showAllEvents ? (
        <>
          {Object.entries(groupedEvents).map(
            ([status, events]) =>
              events.length > 0 && (
                <div key={status}>
                  <p style={s.groupHeader}>
                    {status} — {events.length} events
                  </p>
                  {events.map((event) => renderEventCard(event))}
                </div>
              )
          )}
        </>
      ) : (
        [...displayed].sort((a, b) => b.score - a.score).map((event) => renderEventCard(event))
      )}

      {!showAllEvents && filteredEvents.length > 3 && (
        <button style={s.showMore} onClick={() => setShowAllEvents(true)}>
          SHOW ALL {filteredEvents.length} EVENTS ↓
        </button>
      )}
      {showAllEvents && (
        <button style={s.showMore} onClick={() => setShowAllEvents(false)}>
          SHOW LESS ↑
        </button>
      )}
      <p style={{ fontFamily: "Georgia", fontSize: 14, color: "#3C2415", textAlign: "center", marginTop: 24, fontStyle: "italic" }}>
        {exitInsights[Math.floor(Date.now() / 15000) % exitInsights.length]}
      </p>
    </div>
  );
}
