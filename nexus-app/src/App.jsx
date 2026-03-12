import { useState, useEffect, useCallback } from "react";
import { TABS, mockEvents, dreamEvents } from "./data/constants";
import { styles as s } from "./data/styles";
import { TabBadge } from "./components/Badges";

import ScoutTab from "./tabs/ScoutTab";
import MatchTab from "./tabs/MatchTab";
import PulseTab from "./tabs/PulseTab";
import ForgeTab from "./tabs/ForgeTab";
import SignalTab from "./tabs/SignalTab";
import CreateTab from "./tabs/CreateTab";

export default function NexusApp() {
  const [activeTab, setActiveTab] = useState("SCOUT");
  const [animateIn, setAnimateIn] = useState(true);
  const [time, setTime] = useState(new Date());
  const [hasDraft, setHasDraft] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Tab transition animation
  useEffect(() => {
    setAnimateIn(false);
    const t = setTimeout(() => setAnimateIn(true), 40);
    return () => clearTimeout(t);
  }, [activeTab]);

  const handleDraftChange = useCallback((isDrafting) => {
    setHasDraft(isDrafting);
  }, []);

  const handleTabSwitch = (tab) => {
    setActiveTab(tab);
  };

  const renderContent = () => {
    switch (activeTab) {
      case "SCOUT": return <ScoutTab />;
      case "MATCH": return <MatchTab />;
      case "PULSE": return <PulseTab />;
      case "FORGE": return <ForgeTab />;
      case "SIGNAL": return <SignalTab />;
      case "CREATE": return <CreateTab onDraftChange={handleDraftChange} />;
      default: return null;
    }
  };

  return (
    <div style={s.app}>
      {/* Parchment noise texture */}
      <div style={s.noise} />

      {/* Pulse animation keyframes */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        * { box-sizing: border-box; }
        body { margin: 0; padding: 0; background: #0D0906; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0D0906; }
        ::-webkit-scrollbar-thumb { background: #3C2415; border-radius: 3px; }
        ::selection { background: rgba(184,134,11,0.3); color: #FAF0DC; }
      `}</style>

      {/* Header */}
      <div style={s.header}>
        <div style={s.logo}>
          <span style={s.logoText}>◆ NEXUS</span>
          <span style={s.logoSub}>AI EVENT ORCHESTRATION</span>
        </div>
        <div style={s.clock}>
          <div style={{ fontSize: 13 }}>{time.toLocaleTimeString("en-US", { hour12: false })} EST</div>
          <div style={{ fontSize: 11 }}>HOUSTON, TX</div>
        </div>
      </div>

      {/* Navigation tabs */}
      <nav style={s.nav}>
        {TABS.map((tab) => (
          <button key={tab} style={s.tab(activeTab === tab)} onClick={() => handleTabSwitch(tab)}>
            {tab}
            {tab === "FORGE" && <TabBadge count={mockEvents.length} />}
            {tab === "PULSE" && <TabBadge count={dreamEvents.filter((d) => d.hot).length} />}
            {tab === "CREATE" && hasDraft && <TabBadge count="!" />}
          </button>
        ))}
      </nav>

      {/* Content area */}
      <div style={s.content(animateIn)}>
        {renderContent()}
      </div>

      {/* Footer */}
      <div style={{
        position: "fixed", bottom: 0, left: 0, right: 0,
        padding: "10px 24px",
        background: "linear-gradient(transparent, #0D0906 60%)",
        display: "flex", justifyContent: "center",
      }}>
        <p style={{ fontFamily: "'Courier New', monospace", fontSize: 11, color: "#3C2415", letterSpacing: 3 }}>
          SOVEREIGN MIND MEDIA © 2026 — CONNECTING DEAD SPACE TO LIVING CULTURE
        </p>
      </div>
    </div>
  );
}
