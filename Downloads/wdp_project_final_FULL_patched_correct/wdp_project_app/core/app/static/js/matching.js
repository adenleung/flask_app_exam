const STATIC_PROFILES = [
  {
    id: "mdm-chen",
    name: "Mdm Chen Wei Ling",
    age: 68,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Chen",
    location: "Bukit Merah",
    match: "92%",
    bio: "Passionate about learning technology and staying connected with family.",
    matched: ["Tech support", "Friendly learner", "Community-minded"],
    interests: ["WhatsApp", "Cooking", "Stories"],
    goals: ["Learn video calls", "Meet new friends"],
    teach: ["Traditional recipes"],
    learn: ["Social media basics"],
  },
  {
    id: "uncle-kumar",
    name: "Mr Kumar Raj",
    age: 72,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Kumar",
    location: "Jurong East",
    match: "90%",
    bio: "Enjoys learning digital tools and meeting new people.",
    matched: ["Learning circles", "Helpful mentor", "Curious explorer"],
    interests: ["Instagram", "Photography", "Walking"],
    goals: ["Make new friends", "Learn social apps"],
    teach: ["Life stories", "Cooking tips"],
    learn: ["Digital payments"],
  },
  {
    id: "auntie-lei",
    name: "Auntie Lei Mei",
    age: 70,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Lei",
    location: "Tampines",
    match: "88%",
    bio: "Loves sharing recipes and learning new phone features.",
    matched: ["Foodies", "Patient teacher", "Morning learner"],
    interests: ["Baking", "WhatsApp", "Gardening"],
    goals: ["Join a learning circle", "Learn photo editing"],
    teach: ["Baking basics", "Family recipes"],
    learn: ["Photo editing", "Video calls"],
  },
  {
    id: "uncle-rahim",
    name: "Mr Rahim Ismail",
    age: 75,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Rahim",
    location: "Woodlands",
    match: "86%",
    bio: "Enjoys community volunteering and hearing youth stories.",
    matched: ["Community-minded", "Story teller", "Volunteer"],
    interests: ["Volunteering", "Walking", "Photography"],
    goals: ["Meet new friends", "Learn social apps"],
    teach: ["Life stories", "Community tips"],
    learn: ["Instagram", "Digital payments"],
  },
  {
    id: "auntie-siti",
    name: "Mdm Siti Aminah",
    age: 67,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Siti",
    location: "Bedok",
    match: "91%",
    bio: "Curious about tech and loves local history.",
    matched: ["History lover", "Friendly learner", "Early riser"],
    interests: ["History", "Reading", "Cooking"],
    goals: ["Learn apps", "Share stories"],
    teach: ["Local history", "Cooking tips"],
    learn: ["Online banking", "Maps navigation"],
  },
  {
    id: "uncle-wee",
    name: "Mr Wee Jun Kai",
    age: 69,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Wee",
    location: "Hougang",
    match: "87%",
    bio: "Enjoys photography walks and learning new gadgets.",
    matched: ["Photo buddy", "Calm communicator", "Explorer"],
    interests: ["Photography", "Walking", "Gadgets"],
    goals: ["Join outings", "Learn editing"],
    teach: ["Camera basics"],
    learn: ["Photo editing", "Cloud backup"],
  },
  {
    id: "auntie-jia",
    name: "Ms Jia Ling",
    age: 66,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Jia",
    location: "Toa Payoh",
    match: "89%",
    bio: "Enjoys crafts and sharing life stories with youths.",
    matched: ["Creative", "Patient mentor", "Warm heart"],
    interests: ["Arts & Crafts", "Music", "Cooking"],
    goals: ["Teach crafts", "Learn chat apps"],
    teach: ["Crafting", "Sewing"],
    learn: ["Chat stickers", "Video calls"],
  },
  {
    id: "auntie-lina",
    name: "Mdm Lina Aisyah",
    age: 71,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Lina",
    location: "Serangoon",
    match: "90%",
    bio: "Loves gardening and wants to learn video calls.",
    matched: ["Calm learner", "Green thumb", "Friendly"],
    interests: ["Gardening", "Reading", "WhatsApp"],
    goals: ["Learn video calls", "Join a circle"],
    teach: ["Plant care", "Local tips"],
    learn: ["Video calls", "Photo sharing"],
  },
  {
    id: "uncle-tan",
    name: "Mr Tan Hong",
    age: 74,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Tan",
    location: "Bishan",
    match: "88%",
    bio: "Enjoys morning walks and learning new apps.",
    matched: ["Early riser", "Curious", "Supportive"],
    interests: ["Walking", "Music", "Photography"],
    goals: ["Learn social apps", "Make friends"],
    teach: ["Life stories"],
    learn: ["Maps navigation", "Photo editing"],
  },
  {
    id: "auntie-joy",
    name: "Ms Joy Tan",
    age: 65,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Joy",
    location: "Kallang",
    match: "87%",
    bio: "Enjoys crafts, baking, and sharing recipes.",
    matched: ["Creative", "Patient", "Community-minded"],
    interests: ["Baking", "Crafts", "Reading"],
    goals: ["Teach crafts", "Learn chat apps"],
    teach: ["Baking basics"],
    learn: ["Chat stickers", "Video calls"],
  },
  {
    id: "uncle-dan",
    name: "Mr Daniel Lim",
    age: 73,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Daniel",
    location: "Queenstown",
    match: "86%",
    bio: "Wants to learn digital payments and stay connected.",
    matched: ["Helpful", "Patient", "Tech curious"],
    interests: ["History", "Walking", "News"],
    goals: ["Learn digital payments", "Meet friends"],
    teach: ["History stories"],
    learn: ["Digital payments", "Online banking"],
  },
  {
    id: "auntie-nora",
    name: "Mdm Nora Aziz",
    age: 69,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Nora",
    location: "Pasir Ris",
    match: "89%",
    bio: "Enjoys storytelling and learning new phone tricks.",
    matched: ["Story teller", "Friendly", "Learner"],
    interests: ["Stories", "Cooking", "Music"],
    goals: ["Learn photo sharing", "Join circles"],
    teach: ["Cooking tips"],
    learn: ["Photo sharing", "Video calls"],
  },
  {
    id: "auntie-rani",
    name: "Mdm Rani Devi",
    age: 66,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Rani",
    location: "Tampines",
    match: "88%",
    bio: "Enjoys community activities and learning new apps with friends.",
    matched: ["Community builder", "Friendly learner", "Warm"],
    interests: ["Volunteering", "Cooking", "Reading"],
    goals: ["Meet new friends", "Learn video calls"],
    teach: ["Cooking tips"],
    learn: ["Video calls", "Photo sharing"],
  },
  {
    id: "uncle-goh",
    name: "Mr Goh Wei Ming",
    age: 71,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Goh",
    location: "Paya Lebar",
    match: "87%",
    bio: "Likes photo walks and wants to try editing apps.",
    matched: ["Photo buddy", "Easygoing", "Explorer"],
    interests: ["Photography", "Walking", "Travel"],
    goals: ["Learn editing", "Join outings"],
    teach: ["Camera basics"],
    learn: ["Photo editing", "Cloud backup"],
  },
  {
    id: "auntie-yuni",
    name: "Ms Yuni Sofia",
    age: 68,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Yuni",
    location: "Yishun",
    match: "86%",
    bio: "Enjoys music and crafting with new friends.",
    matched: ["Creative", "Patient", "Kind"],
    interests: ["Music", "Crafts", "Reading"],
    goals: ["Teach crafts", "Join a circle"],
    teach: ["Crafting", "Sewing"],
    learn: ["Chat stickers", "Video calls"],
  },
  {
    id: "uncle-heng",
    name: "Mr Heng Boon Kiat",
    age: 74,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Heng",
    location: "Ang Mo Kio",
    match: "90%",
    bio: "Wants to learn digital payments and stay updated.",
    matched: ["Tech curious", "Helpful", "Calm"],
    interests: ["News", "History", "Walking"],
    goals: ["Learn online banking", "Meet friends"],
    teach: ["History stories"],
    learn: ["Digital payments", "Online banking"],
  },
  {
    id: "auntie-mei",
    name: "Mdm Mei Fang",
    age: 70,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Mei",
    location: "Clementi",
    match: "89%",
    bio: "Enjoys gardening and learning new phone tricks.",
    matched: ["Green thumb", "Friendly", "Early riser"],
    interests: ["Gardening", "Reading", "Cooking"],
    goals: ["Learn photo sharing", "Join circles"],
    teach: ["Plant care"],
    learn: ["Photo sharing", "Video calls"],
  },
  {
    id: "uncle-lim",
    name: "Mr Lim Chee Hong",
    age: 72,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Lim",
    location: "Novena",
    match: "88%",
    bio: "Enjoys volunteering and meeting new people.",
    matched: ["Community-minded", "Supportive", "Listener"],
    interests: ["Volunteering", "Walking", "Stories"],
    goals: ["Meet new friends", "Learn chat apps"],
    teach: ["Community tips"],
    learn: ["Social apps", "Video calls"],
  },
  {
    id: "auntie-elaine",
    name: "Ms Elaine Wong",
    age: 65,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Elaine",
    location: "Kembangan",
    match: "87%",
    bio: "Loves baking and learning new recipes online.",
    matched: ["Foodie", "Patient teacher", "Cheerful"],
    interests: ["Baking", "Cooking", "Travel"],
    goals: ["Learn new recipes", "Meet friends"],
    teach: ["Baking basics"],
    learn: ["Online recipes", "Photo sharing"],
  },
  {
    id: "uncle-hassan",
    name: "Mr Hassan Ali",
    age: 73,
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Hassan",
    location: "Bedok",
    match: "86%",
    bio: "Enjoys walking and sharing local stories.",
    matched: ["Story teller", "Friendly", "Calm"],
    interests: ["Walking", "Stories", "Music"],
    goals: ["Join a circle", "Learn social apps"],
    teach: ["Local stories"],
    learn: ["Social apps", "Video calls"],
  },
];

let index = 0;
let lastConnectedProfile = null;
let lastConnectedMatchId = null;
let currentSort = "default";
let userStations = [];

const MRT_STATIONS = [
  "Admiralty","Aljunied","Ang Mo Kio","Boon Lay","Braddell","Bishan","Bugis","Buangkok","Bukit Batok","Bukit Gombak",
  "Buona Vista","Changi Airport","Chinatown","Choa Chu Kang","City Hall","Clarke Quay","Clementi","Dover","Dhoby Ghaut",
  "Eunos","Hougang","Jurong East","Kallang","Kembangan","Khatib","Kranji","Lakeside","Lavender","Marymount","Novena",
  "Orchard","Outram Park","Paya Lebar","Potong Pasir","Pasir Ris","Punggol","Queenstown","Raffles Place","Redhill",
  "Serangoon","Sengkang","Somerset","Tai Seng","Tampines","Tanjong Pagar","Telok Ayer","Toa Payoh","Woodlands","Yishun"
];

let profiles = [];
let displayProfiles = [];

const card = document.getElementById("card");
const avatar = document.querySelector(".avatar");
const nameEl = document.querySelector(".name");
const locationEl = document.querySelector(".location");
const matchEl = document.querySelector(".match-value");
const bioEl = document.querySelector(".bio");

const matchedTags = document.getElementById("matchedTags");
const interestTags = document.getElementById("interestTags");
const goalsList = document.getElementById("goalsList");
const teachTags = document.getElementById("teachTags");
const learnTags = document.getElementById("learnTags");

const connectBtn = document.getElementById("connectBtn");
const passBtn = document.getElementById("passBtn");

const matchModal = document.getElementById("matchModal");
const matchedName = document.getElementById("matchedName");
const sendMessageBtn = document.getElementById("sendMessageBtn");
const keepSwipingBtn = document.getElementById("keepSwipingBtn");

const matchesBtn = document.getElementById("matchesBtn");
const resetBtn = document.getElementById("resetBtn");

const matchesModal = document.getElementById("matchesModal");
const closeMatchesBtn = document.getElementById("closeMatchesBtn");
const matchesList = document.getElementById("matchesList");
const matchesCount = document.getElementById("matchesCount");
const matchCount = document.getElementById("matchCount");
const filterButtons = document.querySelectorAll(".filter-btn");

const uiModal = document.getElementById("ui-modal");
const uiModalTitle = document.getElementById("ui-modal-title");
const uiModalBody = document.getElementById("ui-modal-body");
const uiModalActions = document.getElementById("ui-modal-actions");
const uiModalClose = document.getElementById("ui-modal-close");

// Modal open
function openModal({ title, bodyHtml, actionsHtml }) {
  if (!uiModal || !uiModalTitle || !uiModalBody || !uiModalActions) return;
  uiModalTitle.textContent = title;
  uiModalBody.innerHTML = bodyHtml;
  uiModalActions.innerHTML = actionsHtml;
  uiModal.classList.add("show");
}

// Modal close
function closeModal() {
  if (!uiModal) return;
  uiModal.classList.remove("show");
}

if (uiModalClose) uiModalClose.addEventListener("click", closeModal);
if (uiModal) {
  uiModal.addEventListener("click", (e) => {
    if (e.target === uiModal) closeModal();
  });
}

// HTML escape
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function demoHeaders(extra) {
  const headers = extra ? { ...extra } : {};
  const demoId = sessionStorage.getItem("demo_user_id");
  if (demoId) headers["X-Demo-User"] = demoId;
  return headers;
}

function stationIndex(name) {
  if (!name) return -1;
  return MRT_STATIONS.indexOf(String(name).trim());
}

function profileStations(profile) {
  const raw = profile?.stations;
  if (Array.isArray(raw) && raw.length) return raw;
  if (profile?.location) return [profile.location];
  return [];
}

function distanceToUser(profile) {
  const u = userStations || [];
  const p = profileStations(profile);
  if (!u.length || !p.length) return Number.POSITIVE_INFINITY;
  let best = Number.POSITIVE_INFINITY;
  u.forEach((uStation) => {
    const ui = stationIndex(uStation);
    if (ui < 0) return;
    p.forEach((pStation) => {
      const pi = stationIndex(pStation);
      if (pi < 0) return;
      const d = Math.abs(ui - pi);
      if (d < best) best = d;
    });
  });
  return best;
}

function closestStationToUser(profile) {
  const u = userStations || [];
  const p = profileStations(profile);
  if (!u.length || !p.length) return null;
  let best = null;
  u.forEach((uStation) => {
    const ui = stationIndex(uStation);
    if (ui < 0) return;
    p.forEach((pStation) => {
      const pi = stationIndex(pStation);
      if (pi < 0) return;
      const d = Math.abs(ui - pi);
      if (!best || d < best.distance) {
        best = { your: uStation, friend: pStation, distance: d };
      }
    });
  });
  return best;
}

function compatibilityScore(profile) {
  const raw = String(profile?.match || "").replace("%", "");
  const val = parseInt(raw, 10);
  return Number.isNaN(val) ? 0 : val;
}

function sortProfiles(list, mode) {
  const sorted = list.slice();
  if (mode === "distance") {
    sorted.sort((a, b) => {
      const da = distanceToUser(a);
      const db = distanceToUser(b);
      if (da === db) return (a._sortIndex || 0) - (b._sortIndex || 0);
      return da - db;
    });
  } else if (mode === "compatibility") {
    sorted.sort((a, b) => {
      const ca = compatibilityScore(a);
      const cb = compatibilityScore(b);
      if (cb === ca) return (a._sortIndex || 0) - (b._sortIndex || 0);
      return cb - ca;
    });
  }
  return sorted;
}

function applySort(mode) {
  currentSort = mode || "default";
  displayProfiles = sortProfiles(profiles, currentSort);
  index = 0;
  updateFilterButtons();
  loadProfile();
}

function updateFilterButtons() {
  filterButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.sort === currentSort);
  });
}

async function loadUserStations() {
  try {
    const res = await fetch("/api/profile", { headers: demoHeaders() });
    if (!res.ok) return;
    const out = await res.json().catch(() => ({}));
    const onboarding = out?.profile?.onboarding || {};
    userStations = Array.isArray(onboarding.stations) ? onboarding.stations : [];
  } catch (e) {
  }
}

async function loadProfiles() {
  let combined = STATIC_PROFILES.slice();
  try {
    const res = await fetch("/api/matching/profiles", { headers: demoHeaders() });
    if (res.ok) {
      const out = await res.json().catch(() => ({}));
      const real = Array.isArray(out.profiles) ? out.profiles : [];
      if (real.length) {
        combined = real.concat(STATIC_PROFILES);
      }
    }
  } catch (e) {
  }
  profiles = combined.map((p, idx) => ({ ...p, _sortIndex: idx }));
}

// API matches
async function apiListMatches() {
  const res = await fetch("/api/matches", { headers: demoHeaders() });
  if (!res.ok) throw new Error("Failed to load matches");
  return await res.json();
}

// API create
async function apiCreateMatch(profile) {
  const res = await fetch("/api/matches", {
    method: "POST",
    headers: demoHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      match_id: profile.id,
      name: profile.name,
      avatar: profile.avatar,
      location: profile.location || "",
    }),
  });
  if (!res.ok) throw new Error("Failed to create match");
  return await res.json();
}

// API delete
async function apiDeleteMatch(matchId) {
  const res = await fetch(`/api/matches/${encodeURIComponent(matchId)}`, {
    method: "DELETE",
    headers: demoHeaders(),
  });
  if (!res.ok) throw new Error("Failed to delete match");
  return await res.json();
}

// API clear
async function apiClearMatches() {
  const res = await fetch("/api/matches", { method: "DELETE", headers: demoHeaders() });
  if (!res.ok) throw new Error("Failed to clear matches");
  return await res.json();
}

async function apiSendMatchRequest(receiverId) {
  const res = await fetch("/api/match_requests", {
    method: "POST",
    headers: demoHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ receiver_id: receiverId }),
  });
  if (!res.ok) throw new Error("Failed to send match request");
  return await res.json();
}

// Render tags
function renderTags(container, list) {
  container.innerHTML = "";
  (list || []).forEach((t) => {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = t;
    container.appendChild(span);
  });
}

// Render goals
function renderGoals(container, list) {
  container.innerHTML = "";
  (list || []).forEach((g) => {
    const li = document.createElement("li");
    li.textContent = g;
    container.appendChild(li);
  });
}

// Load profile
function loadProfile() {
  const p = displayProfiles[index];
  if (!p) {
    if (nameEl) nameEl.textContent = "No profiles yet";
    if (locationEl) locationEl.textContent = "";
    if (matchEl) matchEl.textContent = "";
    if (bioEl) bioEl.textContent = "";
    renderTags(matchedTags, []);
    renderTags(interestTags, []);
    renderGoals(goalsList, []);
    renderTags(teachTags, []);
    renderTags(learnTags, []);
    return;
  }
  avatar.src = p.avatar;
  if (p.age === null || p.age === undefined || p.age === "") {
    nameEl.textContent = `${p.name}`;
  } else {
    nameEl.textContent = `${p.name}, ${p.age}`;
  }
  const closest = closestStationToUser(p);
  const locationText = p.location || "Hidden";
  if (closest) {
    locationEl.textContent = `${locationText} • Closest MRT: ${closest.friend} (you: ${closest.your})`;
  } else {
    locationEl.textContent = locationText;
  }
  matchEl.textContent = p.match;
  bioEl.textContent = `"${p.bio}"`;

  renderTags(matchedTags, p.matched);
  renderTags(interestTags, p.interests);
  renderGoals(goalsList, p.goals);
  renderTags(teachTags, p.teach);
  renderTags(learnTags, p.learn);

  if (sendMessageBtn) {
    const directAllowed = p.allow_direct !== false;
    sendMessageBtn.disabled = !directAllowed;
    sendMessageBtn.title = directAllowed ? "" : "Direct messages are disabled by this user.";
  }
}

// Next profile
function nextProfile() {
  if (!displayProfiles.length) return;
  index = (index + 1) % displayProfiles.length;
  loadProfile();
}

// Match count
async function refreshMatchCount() {
  try {
    const matches = await apiListMatches();
    if (matchCount) matchCount.textContent = String(matches.length);
    if (matchesCount) matchesCount.textContent = String(matches.length);
  } catch (e) {
    if (matchCount) matchCount.textContent = "0";
    if (matchesCount) matchesCount.textContent = "0";
  }
}

// Connect
async function connectProfile() {
  const p = displayProfiles[index];
  if (!p) return;
  try {
    if (p.is_real && p.user_id) {
      await apiSendMatchRequest(p.user_id);
      const saved = await apiCreateMatch(p);
      lastConnectedProfile = p;
      lastConnectedMatchId = saved?.match_id || null;
      localStorage.setItem("lastConnectedUser", lastConnectedMatchId || p.id);
      await refreshMatchCount();
      openModal({
        title: "Match request sent",
        bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">We'll notify you when they respond. This connection is now in your matches list.</div>`,
        actionsHtml: `<button class="ui-btn primary" id="modal-ok">OK</button>`,
      });
      const ok = document.getElementById("modal-ok");
      if (ok) ok.addEventListener("click", closeModal);
      nextProfile();
      return;
    }

    const saved = await apiCreateMatch(p);
    lastConnectedProfile = p;
    lastConnectedMatchId = saved?.match_id || null;
    localStorage.setItem("lastConnectedUser", lastConnectedMatchId || p.id);

    matchedName.textContent = p.name;
    matchModal.classList.add("show");

    await refreshMatchCount();
  } catch (e) {
    openModal({
      title: "Match failed",
      bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">Could not save match. Check Flask is running.</div>`,
      actionsHtml: `<button class="ui-btn primary" id="modal-fail-ok">OK</button>`,
    });
    const ok = document.getElementById("modal-fail-ok");
    if (ok) ok.addEventListener("click", closeModal);
    console.error(e);
  }
}

// Pass
function passProfile() {
  nextProfile();
}

// Matches modal
async function openMatchesModal() {
  try {
    const matches = await apiListMatches();
    matchesList.innerHTML = "";

    if (matchesCount) matchesCount.textContent = String(matches.length);
    if (matchCount) matchCount.textContent = String(matches.length);

    if (matches.length === 0) {
      matchesList.innerHTML = `
        <div style="padding: 12px; color: #7f8c8d; font-size: 14px;">
          No matches yet. Click ❤ Connect to save a match.
        </div>
      `;
      matchesModal.classList.add("show");
      return;
    }

    matches.forEach((m) => {
      const item = document.createElement("div");
      item.className = "match-item";

      item.innerHTML = `
        <img class="avatar" src="${escapeHtml(m.avatar)}" alt="Avatar" />
        <div class="match-item-info">
          <div class="match-item-name">${escapeHtml(m.name)}</div>
          <div class="match-item-location">${escapeHtml(m.location || "")}</div>
        </div>
        <div class="match-actions">
          <button class="match-action-btn message-btn" data-chat="${escapeHtml(m.match_id)}">Chat</button>
          <button class="match-action-btn unmatch-btn" data-del="${escapeHtml(m.match_id)}">Delete</button>
        </div>
      `;

      item.querySelector("[data-chat]").addEventListener("click", () => {
        window.location.href = `/messages?chat=${encodeURIComponent(m.match_id)}`;
      });

      item.querySelector("[data-del]").addEventListener("click", async () => {
        openModal({
          title: "Delete this match?",
          bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">This removes this connection from your list.</div>`,
          actionsHtml: `
            <button class="ui-btn" id="modal-del-cancel">Cancel</button>
            <button class="ui-btn danger" id="modal-del-confirm">Delete</button>
          `,
        });
        const cancel = document.getElementById("modal-del-cancel");
        const confirmDel = document.getElementById("modal-del-confirm");
        if (cancel) cancel.addEventListener("click", closeModal);
        if (confirmDel) {
          confirmDel.addEventListener("click", async () => {
            try {
              await apiDeleteMatch(m.match_id);
              closeModal();
              await openMatchesModal();
              await refreshMatchCount();
            } catch (e) {
              openModal({
                title: "Delete failed",
                bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">Could not delete match.</div>`,
                actionsHtml: `<button class="ui-btn primary" id="modal-del-fail-ok">OK</button>`,
              });
              const okBtn = document.getElementById("modal-del-fail-ok");
              if (okBtn) okBtn.addEventListener("click", closeModal);
              console.error(e);
            }
          });
        }
      });

      matchesList.appendChild(item);
    });

    matchesModal.classList.add("show");
  } catch (e) {
    openModal({
      title: "Load failed",
      bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">Could not load matches. Check Flask is running.</div>`,
      actionsHtml: `<button class="ui-btn primary" id="modal-load-fail-ok">OK</button>`,
    });
    const ok = document.getElementById("modal-load-fail-ok");
    if (ok) ok.addEventListener("click", closeModal);
    console.error(e);
  }
}

if (connectBtn) connectBtn.addEventListener("click", connectProfile);
if (passBtn) passBtn.addEventListener("click", passProfile);

if (keepSwipingBtn) {
  keepSwipingBtn.addEventListener("click", () => {
    matchModal.classList.remove("show");
    nextProfile();
  });
}

if (sendMessageBtn) {
  sendMessageBtn.addEventListener("click", () => {
    const chatId = lastConnectedMatchId || localStorage.getItem("lastConnectedUser");
    if (chatId) window.location.href = `/messages?chat=${encodeURIComponent(chatId)}`;
    else window.location.href = "/messages";
  });
}

if (matchesBtn) matchesBtn.addEventListener("click", openMatchesModal);
if (closeMatchesBtn) closeMatchesBtn.addEventListener("click", () => matchesModal.classList.remove("show"));

if (matchesModal) {
  matchesModal.addEventListener("click", (e) => {
    if (e.target === matchesModal) matchesModal.classList.remove("show");
  });
}

if (resetBtn) {
  resetBtn.addEventListener("click", async () => {
    openModal({
      title: "Reset matches?",
      bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">This will remove all saved matches.</div>`,
      actionsHtml: `
        <button class="ui-btn" id="modal-cancel">Cancel</button>
        <button class="ui-btn danger" id="modal-reset">Reset</button>
      `,
    });

    const cancel = document.getElementById("modal-cancel");
    const confirmReset = document.getElementById("modal-reset");
    if (cancel) cancel.addEventListener("click", closeModal);
    if (confirmReset) {
      confirmReset.addEventListener("click", async () => {
        try {
          await apiClearMatches();
          localStorage.removeItem("lastConnectedUser");
          await refreshMatchCount();
          index = 0;
          applySort(currentSort);
          closeModal();
        } catch (e) {
          openModal({
            title: "Reset failed",
            bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">Could not reset.</div>`,
            actionsHtml: `<button class="ui-btn primary" id="modal-reset-fail-ok">OK</button>`,
          });
          const ok = document.getElementById("modal-reset-fail-ok");
          if (ok) ok.addEventListener("click", closeModal);
          console.error(e);
        }
      });
    }
  });
}

filterButtons.forEach((btn) => {
  btn.addEventListener("click", () => applySort(btn.dataset.sort || "default"));
});

async function initMatching() {
  await loadUserStations();
  await loadProfiles();
  applySort(currentSort);
  refreshMatchCount();
}

initMatching();

