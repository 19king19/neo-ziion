// ═══════════════════════════════════════════════════════════════════════════
// NEXUS v3 — DATA LAYER
// ═══════════════════════════════════════════════════════════════════════════

export const TABS = ["SCOUT", "MATCH", "PULSE", "FORGE", "SIGNAL", "CREATE"];

export const mockEvents = [
  { id: 1, name: "Hip-Hop & Chess Night", venue: "Honey's Coffee House", city: "Houston", time: "Tue 6-9pm", score: 88, demand: 342, category: "Games", status: "GREENLIT", venueDiscount: "72%", influencer: "Chess.com Houston", influencerReach: "45K", profitFloor: "$2,100", novelty: 94, ticketPrice: 25, capacity: 80, breakeven: 42 },
  { id: 2, name: "Art in the Park: Live Mural Session", venue: "Discovery Green", city: "Houston", time: "Sat 10am-2pm", score: 81, demand: 567, category: "Art", status: "GREENLIT", venueDiscount: "FREE (public)", influencer: "HTX Art Collective", influencerReach: "28K", profitFloor: "$1,800", novelty: 76, ticketPrice: 15, capacity: 200, breakeven: 65 },
  { id: 3, name: "Sovereign Minds: Financial Literacy Workshop", venue: "Third Ward Community Center", city: "Houston", time: "Wed 7-9pm", score: 73, demand: 189, category: "Education", status: "OPTIMIZING", venueDiscount: "85%", influencer: "Wallstreet Trapper", influencerReach: "1.2M", profitFloor: "$4,200", novelty: 62, ticketPrice: 40, capacity: 120, breakeven: 38 },
  { id: 4, name: "Comedy + Cooking: Stand-Up Supper Club", venue: "Lucille's Kitchen", city: "Houston", time: "Thu 8-11pm", score: 91, demand: 445, category: "Hybrid", status: "GREENLIT", venueDiscount: "60%", influencer: "Druski", influencerReach: "8.4M", profitFloor: "$6,800", novelty: 97, ticketPrice: 55, capacity: 100, breakeven: 30 },
  { id: 5, name: "Breathwork & Bass: Meditation x DJ Set", venue: "Warehouse Live (Patio)", city: "Houston", time: "Sun 4-7pm", score: 67, demand: 156, category: "Wellness", status: "OPTIMIZING", venueDiscount: "78%", influencer: "Local Wellness IG", influencerReach: "12K", profitFloor: "$900", novelty: 85, ticketPrice: 30, capacity: 60, breakeven: 28 },
  { id: 6, name: "Vinyl & Vino: Rare Record Listening Party", venue: "POST Houston (Rooftop)", city: "Houston", time: "Fri 7-11pm", score: 84, demand: 298, category: "Music", status: "GREENLIT", venueDiscount: "65%", influencer: "DJ Mr. Rogers", influencerReach: "67K", profitFloor: "$3,400", novelty: 88, ticketPrice: 35, capacity: 90, breakeven: 35 },
];

export const dreamEvents = [
  { id: 1, title: "Umar Johnson x 19keys: The Sit-Down", votes: 8742, funded: 67, threshold: "$15,000", raised: "$10,050", daysLeft: 14, hot: true, city: "Houston", category: "Conversation" },
  { id: 2, title: "Nipsey Hussle Tribute: Marathon Continues Panel", votes: 12340, funded: 89, threshold: "$25,000", raised: "$22,250", daysLeft: 6, hot: true, city: "Los Angeles", category: "Cultural" },
  { id: 3, title: "Black Wall Street Summit: 50 Entrepreneurs, 1 Room", votes: 5621, funded: 43, threshold: "$20,000", raised: "$8,600", daysLeft: 21, hot: false, city: "Atlanta", category: "Business" },
  { id: 4, title: "Patrice O'Neal Comedy Legacy Night", votes: 3890, funded: 31, threshold: "$12,000", raised: "$3,720", daysLeft: 30, hot: false, city: "New York", category: "Comedy" },
  { id: 5, title: "Sovereign Minds Dinner: 12 Leaders, No Cameras", votes: 6200, funded: 55, threshold: "$18,000", raised: "$9,900", daysLeft: 18, hot: true, city: "Houston", category: "Exclusive" },
];

export const venueSlots = [
  { venue: "Honey's Coffee House", day: "Tuesday", time: "2pm-6pm", normal: "$800", nexus: "$200", savings: "75%", vibe: "Intimate/Creative", capacity: 60, equipment: "Sound system, projector", tier: "intimate" },
  { venue: "Warehouse Live (Patio)", day: "Sunday", time: "12pm-5pm", normal: "$2,500", nexus: "$550", savings: "78%", vibe: "Industrial/Open Air", capacity: 300, equipment: "Full PA, lights, stage", tier: "premium" },
  { venue: "Lucille's Kitchen", day: "Thursday", time: "3pm-6pm", normal: "$1,200", nexus: "$360", savings: "70%", vibe: "Southern/Upscale", capacity: 80, equipment: "House sound, kitchen access", tier: "standard" },
  { venue: "Discovery Green Pavilion", day: "Wednesday", time: "10am-2pm", normal: "$1,500", nexus: "$375", savings: "75%", vibe: "Outdoor/Community", capacity: 500, equipment: "Power hookups, open space", tier: "premium" },
  { venue: "POST Houston (Rooftop)", day: "Monday", time: "5pm-9pm", normal: "$3,000", nexus: "$600", savings: "80%", vibe: "Skyline/Premium", capacity: 150, equipment: "Full setup available", tier: "premium" },
  { venue: "The MATCH", day: "Friday", time: "1pm-5pm", normal: "$1,800", nexus: "$450", savings: "75%", vibe: "Gallery/Artistic", capacity: 100, equipment: "Gallery walls, basic AV", tier: "standard" },
];

export const signals = [
  { topic: "Chess content", trend: "+340%", source: "YouTube/TikTok", sentiment: "Peak", relevance: "Hip-Hop x Chess crossover events at all-time demand", score: 96, velocity: "accelerating" },
  { topic: "Loneliness epidemic", trend: "+180%", source: "News/Social", sentiment: "Urgent", relevance: "Community connection events positioned as health interventions", score: 89, velocity: "steady" },
  { topic: "Black entrepreneurship", trend: "+95%", source: "Podcasts/X", sentiment: "Motivated", relevance: "Financial literacy and business workshops in high demand", score: 84, velocity: "accelerating" },
  { topic: "Comedy renaissance", trend: "+220%", source: "Streaming/Social", sentiment: "Hungry", relevance: "Live comedy in intimate venues outperforming stadium shows per-capita", score: 91, velocity: "accelerating" },
  { topic: "Wellness masculinity", trend: "+160%", source: "Podcasts/IG", sentiment: "Seeking", relevance: "Men's wellness circles and breathwork events emerging category", score: 78, velocity: "steady" },
  { topic: "Vinyl revival", trend: "+110%", source: "IG/Reddit", sentiment: "Passionate", relevance: "Record listening parties and vinyl markets growing 3x year-over-year", score: 82, velocity: "steady" },
];

// [Hick's Law] Grouped categories instead of flat list
export const categoryGroups = [
  { group: "Social", items: ["Social Connection", "Food & Drink", "Experience Design"] },
  { group: "Cultural", items: ["Cultural", "Art & Culture", "Music & Sound"] },
  { group: "Professional", items: ["Mind & Ideas", "Professional", "Education"] },
  { group: "Hybrid", items: ["Hybrid", "Wellness", "Niche/Novelty"] },
];

// [Peak-End] Rotating insights for session exits
export const exitInsights = [
  "Your next event is one decision away.",
  "The culture is waiting for what you build.",
  "Dead space becomes living culture \u2014 through you.",
  "Every sovereign event starts with a single score.",
];
