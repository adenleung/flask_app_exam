let currentStep = 1;
const totalSteps = 6;
let selectedUserType = null;
let selectedInterests = [];
let selectedTeach = [];
let selectedLearn = [];
let selectedDays = [];
let selectedTimes = [];
let selectedStations = [];

const params = new URLSearchParams(window.location.search);
const isEditMode = params.get('edit') === '1';
const preloaded = window.preloadedOnboarding || {};
const requestedStep = parseInt(params.get('step') || '2', 10);
const editStep = [2, 3, 4, 6].indexOf(requestedStep) !== -1 ? requestedStep : 2;
const returnTarget = (params.get('return') || '').toLowerCase();
const returnTab = (params.get('tab') || '').toLowerCase();

// Step 1: User Type Selection
const userTypeCards = document.querySelectorAll('.user-type-card');
const nextBtn1 = document.getElementById('next-1');

userTypeCards.forEach(card => {
  card.addEventListener('click', function() {
    userTypeCards.forEach(c => c.classList.remove('selected'));
    this.classList.add('selected');
    selectedUserType = this.dataset.type;
    nextBtn1.disabled = false;
  });
});

nextBtn1.addEventListener('click', function() {
  goToStep(2);
});

// Step 2: Interests Selection
const interestChips = document.querySelectorAll('#step-2 .interest-chip[data-interest]');
const teachChips = document.querySelectorAll('#step-3 .interest-chip[data-teach]');
const learnChips = document.querySelectorAll('#step-4 .interest-chip[data-learn]');
const nextBtn2 = document.getElementById('next-2');
const backBtn2 = document.getElementById('back-2');

function updateInterestNextButton() {
  const minCount = 3;
  if (!nextBtn2) return;
  nextBtn2.disabled = selectedInterests.length < minCount;
}

interestChips.forEach(chip => {
  chip.addEventListener('click', function() {
    const interest = this.dataset.interest;

    if (this.classList.contains('selected')) {
      this.classList.remove('selected');
      if (interest) selectedInterests = selectedInterests.filter(i => i !== interest);
    } else {
      this.classList.add('selected');
      if (interest) selectedInterests.push(interest);
    }

    updateInterestNextButton();
  });
});

nextBtn2.addEventListener('click', function() {
  if (isEditMode && editStep === 2) {
    submitOnboarding();
    return;
  }
  goToStep(3);
});

backBtn2.addEventListener('click', function() {
  goToStep(1);
});

// Step 3: Skills I Can Teach
const backBtn3 = document.getElementById('back-3');
const nextBtn3 = document.getElementById('next-3');

function updateTeachNextButton() {
  if (!nextBtn3) return;
  nextBtn3.disabled = selectedTeach.length < 1;
}

teachChips.forEach(chip => {
  chip.addEventListener('click', function() {
    const teach = this.dataset.teach;
    if (!teach) return;
    if (this.classList.contains('selected')) {
      this.classList.remove('selected');
      selectedTeach = selectedTeach.filter(i => i !== teach);
    } else {
      this.classList.add('selected');
      selectedTeach.push(teach);
    }
    updateTeachNextButton();
  });
});

backBtn3.addEventListener('click', function() {
  goToStep(2);
});

if (nextBtn3) {
  nextBtn3.addEventListener('click', function() {
    if (isEditMode && editStep === 3) {
      submitOnboarding();
      return;
    }
    goToStep(4);
  });
}

// Step 4: Skills I Want to Learn
const backBtn4 = document.getElementById('back-4');
const nextBtn4 = document.getElementById('next-4');

function updateLearnNextButton() {
  if (!nextBtn4) return;
  nextBtn4.disabled = selectedLearn.length < 1;
}

learnChips.forEach(chip => {
  chip.addEventListener('click', function() {
    const learn = this.dataset.learn;
    if (!learn) return;
    if (this.classList.contains('selected')) {
      this.classList.remove('selected');
      selectedLearn = selectedLearn.filter(i => i !== learn);
    } else {
      this.classList.add('selected');
      selectedLearn.push(learn);
    }
    updateLearnNextButton();
  });
});

if (backBtn4) {
  backBtn4.addEventListener('click', function() {
    goToStep(3);
  });
}

if (nextBtn4) {
  nextBtn4.addEventListener('click', function() {
    if (isEditMode && editStep === 4) {
      submitOnboarding();
      return;
    }
    goToStep(5);
  });
}

// Step 5: Availability Selection
const dayChips = document.querySelectorAll('.day-chip');
const timeChips = document.querySelectorAll('.time-chip');
const finishBtn = document.getElementById('finish');
const backBtn5 = document.getElementById('back-5');
const nextBtn5 = document.getElementById('next-5');
const backBtn6 = document.getElementById('back-6');
const nextBtn6 = document.getElementById('next-6');

dayChips.forEach(chip => {
  chip.addEventListener('click', function() {
    const day = this.dataset.day;

    if (this.classList.contains('selected')) {
      this.classList.remove('selected');
      selectedDays = selectedDays.filter(d => d !== day);
    } else {
      this.classList.add('selected');
      selectedDays.push(day);
    }
  });
});

timeChips.forEach(chip => {
  chip.addEventListener('click', function() {
    const time = this.dataset.time;
    if (this.classList.contains('selected')) {
      this.classList.remove('selected');
      selectedTimes = selectedTimes.filter(t => t !== time);
    } else {
      this.classList.add('selected');
      selectedTimes.push(time);
    }
  });
});

if (backBtn5) {
  backBtn5.addEventListener('click', function() {
    goToStep(4);
  });
}

if (nextBtn5) {
  nextBtn5.addEventListener('click', function() {
    goToStep(6);
  });
}

if (backBtn6) {
  backBtn6.addEventListener('click', function() {
    goToStep(5);
  });
}

async function submitOnboarding() {
  // Store onboarding data in the database
  var payload = {
    memberType: selectedUserType || '',
    interests: selectedInterests || [],
    skills_teach: selectedTeach || [],
    skills_learn: selectedLearn || [],
    days: selectedDays || [],
    time: selectedTimes || [],
    stations: selectedStations || [],
    landmarks: []
  };

  try {
    var res = await fetch('/api/onboarding', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    var out = await res.json().catch(function () { return {}; });

    if (!res.ok) {
      if (res.status === 401) {
        alert('Please sign up or log in first.');
        window.location.href = '/signup';
        return;
      }
      alert(out.error || 'Could not save your onboarding details.');
      return;
    }

    if (returnTarget === 'profile') {
      window.location.href = '/profile';
    } else {
      window.location.href = '/dashboard';
    }
  } catch (err) {
    alert('Could not reach the server. Please try again.');
  }
}

if (nextBtn6) {
  nextBtn6.addEventListener('click', submitOnboarding);
}
if (finishBtn) {
  finishBtn.addEventListener('click', submitOnboarding);
}

// Navigation Function
function goToStep(stepNumber) {
  // Hide all steps
  document.querySelectorAll('.onboarding-step').forEach(step => {
    step.classList.remove('active');
  });

  // Show current step
  document.getElementById(`step-${stepNumber}`).classList.add('active');

  // Update progress
  currentStep = stepNumber;
  document.getElementById('current-step').textContent = stepNumber;

  const progressPercent = (stepNumber / totalSteps) * 100;
  document.getElementById('progress-fill').style.width = `${progressPercent}%`;

  // Scroll to top
  window.scrollTo(0, 0);

  if (stepNumber === 6 && mrtViewMode === "map") {
    setTimeout(function () {
      if (realMap) realMap.invalidateSize();
    }, 220);
  }
}

function applyEditModeUI() {
  if (!isEditMode) return;
  const progressContainer = document.querySelector('.progress-container');
  if (progressContainer) progressContainer.style.display = 'none';

  const config = {
    2: { back: 'back-2', next: 'next-2' },
    3: { back: 'back-3', next: 'next-3' },
    4: { back: 'back-4', next: 'next-4' },
    6: { back: 'back-6', next: 'next-6' }
  }[editStep];
  if (!config) return;

  const backBtn = document.getElementById(config.back);
  const nextBtn = document.getElementById(config.next);
  if (backBtn) backBtn.style.display = 'none';
  if (nextBtn) {
    nextBtn.textContent = 'SAVE';
    nextBtn.classList.add('btn-full');
    nextBtn.style.width = '100%';
    const group = nextBtn.closest('.button-group');
    if (group) group.classList.add('edit-save-only');
  }
}

// Preload selections for edit mode
document.addEventListener('DOMContentLoaded', function() {
  if (preloaded && preloaded.memberType) {
    selectedUserType = preloaded.memberType;
    userTypeCards.forEach(card => {
      if (card.dataset.type === selectedUserType) {
        card.classList.add('selected');
      }
    });
    nextBtn1.disabled = false;
  }

  if (preloaded && Array.isArray(preloaded.interests)) {
    selectedInterests = [...preloaded.interests];
    preloaded.interests.forEach(function(interest) {
      var chip = document.querySelector('.interest-chip[data-interest="' + interest + '"]');
      if (chip) chip.classList.add('selected');
    });
  }

  if (preloaded && Array.isArray(preloaded.skills_teach)) {
    selectedTeach = [...preloaded.skills_teach];
    preloaded.skills_teach.forEach(function(skill) {
      var chip = document.querySelector('.interest-chip[data-teach="' + skill + '"]');
      if (chip) chip.classList.add('selected');
    });
  }

  if (preloaded && Array.isArray(preloaded.skills_learn)) {
    selectedLearn = [...preloaded.skills_learn];
    preloaded.skills_learn.forEach(function(skill) {
      var chip = document.querySelector('.interest-chip[data-learn="' + skill + '"]');
      if (chip) chip.classList.add('selected');
    });
  }

  updateInterestNextButton();
  updateTeachNextButton();
  updateLearnNextButton();

  if (preloaded && Array.isArray(preloaded.days)) {
    selectedDays = [...preloaded.days];
    preloaded.days.forEach(function(day) {
      var chip = document.querySelector('.day-chip[data-day="' + day + '"]');
      if (chip) chip.classList.add('selected');
    });
  }

  if (preloaded && Array.isArray(preloaded.time)) {
    selectedTimes = [...preloaded.time];
    preloaded.time.forEach(function(t) {
      var chip = document.querySelector('.time-chip[data-time="' + t + '"]');
      if (chip) chip.classList.add('selected');
    });
  }

  applyEditModeUI();
  if (isEditMode) goToStep(editStep);

  if (preloaded && Array.isArray(preloaded.stations)) {
    selectedStations = [...preloaded.stations];
  }
});

// MRT Station Picker
const mrtStations = [
  "Admiralty","Aljunied","Ang Mo Kio","Bartley","Bayfront","Beauty World","Bedok","Bedok North","Bedok Reservoir",
  "Bencoolen","Bendemeer","Bishan","Boon Keng","Boon Lay","Botanic Gardens","Braddell","Bras Basah","Bright Hill",
  "Bugis","Buona Vista","Buangkok","Bukit Batok","Bukit Gombak","Bukit Panjang","Caldecott","Canberra","Cashew",
  "Changi Airport","Chinatown","Choa Chu Kang","Chinese Garden","City Hall","Clarke Quay","Clementi","Commonwealth",
  "Dakota","Dhoby Ghaut","Dover","Downtown","Eunos","Expo","Farrer Park","Farrer Road","Fort Canning",
  "Gardens by the Bay","Geylang Bahru","Great World","Gul Circle","Havelock","Haw Par Villa","HarbourFront",
  "Hillview","Holland Village","Hougang","Jalan Besar","Joo Koon","Jurong East","Kaki Bukit","Kallang","Katong Park",
  "Kembangan","Kent Ridge","Khatib","King Albert Park","Kovan","Kranji","Labrador Park","Lakeside","Lavender",
  "Lentor","Little India","Lorong Chuan","MacPherson","Marina Bay","Marina South Pier","Marine Parade",
  "Marine Terrace","Marymount","Mattar","Maxwell","Mayflower","Mountbatten","Napier","Nicoll Highway","Novena",
  "one-north","Orchard","Orchard Boulevard","Outram Park","Pasir Panjang","Pasir Ris","Paya Lebar","Pioneer",
  "Potong Pasir","Promenade","Punggol","Queenstown","Raffles Place","Redhill","Rochor","Sembawang","Sengkang",
  "Serangoon","Shenton Way","Simei","Siglap","Sixth Avenue","Somerset","Springleaf","Stadium","Stevens","Tai Seng",
  "Tampines","Tampines East","Tampines West","Tan Kah Kee","Tanah Merah","Tanjong Katong","Tanjong Pagar",
  "Tanjong Rhu","Telok Ayer","Tiong Bahru","Toa Payoh","Tuas Crescent","Tuas Link","Tuas West Road",
  "Ubi","Upper Changi","Upper Thomson","Woodlands","Woodlands North","Woodlands South","Woodleigh","Yew Tee",
  "Yio Chu Kang","Yishun"
];

const mrtLineGroups = [
  { key: "NSL", label: "North South Line", stations: ["Admiralty","Ang Mo Kio","Bishan","Braddell","Canberra","Choa Chu Kang","City Hall","Jurong East","Khatib","Kranji","Marina Bay","Novena","Orchard","Raffles Place","Sembawang","Somerset","Toa Payoh","Woodlands","Yew Tee","Yio Chu Kang","Yishun"] },
  { key: "EWL", label: "East West Line", stations: ["Aljunied","Bedok","Boon Lay","Bugis","Buona Vista","Chinese Garden","Clementi","Commonwealth","Dover","Eunos","Expo","Joo Koon","Kallang","Kembangan","Lakeside","Lavender","Outram Park","Pasir Ris","Paya Lebar","Pioneer","Queenstown","Redhill","Simei","Tanah Merah","Tanjong Pagar","Tuas Crescent","Tuas Link","Tuas West Road"] },
  { key: "DTL", label: "Downtown Line", stations: ["Bayfront","Beauty World","Bedok North","Bedok Reservoir","Bencoolen","Bendemeer","Botanic Gardens","Bukit Panjang","Cashew","Chinatown","Downtown","Expo","Fort Canning","Hillview","Jalan Besar","Kaki Bukit","King Albert Park","Little India","MacPherson","Mattar","Newton","Promenade","Rochor","Sixth Avenue","Stevens","Tan Kah Kee","Telok Ayer","Tampines","Tampines East","Tampines West","Ubi","Upper Changi"] },
  { key: "NEL", label: "North East Line", stations: ["Buangkok","Chinatown","Clarke Quay","Dhoby Ghaut","Farrer Park","HarbourFront","Hougang","Kovan","Little India","Outram Park","Potong Pasir","Punggol","Sengkang","Serangoon","Woodleigh"] },
  { key: "CCL", label: "Circle Line", stations: ["Bartley","Bayfront","Botanic Gardens","Bras Basah","Buona Vista","Caldecott","Dakota","Dhoby Ghaut","Esplanade","Farrer Road","HarbourFront","Haw Par Villa","Holland Village","Labrador Park","Lorong Chuan","MacPherson","Marina Bay","Marymount","Mountbatten","Nicoll Highway","one-north","Pasir Panjang","Promenade","Serangoon","Stadium","Tai Seng"] },
  { key: "TEL", label: "Thomson-East Coast Line", stations: ["Bright Hill","Caldecott","Gardens by the Bay","Great World","Havelock","Lentor","Marine Parade","Marine Terrace","Maxwell","Mayflower","Napier","Orchard Boulevard","Outram Park","Shenton Way","Siglap","Springleaf","Stevens","Tanjong Katong","Tanjong Rhu","Upper Thomson","Woodlands North","Woodlands South"] }
];

const mrtLineColor = {
  NSL: "#ef4444",
  EWL: "#22c55e",
  DTL: "#3b82f6",
  NEL: "#a855f7",
  CCL: "#f59e0b",
  TEL: "#8b5e3c",
  OTHER: "#64748b"
};

const MRT_LINE_CODE_PREFIX = {
  NSL: "NS",
  EWL: "EW",
  CCL: "CC",
  DTL: "DT",
  NEL: "NE",
  TEL: "TE"
};

const MRT_ROUTE_RULES = {
  minutesPerStop: 2,
  transferPenalty: 6
};

let routeGraph = null;
let routeNodesByStation = null;
const routeMinutesCache = new Map();

function buildRouteGraph() {
  if (routeGraph && routeNodesByStation) {
    return { graph: routeGraph, nodesByStation: routeNodesByStation };
  }

  const graph = new Map();
  const nodesByStation = new Map();

  function addNode(nodeId) {
    if (!graph.has(nodeId)) {
      graph.set(nodeId, []);
    }
  }

  function addEdge(a, b, minutes, type) {
    addNode(a);
    addNode(b);
    graph.get(a).push({ to: b, minutes: minutes, type: type });
  }

  mrtLineGroups.forEach(function (line) {
    line.stations.forEach(function (stationName) {
      const nodeId = line.key + "::" + stationName;
      addNode(nodeId);
      if (!nodesByStation.has(stationName)) {
        nodesByStation.set(stationName, []);
      }
      nodesByStation.get(stationName).push(nodeId);
    });

    for (let i = 0; i < line.stations.length - 1; i += 1) {
      const a = line.key + "::" + line.stations[i];
      const b = line.key + "::" + line.stations[i + 1];
      addEdge(a, b, MRT_ROUTE_RULES.minutesPerStop, "ride");
      addEdge(b, a, MRT_ROUTE_RULES.minutesPerStop, "ride");
    }
  });

  nodesByStation.forEach(function (nodes) {
    if (nodes.length < 2) return;
    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        addEdge(nodes[i], nodes[j], MRT_ROUTE_RULES.transferPenalty, "transfer");
        addEdge(nodes[j], nodes[i], MRT_ROUTE_RULES.transferPenalty, "transfer");
      }
    }
  });

  routeGraph = graph;
  routeNodesByStation = nodesByStation;
  return { graph: routeGraph, nodesByStation: routeNodesByStation };
}

function shortestMinutesBetweenStations(startStation, endStation) {
  if (!startStation || !endStation) return null;
  if (startStation === endStation) return 0;
  const cacheKey = startStation + ">>" + endStation;
  if (routeMinutesCache.has(cacheKey)) {
    return routeMinutesCache.get(cacheKey);
  }

  const built = buildRouteGraph();
  const graph = built.graph;
  const nodesByStation = built.nodesByStation;
  const startNodes = nodesByStation.get(startStation) || [];
  const goalNodes = new Set(nodesByStation.get(endStation) || []);
  if (!startNodes.length || !goalNodes.size) {
    routeMinutesCache.set(cacheKey, null);
    return null;
  }

  const dist = new Map();
  const visited = new Set();
  const queue = [];

  startNodes.forEach(function (nodeId) {
    dist.set(nodeId, 0);
    queue.push({ node: nodeId, d: 0 });
  });

  function push(nodeId, d) {
    queue.push({ node: nodeId, d: d });
    queue.sort(function (a, b) { return a.d - b.d; });
  }

  let best = null;
  while (queue.length) {
    const current = queue.shift();
    if (visited.has(current.node)) continue;
    visited.add(current.node);

    if (goalNodes.has(current.node)) {
      best = current.d;
      break;
    }

    const edges = graph.get(current.node) || [];
    edges.forEach(function (edge) {
      const nextDist = current.d + edge.minutes;
      const prevDist = dist.has(edge.to) ? dist.get(edge.to) : Infinity;
      if (nextDist < prevDist) {
        dist.set(edge.to, nextDist);
        push(edge.to, nextDist);
      }
    });
  }

  routeMinutesCache.set(cacheKey, best);
  routeMinutesCache.set(endStation + ">>" + startStation, best);
  return best;
}

function shortestRouteDetails(startStation, endStation) {
  if (!startStation || !endStation) return null;
  if (startStation === endStation) return { minutes: 0, transfers: 0 };

  const built = buildRouteGraph();
  const graph = built.graph;
  const nodesByStation = built.nodesByStation;
  const startNodes = nodesByStation.get(startStation) || [];
  const goalNodes = new Set(nodesByStation.get(endStation) || []);
  if (!startNodes.length || !goalNodes.size) return null;

  const dist = new Map();
  const prev = new Map();
  const visited = new Set();
  const queue = [];

  function push(nodeId, d) {
    queue.push({ node: nodeId, d: d });
    queue.sort(function (a, b) { return a.d - b.d; });
  }

  startNodes.forEach(function (nodeId) {
    dist.set(nodeId, 0);
    push(nodeId, 0);
  });

  let targetNode = null;
  while (queue.length) {
    const current = queue.shift();
    if (visited.has(current.node)) continue;
    visited.add(current.node);

    if (goalNodes.has(current.node)) {
      targetNode = current.node;
      break;
    }

    (graph.get(current.node) || []).forEach(function (edge) {
      const nextDist = current.d + edge.minutes;
      const prevDist = dist.has(edge.to) ? dist.get(edge.to) : Infinity;
      if (nextDist < prevDist) {
        dist.set(edge.to, nextDist);
        prev.set(edge.to, { node: current.node, type: edge.type });
        push(edge.to, nextDist);
      }
    });
  }

  if (!targetNode) return null;
  let transfers = 0;
  let cursor = targetNode;
  while (prev.has(cursor)) {
    const step = prev.get(cursor);
    if (step.type === "transfer") transfers += 1;
    cursor = step.node;
  }
  return { minutes: dist.get(targetNode), transfers: transfers };
}

let mrtViewMode = "list";
let selectedLineKey = "NSL";
let activeLineFilter = "ALL";

const LINE_FILTER_TO_KEYS = {
  ALL: null,
  NS: ["NSL"],
  EW: ["EWL"],
  DT: ["DTL"],
  NE: ["NEL"],
  CC: ["CCL"],
  TE: ["TEL"]
};

function lineCodeFromKey(key) {
  if (key === "NSL") return "NS";
  if (key === "EWL") return "EW";
  if (key === "DTL") return "DT";
  if (key === "NEL") return "NE";
  if (key === "CCL") return "CC";
  if (key === "TEL") return "TE";
  return key;
}

function stationLineKey(name) {
  for (var i = 0; i < mrtLineGroups.length; i += 1) {
    if (mrtLineGroups[i].stations.indexOf(name) !== -1) return mrtLineGroups[i].key;
  }
  return "OTHER";
}

function stationLineKeys(name) {
  var keys = [];
  for (var i = 0; i < mrtLineGroups.length; i += 1) {
    if (mrtLineGroups[i].stations.indexOf(name) !== -1) keys.push(mrtLineGroups[i].key);
  }
  return keys.length ? keys : ["OTHER"];
}

function stationStripe(name) {
  var keys = stationLineKeys(name);
  var colors = keys.map(function (k) { return mrtLineColor[k] || mrtLineColor.OTHER; });
  if (colors.length === 1) return colors[0];
  var step = 100 / colors.length;
  var stops = colors.map(function (c, idx) {
    var start = (idx * step).toFixed(2);
    var end = ((idx + 1) * step).toFixed(2);
    return c + " " + start + "% " + end + "%";
  });
  return "linear-gradient(to bottom, " + stops.join(", ") + ")";
}

function stationLineLabel(key) {
  var found = mrtLineGroups.find(function (g) { return g.key === key; });
  return found ? found.label : "Other Lines";
}

function renderStationOptions(list, selected) {
  const container = document.getElementById('mrt-options');
  if (!container) return;
  container.innerHTML = '';
  container.classList.toggle("map-view-mode", mrtViewMode === "map");

  const grouped = {};
  list.forEach(function (name) {
    var key = stationLineKeys(name)[0];
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(name);
  });

  const orderedKeys = mrtLineGroups.map(function (g) { return g.key; }).concat(["OTHER"]);
  orderedKeys.forEach(function (lineKey) {
    var stations = grouped[lineKey];
    if (!stations || !stations.length) return;

    const section = document.createElement("section");
    section.className = "mrt-line-group";
    section.style.borderColor = mrtViewMode === "map" ? mrtLineColor[lineKey] || mrtLineColor.OTHER : "";

    const title = document.createElement("h4");
    title.className = "mrt-line-title";
    title.textContent = "🚇 " + stationLineLabel(lineKey);
    if (mrtViewMode === "map") {
      title.style.color = mrtLineColor[lineKey] || mrtLineColor.OTHER;
    } else {
      title.style.color = "#475569";
    }

    const grid = document.createElement("div");
    grid.className = "station-grid";

    stations.forEach(function (name) {
      const checked = selected.indexOf(name) !== -1;
      const item = document.createElement("button");
      item.type = "button";
      item.className = "station-chip" + (checked ? " selected" : "");
      item.style.setProperty("--line-stripe", stationStripe(name));
      item.innerHTML = "<span>" + name + "</span>";
      item.setAttribute("aria-pressed", checked ? "true" : "false");
      item.addEventListener("click", function () {
        toggleStation(name);
        const stationSearch = document.getElementById("mrt-search");
        filterStations(stationSearch ? stationSearch.value : "");
      });
      grid.appendChild(item);
    });

    section.appendChild(title);
    section.appendChild(grid);
    container.appendChild(section);
  });
}

function renderSchematicMap(list, selected) {
  const board = document.getElementById("mrt-schematic-lines");
  if (!board) return;
  board.innerHTML = "";

  const filteredSet = new Set(list);
  mrtLineGroups.forEach(function (group) {
    const stations = group.stations.filter(function (name) { return filteredSet.has(name); });
    if (!stations.length) return;

    const row = document.createElement("div");
    row.className = "mrt-line-row";

    const label = document.createElement("div");
    label.className = "mrt-line-chip";
    label.style.background = mrtLineColor[group.key] || mrtLineColor.OTHER;
    label.textContent = group.label;

    const stationWrap = document.createElement("div");
    stationWrap.className = "mrt-line-stations";

    stations.forEach(function (name) {
      const active = selected.indexOf(name) !== -1;
      const node = document.createElement("button");
      node.type = "button";
      node.className = "station-node" + (active ? " selected" : "");
      node.textContent = name;
      node.setAttribute("aria-pressed", active ? "true" : "false");
      node.addEventListener("click", function () {
        toggleStation(name);
        const stationSearch = document.getElementById("mrt-search");
        filterStations(stationSearch ? stationSearch.value : "");
      });
      stationWrap.appendChild(node);
    });

    row.appendChild(label);
    row.appendChild(stationWrap);
    board.appendChild(row);
  });
}

function stationToMapPercent(stationName) {
  const coord = STATION_CENTER[stationName];
  if (!coord) return null;
  const lat = coord[0];
  const lng = coord[1];
  const minLat = 1.23;
  const maxLat = 1.47;
  const minLng = 103.60;
  const maxLng = 104.02;
  const x = ((lng - minLng) / (maxLng - minLng)) * 100;
  const y = (1 - ((lat - minLat) / (maxLat - minLat))) * 100;
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
  return { x: Math.max(2, Math.min(98, x)), y: Math.max(2, Math.min(98, y)) };
}

function getMrtImageGeometry() {
  const wrap = document.getElementById("mrt-map-wrap");
  const img = document.querySelector(".mrt-map-img");
  if (!wrap || !img) return null;
  const wrapRect = wrap.getBoundingClientRect();
  const naturalW = img.naturalWidth || 2048;
  const naturalH = img.naturalHeight || 1576;
  const imageRatio = naturalW / naturalH;
  const boxRatio = wrapRect.width / wrapRect.height;
  let renderW = wrapRect.width;
  let renderH = wrapRect.height;
  if (boxRatio > imageRatio) {
    renderW = wrapRect.height * imageRatio;
  } else {
    renderH = wrapRect.width / imageRatio;
  }
  const offsetX = (wrapRect.width - renderW) / 2;
  const offsetY = (wrapRect.height - renderH) / 2;
  return { wrap, img, wrapRect, naturalW, naturalH, renderW, renderH, offsetX, offsetY };
}

function buildStationImageCoords(naturalW, naturalH) {
  return Object.keys(STATION_CENTER).map(function (stationName) {
    const p = stationToMapPercent(stationName);
    if (!p) return null;
    return {
      name: stationName,
      x: (p.x / 100) * naturalW,
      y: (p.y / 100) * naturalH
    };
  }).filter(Boolean);
}

let mrtMapClickBound = false;
const MRT_MAP_DEBUG = (new URLSearchParams(window.location.search).get("mrtdebug") === "1");

function ensureMrtDebugDot(container) {
  if (!container) return null;
  let dot = container.querySelector(".mrt-debug-dot");
  if (!dot) {
    dot = document.createElement("div");
    dot.className = "mrt-debug-dot";
    dot.style.display = "none";
    container.appendChild(dot);
  }
  return dot;
}

function renderMrtImageHotspots(selected) {
  const geo = getMrtImageGeometry();
  const overlay = document.getElementById("mrt-map-hotspots");
  if (!overlay || !geo) return;
  overlay.innerHTML = "";
  const coords = buildStationImageCoords(geo.naturalW, geo.naturalH);
  coords.forEach(function (station) {
    const left = geo.offsetX + (station.x / geo.naturalW) * geo.renderW;
    const top = geo.offsetY + (station.y / geo.naturalH) * geo.renderH;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "mrt-map-hotspot" + (selected.indexOf(station.name) !== -1 ? " selected" : "");
    btn.style.left = left + "px";
    btn.style.top = top + "px";
    btn.title = station.name;
    btn.setAttribute("aria-label", station.name);
    btn.addEventListener("click", function () {
      toggleStation(station.name);
      const stationSearch = document.getElementById("mrt-search");
      filterStations(stationSearch ? stationSearch.value : "");
    });
    overlay.appendChild(btn);
  });

  if (!mrtMapClickBound) {
    mrtMapClickBound = true;
    geo.wrap.addEventListener("click", function (event) {
      if (event.target && event.target.classList && event.target.classList.contains("mrt-map-hotspot")) {
        return;
      }
      const currentGeo = getMrtImageGeometry();
      if (!currentGeo) return;
      const xInWrap = event.clientX - currentGeo.wrapRect.left;
      const yInWrap = event.clientY - currentGeo.wrapRect.top;

      if (
        xInWrap < currentGeo.offsetX ||
        xInWrap > currentGeo.offsetX + currentGeo.renderW ||
        yInWrap < currentGeo.offsetY ||
        yInWrap > currentGeo.offsetY + currentGeo.renderH
      ) {
        return;
      }

      const xOriginal = ((xInWrap - currentGeo.offsetX) / currentGeo.renderW) * currentGeo.naturalW;
      const yOriginal = ((yInWrap - currentGeo.offsetY) / currentGeo.renderH) * currentGeo.naturalH;
      const stations = buildStationImageCoords(currentGeo.naturalW, currentGeo.naturalH);
      let nearest = null;
      let bestDist = Infinity;
      stations.forEach(function (station) {
        const dx = xOriginal - station.x;
        const dy = yOriginal - station.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < bestDist) {
          bestDist = dist;
          nearest = station;
        }
      });

      const maxClickRadiusDisplayPx = 26;
      const scaleX = currentGeo.naturalW / currentGeo.renderW;
      const maxClickRadiusOriginalPx = maxClickRadiusDisplayPx * scaleX;
      if (MRT_MAP_DEBUG) {
        const dot = ensureMrtDebugDot(currentGeo.wrap);
        if (dot) {
          dot.style.left = xInWrap + "px";
          dot.style.top = yInWrap + "px";
          dot.style.display = "block";
        }
        console.log("[MRT DEBUG]", {
          click_display: { x: Number(xInWrap.toFixed(2)), y: Number(yInWrap.toFixed(2)) },
          click_original: { x: Number(xOriginal.toFixed(2)), y: Number(yOriginal.toFixed(2)) },
          nearest_station: nearest ? nearest.name : null,
          nearest_distance_original_px: Number(bestDist.toFixed(2)),
          threshold_original_px: Number(maxClickRadiusOriginalPx.toFixed(2))
        });
      }
      if (nearest && bestDist <= maxClickRadiusOriginalPx) {
        toggleStation(nearest.name);
        const stationSearch = document.getElementById("mrt-search");
        filterStations(stationSearch ? stationSearch.value : "");
      }
    });
  }
}

function stationCode(lineKey, index) {
  return (MRT_LINE_CODE_PREFIX[lineKey] || lineKey) + String(index + 1);
}

function renderLineChips() {
  const wrap = document.getElementById("mrt-line-chips");
  if (!wrap) return;
  wrap.innerHTML = "";
  mrtLineGroups.forEach(function (line) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "mrt-line-chip" + (line.key === selectedLineKey ? " active" : "");
    chip.style.background = line.key === selectedLineKey ? (mrtLineColor[line.key] || "#0f172a") : "#ffffff";
    chip.textContent = (MRT_LINE_CODE_PREFIX[line.key] || line.key) + " • " + line.label;
    chip.setAttribute("aria-pressed", line.key === selectedLineKey ? "true" : "false");
    chip.addEventListener("click", function () {
      selectedLineKey = line.key;
      renderLineChips();
      renderLineStations();
    });
    wrap.appendChild(chip);
  });
}

function renderLineStations() {
  const wrap = document.getElementById("mrt-station-buttons");
  if (!wrap) return;
  wrap.innerHTML = "";
  const line = mrtLineGroups.find(function (l) { return l.key === selectedLineKey; }) || mrtLineGroups[0];
  if (!line) return;
  line.stations.forEach(function (stationName, idx) {
    const code = stationCode(line.key, idx);
    const selected = selectedStations.indexOf(stationName) !== -1;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "mrt-station-btn" + (selected ? " selected" : "");
    btn.style.setProperty("--line-stripe", stationStripe(stationName));
    btn.innerHTML = "<strong>" + stationName + "</strong><span>" + code + "</span>";
    btn.setAttribute("aria-pressed", selected ? "true" : "false");
    btn.addEventListener("click", function () {
      toggleStation(stationName);
    });
    wrap.appendChild(btn);
  });
}

function filterStations(query, lineFilter) {
  if (typeof lineFilter === "string") activeLineFilter = lineFilter;
  var allowedKeys = LINE_FILTER_TO_KEYS[activeLineFilter] || null;
  const q = (query || '').toLowerCase();
  const filtered = mrtStations.filter(function (s) {
    var searchOk = s.toLowerCase().includes(q);
    if (!searchOk) return false;
    if (!allowedKeys || !allowedKeys.length) return true;
    var keys = stationLineKeys(s);
    return keys.some(function (k) { return allowedKeys.indexOf(k) !== -1; });
  });
  renderStationOptions(filtered, selectedStations);
  renderSchematicMap(filtered, selectedStations);
  renderMrtImageHotspots(selectedStations);
}

function toggleStation(name) {
  const idx = selectedStations.indexOf(name);
  if (idx === -1) {
    selectedStations.push(name);
  } else {
    selectedStations.splice(idx, 1);
  }
  renderLineStations();
  renderSelectedStations();
}

function removeStation(name) {
  selectedStations = selectedStations.filter(function (s) { return s !== name; });
  renderLineStations();
  renderSelectedStations();
}

function renderSelectedStations() {
  const tags = document.getElementById('selected-stations-tags');
  const listEl = document.getElementById('selected-stations-list');
  if (!tags) return;
  tags.innerHTML = '';
  if (listEl) listEl.innerHTML = '';
  if (!selectedStations.length) {
    tags.innerHTML = '<span class="selected-stations-empty">No stations selected yet.</span>';
    if (listEl) listEl.innerHTML = '<li>No station selected</li>';
    updateMidpointSuggestion();
    return;
  }
  selectedStations.forEach(function (name) {
    const tag = document.createElement('span');
    tag.className = 'station-tag';
    tag.innerHTML = `
      <span>${name}</span>
      <button type="button" class="station-tag-remove" aria-label="Remove ${name}">x</button>
    `;
    const removeBtn = tag.querySelector('.station-tag-remove');
    if (removeBtn) {
      removeBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        removeStation(name);
      });
    }
    tags.appendChild(tag);
    if (listEl) {
      const li = document.createElement("li");
      li.textContent = name;
      listEl.appendChild(li);
    }
  });
  updateMidpointSuggestion();
}

function suggestMidpoint(stations) {
  if (!stations || stations.length < 2) return null;
  const built = buildRouteGraph();
  const candidates = Array.from(built.nodesByStation.keys());
  if (!candidates.length) return null;

  const uniqueStarts = Array.from(new Set(stations)).filter(function (name) {
    return built.nodesByStation.has(name);
  });
  if (uniqueStarts.length < 2) return null;

  let bestStation = null;
  let bestFairness = Infinity;
  let bestTotal = Infinity;

  candidates.forEach(function (candidate) {
    const times = uniqueStarts
      .map(function (startStation) {
        return shortestMinutesBetweenStations(startStation, candidate);
      })
      .filter(function (minutes) { return minutes !== null; });

    if (times.length !== uniqueStarts.length) return;

    const minTime = Math.min.apply(null, times);
    const maxTime = Math.max.apply(null, times);
    const fairness = maxTime - minTime;
    const total = times.reduce(function (sum, value) { return sum + value; }, 0);

    if (fairness < bestFairness || (fairness === bestFairness && total < bestTotal)) {
      bestFairness = fairness;
      bestTotal = total;
      bestStation = candidate;
    }
  });

  return bestStation;
}

const STATION_CENTER = {
  "Toa Payoh": [1.3320, 103.8474],
  "Bishan": [1.3508, 103.8480],
  "Serangoon": [1.3497, 103.8737],
  "Bugis": [1.3009, 103.8552],
  "City Hall": [1.2931, 103.8520],
  "Dhoby Ghaut": [1.2993, 103.8458],
  "Paya Lebar": [1.3174, 103.8921],
  "Jurong East": [1.3332, 103.7422],
  "Outram Park": [1.2819, 103.8392],
};

let realMap = null;
let realMapMarkers = [];
let realMapHeatCircles = [];

function midpointCenter(midpoint) {
  return STATION_CENTER[midpoint] || [1.3521, 103.8198];
}

function centerFromStations(stations) {
  const points = (stations || [])
    .map(function (s) { return STATION_CENTER[s]; })
    .filter(Boolean);
  if (!points.length) return [1.3521, 103.8198];
  const sum = points.reduce(function (acc, point) {
    return [acc[0] + point[0], acc[1] + point[1]];
  }, [0, 0]);
  return [sum[0] / points.length, sum[1] / points.length];
}

function clearLeafletMarkers() {
  if (!realMapMarkers.length) return;
  realMapMarkers.forEach(function (marker) {
    if (realMap) realMap.removeLayer(marker);
  });
  realMapMarkers = [];
}

function clearLeafletHeatmap() {
  if (!realMapHeatCircles.length) return;
  realMapHeatCircles.forEach(function (circle) {
    if (realMap) realMap.removeLayer(circle);
  });
  realMapHeatCircles = [];
}

function initRealMap() {
  if (realMap || typeof window.L === "undefined") return;
  const mapEl = document.getElementById("realMap");
  if (!mapEl) return;

  realMap = window.L.map("realMap", { zoomControl: true }).setView([1.3521, 103.8198], 12);
  window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap",
    maxZoom: 19
  }).addTo(realMap);
}

function iconForVenueType(type) {
  var t = (type || "").toLowerCase();
  if (t.indexOf("library") !== -1) return "📚";
  if (t.indexOf("community") !== -1) return "🏢";
  if (t.indexOf("senior") !== -1) return "🧓";
  if (t.indexOf("cafe") !== -1 || t.indexOf("coffee") !== -1) return "☕";
  if (t.indexOf("park") !== -1) return "🌳";
  return "📍";
}

async function fetchSafeVenues(stations) {
  if (!stations || !stations.length) return [];
  const qs = encodeURIComponent(stations.join(","));
  const res = await fetch("/api/safe_locations?stations=" + qs);
  if (!res.ok) return [];
  const rows = await res.json().catch(function () { return []; });
  if (!Array.isArray(rows)) return [];
  return rows.map(function (row, idx) {
    return {
      id: "venue-" + idx + "-" + (row.place_name || "").replace(/\s+/g, "-").toLowerCase(),
      icon: iconForVenueType(row.venue_type),
      type: row.venue_type || "venue",
      name: row.place_name || "Safe venue",
      walk: row.walking_mins ? (row.walking_mins + " min walk from " + row.station_name + " MRT") : ("Near " + row.station_name + " MRT"),
      station_name: row.station_name || "",
      address: row.address || "",
      lat: Number(row.lat),
      lng: Number(row.lng),
      walking_mins: row.walking_mins
    };
  }).filter(function (row) {
    return Number.isFinite(row.lat) && Number.isFinite(row.lng);
  });
}

function updateMidpointSuggestion() {
  const midpointEl = document.getElementById("midpoint-station");
  const midpointMetaEl = document.querySelector(".midpoint-meta");
  const breakdownEl = document.getElementById("midpoint-breakdown");
  const midpoint = suggestMidpoint(selectedStations);
  if (midpointEl) {
    midpointEl.textContent = midpoint ? ("📍 " + midpoint + " MRT") : "Midpoint unavailable.";
  }
  if (midpointMetaEl) {
    midpointMetaEl.textContent = midpoint
      ? "Travel time balanced for both users"
      : "Select stations to calculate a midpoint.";
  }
  if (breakdownEl) {
    if (midpoint && selectedStations.length >= 2) {
      const userA = selectedStations[0];
      const userB = selectedStations[1];
      const routeA = shortestRouteDetails(userA, midpoint);
      const routeB = shortestRouteDetails(userB, midpoint);
      const lineA = routeA ? `User A (${userA}) → ${routeA.minutes} mins, transfers ${routeA.transfers}` : "";
      const lineB = routeB ? `User B (${userB}) → ${routeB.minutes} mins, transfers ${routeB.transfers}` : "";
      breakdownEl.innerHTML = `<div>${lineA}</div><div>${lineB}</div>`;
    } else {
      breakdownEl.innerHTML = "";
    }
  }
}

function renderRealMapPopup(venue) {
  const icon = document.getElementById("real-map-popup-icon");
  const name = document.getElementById("real-map-popup-name");
  const type = document.getElementById("real-map-popup-type");
  const walk = document.getElementById("real-map-popup-walk");
  if (icon) icon.textContent = venue.icon;
  if (name) name.textContent = venue.name;
  if (type) type.textContent = venue.type;
  if (walk) walk.textContent = venue.walk;
}

function renderMapMarkers(venues, activeId) {
  if (realMap) {
    clearLeafletMarkers();
    venues.forEach(function (venue) {
      const icon = window.L.divIcon({
        className: "leaflet-venue-icon",
        html: '<div style="width:34px;height:34px;border-radius:999px;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 6px 16px rgba(15,23,42,.24);border:2px solid ' + (venue.id === activeId ? "#14b8a6" : "#ffffff") + ';">' + venue.icon + "</div>",
        iconSize: [34, 34],
        iconAnchor: [17, 17]
      });
      const marker = window.L.marker([venue.lat, venue.lng], { icon: icon }).addTo(realMap);
      marker.on("click", function () {
        setActiveVenue(venue.id);
      });
      marker.bindPopup(
        "<strong>" + venue.name + "</strong><br>" +
        venue.type + "<br>" +
        venue.walk
      );
      realMapMarkers.push(marker);
    });
    return;
  }

  const markers = document.getElementById("real-map-markers");
  if (!markers) return;
  markers.innerHTML = "";
  venues.forEach(function (venue) {
    const marker = document.createElement("button");
    marker.type = "button";
    marker.className = "map-marker" + (venue.id === activeId ? " active" : "");
    marker.style.left = venue.position.x + "%";
    marker.style.top = venue.position.y + "%";
    marker.textContent = venue.icon;
    marker.setAttribute("aria-label", venue.name);
    marker.addEventListener("click", function () {
      setActiveVenue(venue.id);
    });
    markers.appendChild(marker);
  });
}

let currentVenues = [];
let currentActiveVenueId = "library";

function setActiveVenue(venueId) {
  currentActiveVenueId = venueId;
  const venue = currentVenues.find(function (v) { return v.id === venueId; }) || currentVenues[0];
  if (!venue) return;
  const popup = document.getElementById("real-map-popup");
  if (popup) popup.style.display = "";
  document.querySelectorAll(".venue-card").forEach(function (card) {
    card.classList.toggle("active", card.getAttribute("data-venue-id") === venue.id);
  });
  renderRealMapPopup(venue);
  renderMapMarkers(currentVenues, venue.id);
  if (realMap) {
    realMap.flyTo([venue.lat, venue.lng], 14, { duration: 0.45 });
  }
}

function renderSafeVenueCards(midpoint) {
  const grid = document.getElementById("safe-venue-list");
  if (!grid) return;
  if (!midpoint) {
    grid.innerHTML = '<div class="selected-stations-empty">Select at least 2 stations to get midpoint-based venue recommendations.</div>';
    return;
  }
  if (!currentVenues.length) {
    grid.innerHTML = '<div class="selected-stations-empty">No curated safe venues found for ' + midpoint + ' yet.</div>';
    return;
  }
  grid.innerHTML = currentVenues.map(function (spot) {
    return (
      '<article class="safe-venue-card">' +
      '<h5>' + spot.icon + " " + spot.name + "</h5>" +
      '<p>' + spot.walk + "</p>" +
      "</article>"
    );
  }).join("");
}

async function refreshSafeVenues() {
  const midpoint = suggestMidpoint(selectedStations);
  if (!midpoint) {
    currentVenues = [];
    renderSafeVenueCards(null);
    return;
  }
  try {
    currentVenues = await fetchSafeVenues([midpoint]);
  } catch (err) {
    currentVenues = [];
  }
  renderSafeVenueCards(midpoint);
}

function setMrtViewMode(mode) {
  mrtViewMode = mode === "map" ? "map" : "list";
  const isRealMap = mrtViewMode === "map";
  const schematic = document.getElementById("mrt-schematic");
  const realMapPanel = document.getElementById("real-map-panel");
  const options = document.getElementById("mrt-options");

  if (schematic) schematic.hidden = isRealMap;
  if (realMapPanel) realMapPanel.hidden = !isRealMap;
  if (options) options.hidden = true;

  if (isRealMap) {
    initRealMap();
    setTimeout(function () {
      if (realMap) {
        realMap.invalidateSize();
      }
    }, 220);
  }

  document.querySelectorAll(".mrt-view-btn").forEach(function (b) {
    const active = (b.getAttribute("data-mrt-view") || "list") === mrtViewMode;
    b.classList.toggle("active", active);
    b.setAttribute("aria-selected", active ? "true" : "false");
  });
}

const stationSearch = document.getElementById('mrt-search');
if (stationSearch) {
  stationSearch.addEventListener('input', function () {
    filterStations(stationSearch.value, activeLineFilter);
  });
}

document.querySelectorAll(".mrt-line-filter-chip").forEach(function (chip) {
  chip.addEventListener("click", function () {
    var line = chip.getAttribute("data-line-filter") || "ALL";
    activeLineFilter = line;
    document.querySelectorAll(".mrt-line-filter-chip").forEach(function (c) {
      c.classList.toggle("active", c === chip);
    });
    filterStations(stationSearch ? stationSearch.value : "", activeLineFilter);
  });
});

document.querySelectorAll(".mrt-view-btn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    setMrtViewMode(btn.getAttribute("data-mrt-view") || "list");
    const stationSearch = document.getElementById("mrt-search");
    filterStations(stationSearch ? stationSearch.value : "");
  });
});

const findSafeBtn = document.getElementById("find-safe-locations");
if (findSafeBtn) {
  findSafeBtn.addEventListener("click", function () {
    refreshSafeVenues();
  });
}

const heatToggle = document.getElementById("real-map-heat-toggle");
const heatOverlay = document.getElementById("real-map-heat-overlay");
const heatLabel = document.getElementById("real-map-heat-label");
function applyHeatmapState() {
  const on = !!(heatToggle && heatToggle.checked);
  if (heatOverlay) heatOverlay.classList.toggle("show", on);
  if (heatLabel) heatLabel.textContent = on ? "ON" : "OFF";
  if (!realMap) return;
  clearLeafletHeatmap();
  if (!on) return;
  currentVenues.forEach(function (venue) {
    const circle = window.L.circle([venue.lat, venue.lng], {
      radius: 500,
      color: "#14b8a6",
      fillColor: "#14b8a6",
      fillOpacity: 0.15,
      weight: 1
    }).addTo(realMap);
    realMapHeatCircles.push(circle);
  });
}

if (heatToggle) {
  heatToggle.addEventListener("change", function () {
    applyHeatmapState();
  });
}

const clearSelectionBtn = document.getElementById("mrt-clear-selection");
if (clearSelectionBtn) {
  clearSelectionBtn.addEventListener("click", function () {
    selectedStations = [];
    renderLineStations();
    renderSelectedStations();
  });
}

if (preloaded && Array.isArray(preloaded.stations)) {
  selectedStations = [...new Set(preloaded.stations)];
}

filterStations("", "ALL");
renderSelectedStations();
renderMrtImageHotspots(selectedStations);
setMrtViewMode(mrtViewMode);
renderLineChips();
renderLineStations();
window.addEventListener("resize", function () {
  renderMrtImageHotspots(selectedStations);
});
