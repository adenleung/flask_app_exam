// Profile Page Tab Switching

function demoHeaders(extra) {
  const headers = extra ? { ...extra } : {};
  const demoId = sessionStorage.getItem('demo_user_id');
  if (demoId) headers['X-Demo-User'] = demoId;
  return headers;
}

function openUiModal(options) {
  const uiModal = document.getElementById('ui-modal');
  const uiTitle = document.getElementById('ui-modal-title');
  const uiBody = document.getElementById('ui-modal-body');
  const uiActions = document.getElementById('ui-modal-actions');
  if (!uiModal || !uiTitle || !uiBody || !uiActions) return null;
  uiTitle.textContent = options.title || 'Notice';
  uiBody.innerHTML = options.bodyHtml || '';
  uiActions.innerHTML = options.actionsHtml || '';
  uiModal.classList.add('show');
  return uiModal;
}

function closeUiModal() {
  const uiModal = document.getElementById('ui-modal');
  if (uiModal) uiModal.classList.remove('show');
}

function uiAlert(message, title) {
  openUiModal({
    title: title || 'Notice',
    bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">${escapeHtml(message || '')}</div>`,
    actionsHtml: '<button class="ui-btn primary" id="ui-alert-ok">OK</button>',
  });
  const ok = document.getElementById('ui-alert-ok');
  if (ok) ok.addEventListener('click', closeUiModal);
}

function uiConfirm(message, title, confirmLabel, cancelLabel) {
  return new Promise((resolve) => {
    openUiModal({
      title: title || 'Confirm',
      bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">${escapeHtml(message || '')}</div>`,
      actionsHtml: `
        <button class="ui-btn" id="ui-confirm-cancel">${escapeHtml(cancelLabel || 'Cancel')}</button>
        <button class="ui-btn danger" id="ui-confirm-ok">${escapeHtml(confirmLabel || 'Confirm')}</button>
      `,
    });
    const cancel = document.getElementById('ui-confirm-cancel');
    const confirm = document.getElementById('ui-confirm-ok');
    if (cancel) cancel.addEventListener('click', () => { closeUiModal(); resolve(false); });
    if (confirm) confirm.addEventListener('click', () => { closeUiModal(); resolve(true); });
  });
}

document.addEventListener('DOMContentLoaded', function() {
  const tabBtns = document.querySelectorAll('.profile-tab-btn');
  const tabContents = document.querySelectorAll('.profile-tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      const tabName = this.dataset.tab;

      // Remove active from all
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      // Add active to clicked
      this.classList.add('active');
      const targetContent = document.getElementById(`tab-${tabName}`);
      if (targetContent) {
        targetContent.classList.add('active');
      }

      // Scroll to top
      window.scrollTo({ top: 200, behavior: 'smooth' });
    });
  });

  // Load profile data
  loadProfile();

  // Edit Bio functionality
  const editBioBtn = document.getElementById('edit-bio-btn');
  if (editBioBtn) {
    editBioBtn.addEventListener('click', function() {
      const bioText = document.getElementById('bio-text');
      if (!bioText) return;

      const currentBio = bioText.textContent || '';
      const textarea = document.createElement('textarea');
      textarea.value = currentBio;
      textarea.className = 'bio-edit-textarea';
      textarea.rows = 4;
      textarea.style.width = '100%';
      textarea.style.marginBottom = '10px';

      const saveBtn = document.createElement('button');
      saveBtn.textContent = 'Save';
      saveBtn.className = 'btn bio-save-btn';

      const cancelBtn = document.createElement('button');
      cancelBtn.textContent = 'Cancel';
      cancelBtn.className = 'btn btn-secondary bio-cancel-btn';

      const buttonContainer = document.createElement('div');
      buttonContainer.className = 'bio-action-buttons';
      buttonContainer.appendChild(saveBtn);
      buttonContainer.appendChild(cancelBtn);

      // Replace bio text with textarea and buttons
      bioText.style.display = 'none';
      editBioBtn.style.display = 'none';
      bioText.parentNode.insertBefore(textarea, bioText);
      bioText.parentNode.insertBefore(buttonContainer, bioText);

      saveBtn.addEventListener('click', function() {
        const newBio = textarea.value.trim();
        updateBio(newBio);
      });

      cancelBtn.addEventListener('click', function() {
        // Restore original
        textarea.remove();
        buttonContainer.remove();
        bioText.style.display = '';
        editBioBtn.style.display = '';
      });
    });
  }

  document.querySelector('.btn-danger')?.addEventListener('click', async function() {
    const ok = await uiConfirm('\u26A0\uFE0F Are you SURE you want to delete your account? This action cannot be undone.', 'Delete Account', 'Delete');
    if (ok) {
      uiAlert('Account deletion process initiated. You will receive a confirmation email.', 'Request Sent');
    }
  });

  const mediaModal = document.getElementById('media-choice-modal');
  const mediaCameraBtn = document.getElementById('media-choice-camera');
  const mediaUploadBtn = document.getElementById('media-choice-upload');
  const mediaCancelBtn = document.getElementById('media-choice-cancel');
  let activeMediaTarget = null;

  function openMediaModal(target) {
    activeMediaTarget = target;
    if (mediaModal) {
      mediaModal.classList.add('show');
      mediaModal.setAttribute('aria-hidden', 'false');
    }
  }

  function closeMediaModal() {
    activeMediaTarget = null;
    if (mediaModal) {
      mediaModal.classList.remove('show');
      mediaModal.setAttribute('aria-hidden', 'true');
    }
  }

  if (mediaCancelBtn) mediaCancelBtn.addEventListener('click', closeMediaModal);
  const uiModalClose = document.getElementById('ui-modal-close');
  if (uiModalClose) uiModalClose.addEventListener('click', closeUiModal);
  const uiModal = document.getElementById('ui-modal');
  if (uiModal) {
    uiModal.addEventListener('click', function (e) {
      if (e.target === uiModal) closeUiModal();
    });
  }
  if (mediaModal) {
    mediaModal.addEventListener('click', function (e) {
      if (e.target === mediaModal) closeMediaModal();
    });
  }

  const avatarBtn = document.getElementById('edit-avatar-btn');
  const bannerBtn = document.getElementById('edit-banner-btn');
  const avatarCamera = document.getElementById('avatar-input-camera');
  const avatarUpload = document.getElementById('avatar-input-upload');
  const bannerCamera = document.getElementById('banner-input-camera');
  const bannerUpload = document.getElementById('banner-input-upload');

  if (avatarBtn) avatarBtn.addEventListener('click', () => openMediaModal('avatar'));
  if (bannerBtn) bannerBtn.addEventListener('click', () => openMediaModal('banner'));

  if (mediaCameraBtn) {
    mediaCameraBtn.addEventListener('click', function () {
      if (activeMediaTarget === 'avatar' && avatarCamera) avatarCamera.click();
      if (activeMediaTarget === 'banner' && bannerCamera) bannerCamera.click();
      closeMediaModal();
    });
  }

  if (mediaUploadBtn) {
    mediaUploadBtn.addEventListener('click', function () {
      if (activeMediaTarget === 'avatar' && avatarUpload) avatarUpload.click();
      if (activeMediaTarget === 'banner' && bannerUpload) bannerUpload.click();
      closeMediaModal();
    });
  }

  async function handleAvatarUpload(input) {
    if (!input || !input.files || !input.files[0]) return;
    const form = new FormData();
    form.append('avatar', input.files[0]);
    const res = await fetch('/api/profile/avatar', { method: 'POST', headers: demoHeaders(), body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return uiAlert(data.error || 'Could not upload avatar.', 'Upload Failed');
    const img = document.getElementById('profile-avatar');
    if (img) img.src = data.url;
  }

  async function handleBannerUpload(input) {
    if (!input || !input.files || !input.files[0]) return;
    const form = new FormData();
    form.append('banner', input.files[0]);
    const res = await fetch('/api/profile/banner', { method: 'POST', headers: demoHeaders(), body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return uiAlert(data.error || 'Could not upload banner.', 'Upload Failed');
    const cover = document.getElementById('profile-cover');
    if (cover) cover.style.backgroundImage = `url('${data.url}')`;
  }

  if (avatarCamera) avatarCamera.addEventListener('change', () => handleAvatarUpload(avatarCamera));
  if (avatarUpload) avatarUpload.addEventListener('change', () => handleAvatarUpload(avatarUpload));
  if (bannerCamera) bannerCamera.addEventListener('change', () => handleBannerUpload(bannerCamera));
  if (bannerUpload) bannerUpload.addEventListener('change', () => handleBannerUpload(bannerUpload));

  const editTeach = document.getElementById('edit-skills-teach');
  if (editTeach) {
    editTeach.addEventListener('click', () => {
      window.location.href = '/onboarding?edit=1&step=3&return=profile&tab=interests';
    });
  }

  const editLearn = document.getElementById('edit-skills-learn');
  if (editLearn) {
    editLearn.addEventListener('click', () => {
      window.location.href = '/onboarding?edit=1&step=4&return=profile&tab=interests';
    });
  }

  const editInterests = document.getElementById('edit-interests');
  if (editInterests) {
    editInterests.addEventListener('click', () => {
      window.location.href = '/onboarding?edit=1&step=2&return=profile&tab=interests';
    });
  }

  const safetyInfo = document.getElementById('safety-score-info');
  if (safetyInfo) {
    safetyInfo.addEventListener('click', () => {
      uiAlert('Your Safety Score grows with positive activity (circles, good behavior) and drops with confirmed violations or no-shows.', 'Safety Score');
    });
  }

  async function loadBlockConnections() {
    const targetSelect = document.getElementById('report-target');
    if (!targetSelect) return;
    try {
      const res = await fetch('/api/matches', { headers: demoHeaders() });
      const rows = await res.json().catch(() => []);
      if (!Array.isArray(rows)) return;
      targetSelect.innerHTML = '<option value="">Select connection to block (optional)</option>';
      rows.forEach((row) => {
        const opt = document.createElement('option');
        opt.value = row.match_id || '';
        opt.textContent = row.name || row.match_id || 'Connection';
        targetSelect.appendChild(opt);
      });
    } catch (_) {
    }
  }

  const reportBtn = document.getElementById('submit-report');
  if (reportBtn) {
    reportBtn.addEventListener('click', async () => {
      const reason = (document.getElementById('report-reason')?.value || '').trim();
      const date = (document.getElementById('report-date')?.value || '').trim();
      const details = (document.getElementById('report-details')?.value || '').trim();
      const targetMatchId = (document.getElementById('report-target')?.value || '').trim();
      const blockNow = !!document.getElementById('report-block-now')?.checked;
      if (!reason || !date) return uiAlert('Please select a reason and date.', 'Missing Details');
      const res = await fetch('/api/report', {
        method: 'POST',
        headers: demoHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ reason: reason, incident_date: date, details: details, target_match_id: targetMatchId, block_connection: blockNow })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) return uiAlert(data.error || 'Could not submit report.', 'Submit Failed');
      uiAlert(blockNow ? 'Report submitted and connection blocked.' : 'Report submitted. Our safety team will review it.', 'Report Submitted');
      if (document.getElementById('report-target')) document.getElementById('report-target').value = '';
      if (document.getElementById('report-reason')) document.getElementById('report-reason').value = '';
      if (document.getElementById('report-date')) document.getElementById('report-date').value = '';
      if (document.getElementById('report-details')) document.getElementById('report-details').value = '';
      if (document.getElementById('report-block-now')) document.getElementById('report-block-now').checked = false;
    });
  }
  loadBlockConnections();

  const saveEmergency = document.getElementById('save-emergency');
  const emergencyPhoneInput = document.getElementById('emergency-phone');
  if (emergencyPhoneInput) {
    emergencyPhoneInput.addEventListener('input', function () {
      emergencyPhoneInput.value = emergencyPhoneInput.value.replace(/\D+/g, '');
    });
  }
  if (saveEmergency) {
    saveEmergency.addEventListener('click', async () => {
      const name = (document.getElementById('emergency-name')?.value || '').trim();
      const relationship = (document.getElementById('emergency-relationship')?.value || '').trim();
      const code = (document.getElementById('emergency-phone-code')?.value || '+65').trim();
      const phoneDigits = (document.getElementById('emergency-phone')?.value || '').replace(/\D+/g, '');
      if ((document.getElementById('emergency-phone')?.value || '').trim() && !phoneDigits) {
        uiAlert('Phone number should contain digits only.', 'Invalid Phone');
        return;
      }
      const phone = phoneDigits ? `${code} ${phoneDigits}` : '';
      await saveProfile({ emergency_contact: { name, relationship, phone } });
      uiAlert('Emergency contact saved.', 'Saved');
    });
  }

  const verifyEmail = document.getElementById('verify-email');
  if (verifyEmail) {
    verifyEmail.addEventListener('click', async () => {
      await saveProfile({ verified_with: 'email' });
      uiAlert('Email verification marked as completed.', 'Verified');
    });
  }
  const verifyPhone = document.getElementById('verify-phone');
  if (verifyPhone) {
    verifyPhone.addEventListener('click', async () => {
      await saveProfile({ verified_with: 'phone' });
      uiAlert('Phone verification marked as completed.', 'Verified');
    });
  }

  ['notif-messages','notif-matches','notif-circles','notif-challenges','notif-badges',
   'privacy-age','privacy-location','privacy-badges','privacy-direct'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', () => {
        const notifications = {
          messages: !!document.getElementById('notif-messages')?.checked,
          matches: !!document.getElementById('notif-matches')?.checked,
          circles: !!document.getElementById('notif-circles')?.checked,
          challenges: !!document.getElementById('notif-challenges')?.checked,
          badges: !!document.getElementById('notif-badges')?.checked,
        };
        const privacy = {
          show_age: !!document.getElementById('privacy-age')?.checked,
          show_location: !!document.getElementById('privacy-location')?.checked,
          show_badges: !!document.getElementById('privacy-badges')?.checked,
          allow_direct: !!document.getElementById('privacy-direct')?.checked,
        };
        saveProfile({ notifications, privacy });
      });
    }
  });

  const MRT_STATIONS = [
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

  const MRT_LINE_HINTS = {
    NS: ["Admiralty","Ang Mo Kio","Bishan","Braddell","Canberra","Choa Chu Kang","City Hall","Dhoby Ghaut","Jurong East","Khatib","Kranji","Marina Bay","Marina South Pier","Novena","Orchard","Raffles Place","Sembawang","Somerset","Toa Payoh","Woodlands","Yew Tee","Yio Chu Kang","Yishun"],
    EW: ["Aljunied","Bedok","Boon Lay","Bugis","Buona Vista","Chinese Garden","Clementi","Commonwealth","Dover","Eunos","Expo","Joo Koon","Kallang","Kembangan","Lakeside","Lavender","Outram Park","Pasir Ris","Paya Lebar","Pioneer","Queenstown","Redhill","Simei","Tanah Merah","Tanjong Pagar","Tuas Crescent","Tuas Link","Tuas West Road"],
    DT: ["Bayfront","Beauty World","Bedok North","Bedok Reservoir","Bencoolen","Bendemeer","Botanic Gardens","Bukit Panjang","Cashew","Chinatown","Downtown","Expo","Fort Canning","Hillview","Jalan Besar","Kaki Bukit","King Albert Park","Little India","MacPherson","Mattar","Promenade","Rochor","Sixth Avenue","Stevens","Tan Kah Kee","Telok Ayer","Tampines","Tampines East","Tampines West","Ubi","Upper Changi"],
    NE: ["Buangkok","Chinatown","Clarke Quay","Dhoby Ghaut","Farrer Park","HarbourFront","Hougang","Kovan","Little India","Outram Park","Potong Pasir","Punggol","Sengkang","Serangoon","Woodleigh"],
    CC: ["Bartley","Bayfront","Botanic Gardens","Bras Basah","Buona Vista","Caldecott","Dakota","Dhoby Ghaut","Esplanade","Farrer Road","HarbourFront","Haw Par Villa","Holland Village","Labrador Park","Lorong Chuan","MacPherson","Marina Bay","Marymount","Mountbatten","Nicoll Highway","one-north","Pasir Panjang","Promenade","Serangoon","Stadium","Tai Seng"],
    TE: ["Bright Hill","Caldecott","Gardens by the Bay","Great World","Havelock","Lentor","Marine Parade","Marine Terrace","Maxwell","Mayflower","Napier","Orchard Boulevard","Outram Park","Shenton Way","Siglap","Springleaf","Stevens","Tanjong Katong","Tanjong Rhu","Upper Thomson","Woodlands North","Woodlands South"]
  };

  const LINE_FILTER_TO_KEYS = {
    ALL: null,
    NS: ["NS"],
    EW: ["EW"],
    DT: ["DT"],
    NE: ["NE"],
    CC: ["CC"],
    TE: ["TE"]
  };

  let activeProfileLineFilter = "ALL";
  const profileStationToLines = {};
  Object.keys(MRT_LINE_HINTS).forEach(function (line) {
    MRT_LINE_HINTS[line].forEach(function (station) {
      if (!profileStationToLines[station]) profileStationToLines[station] = [];
      if (profileStationToLines[station].indexOf(line) === -1) profileStationToLines[station].push(line);
    });
  });

  function stationLines(name) {
    return profileStationToLines[name] && profileStationToLines[name].length ? profileStationToLines[name] : ["NS"];
  }

  function lineColor(line) {
    if (line === "NS") return "#ef4444";
    if (line === "EW") return "#22c55e";
    if (line === "DT") return "#3b82f6";
    if (line === "NE") return "#a855f7";
    if (line === "CC") return "#f59e0b";
    if (line === "TE") return "#8b5e3c";
    return "#cbd5e1";
  }

  function stripeGradient(lines) {
    if (!lines || !lines.length) return lineColor("NS");
    if (lines.length === 1) return lineColor(lines[0]);
    const step = 100 / lines.length;
    const stops = lines.map(function (l, idx) {
      const start = (idx * step).toFixed(2);
      const end = ((idx + 1) * step).toFixed(2);
      return `${lineColor(l)} ${start}% ${end}%`;
    });
    return `linear-gradient(to bottom, ${stops.join(", ")})`;
  }

  let selectedStations = [];

  function renderProfileStations(list) {
    const container = document.getElementById('profile-mrt-options');
    if (!container) return;
    container.innerHTML = '';
    list.forEach(function (name) {
      const id = 'profile-mrt-' + name.replace(/\s+/g, '-').toLowerCase();
      const checked = selectedStations.indexOf(name) !== -1 ? 'checked' : '';
      const item = document.createElement('label');
      item.className = 'station-option';
      item.style.setProperty('--line-stripe', stripeGradient(stationLines(name)));
      item.style.setProperty('--line-color', lineColor(stationLines(name)[0]));
      item.innerHTML = `
        <input type="checkbox" class="profile-station-checkbox" id="${id}" value="${name}" ${checked}>
        <span>${name}</span>
      `;
      container.appendChild(item);
    });

    container.querySelectorAll('.profile-station-checkbox').forEach(function (cb) {
      cb.addEventListener('change', function () {
        const val = cb.value;
        if (cb.checked) {
          if (selectedStations.indexOf(val) === -1) selectedStations.push(val);
        } else {
          selectedStations = selectedStations.filter(s => s !== val);
        }
      });
    });
  }

  function filterProfileStations(query, lineFilter) {
    if (typeof lineFilter === 'string') activeProfileLineFilter = lineFilter;
    const allowed = LINE_FILTER_TO_KEYS[activeProfileLineFilter] || null;
    const q = (query || '').toLowerCase();
    const filtered = MRT_STATIONS.filter(function (s) {
      const searchOk = s.toLowerCase().includes(q);
      if (!searchOk) return false;
      if (!allowed || !allowed.length) return true;
      const lines = stationLines(s);
      return lines.some(function (l) { return allowed.indexOf(l) !== -1; });
    });
    renderProfileStations(filtered);
  }

  const profileSearch = document.getElementById('profile-mrt-search');
  if (profileSearch) {
    profileSearch.addEventListener('input', function () {
      filterProfileStations(profileSearch.value, activeProfileLineFilter);
    });
  }

  document.querySelectorAll('.profile-mrt-line-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      const line = chip.getAttribute('data-line-filter') || 'ALL';
      activeProfileLineFilter = line;
      document.querySelectorAll('.profile-mrt-line-chip').forEach(function (x) {
        x.classList.toggle('active', x === chip);
      });
      filterProfileStations(profileSearch ? profileSearch.value : '', activeProfileLineFilter);
    });
  });

  const profileSave = document.getElementById('profile-mrt-save-btn');
  if (profileSave) {
    profileSave.addEventListener('click', async () => {
      const name = selectedStations.join(', ');
      await saveProfile({ location_name: name });
      const display = document.getElementById('location-display');
      if (display && name) display.textContent = `\u{1F4CD} ${name}`;
    });
  }

  window.__setProfileStations = function (stations) {
    selectedStations = Array.isArray(stations) ? stations.slice() : [];
    filterProfileStations(profileSearch ? profileSearch.value : '', activeProfileLineFilter);
  };
});

function loadProfile() {
  fetch('/api/profile', { headers: (typeof demoHeaders === 'function' ? demoHeaders() : {}) })
    .then(response => response.json())
    .then(data => {
      if (data.ok) {
        const profile = data.profile;
        const bioText = document.getElementById('bio-text');
        if (bioText) {
          bioText.textContent = profile.bio || '';
        }
        const connections = document.getElementById('connections-count');
        if (connections) connections.textContent = profile.connections_count ?? 0;
        const memories = document.getElementById('memories-count');
        if (memories) memories.textContent = profile.memories_count ?? 0;
        const repoints = document.getElementById('repoints-count');
        if (repoints) repoints.textContent = profile.repoints ?? 0;

        const avatar = document.getElementById('profile-avatar');
        if (avatar && profile.avatar_url) avatar.src = profile.avatar_url;
        const cover = document.getElementById('profile-cover');
        if (cover && profile.banner_url) cover.style.backgroundImage = `url('${profile.banner_url}')`;

        const locDisplay = document.getElementById('location-display');
        const onboardingStations = Array.isArray(profile.onboarding?.stations) ? profile.onboarding.stations : [];
        const storedStations = profile.location_name
          ? profile.location_name.split(',').map(s => s.trim()).filter(Boolean)
          : [];
        const stationList = onboardingStations.length ? onboardingStations : storedStations;
        if (locDisplay && stationList.length) locDisplay.textContent = `\u{1F4CD} ${stationList.join(', ')}`;
        if (stationList.length && typeof window.__setProfileStations === 'function') {
          window.__setProfileStations(stationList);
        } else if (typeof window.__setProfileStations === 'function') {
          window.__setProfileStations([]);
        }
        const interests = Array.isArray(profile.onboarding?.interests) ? profile.onboarding.interests : [];
        const interestMap = {
          technology: '💻 Technology',
          cooking: '🍳 Cooking',
          gardening: '🌱 Gardening',
          music: '🎵 Music',
          art: '🎨 Arts & Crafts',
          reading: '📚 Reading',
          fitness: '💪 Fitness',
          photography: '📷 Photography',
          travel: '✈️ Travel',
          games: '🎮 Games',
          language: '🗣️ Languages',
          volunteering: '🤝 Volunteering'
        };
        const interestsWrap = document.querySelector('.interest-tags');
        if (interestsWrap) {
          if (interests.length) {
            interestsWrap.innerHTML = interests.map(i => `<span class="interest-tag">${interestMap[i] || escapeHtml(i)}</span>`).join('');
          } else {
            interestsWrap.innerHTML = '<span class="interest-tag">Add your top 3 interests</span>';
          }
        }
        const langs = profile.languages || [];
        document.querySelectorAll('.lang-checkbox').forEach(cb => {
          cb.checked = langs.includes(cb.value);
        });

        const teachList = document.getElementById('skills-teach-list');
        if (teachList) {
          const list = profile.skills_teach && profile.skills_teach.length ? profile.skills_teach : [];
          teachList.innerHTML = list.length
            ? list.map(s => `<li>\u2714\uFE0F ${escapeHtml(s)}</li>`).join('')
            : '<li class="text-muted">Add skills you can teach</li>';
        }
        const learnList = document.getElementById('skills-learn-list');
        if (learnList) {
          const list = profile.skills_learn && profile.skills_learn.length ? profile.skills_learn : [];
          learnList.innerHTML = list.length
            ? list.map(s => `<li>\u{1F3AF} ${escapeHtml(s)}</li>`).join('')
            : '<li class="text-muted">Add skills you want to learn</li>';
        }

        const emergency = profile.emergency_contact || {};
        if (document.getElementById('emergency-name')) document.getElementById('emergency-name').value = emergency.name || '';
        if (document.getElementById('emergency-relationship')) document.getElementById('emergency-relationship').value = emergency.relationship || '';
        const emergencyPhone = String(emergency.phone || '').trim();
        const phoneCodeEl = document.getElementById('emergency-phone-code');
        const phoneEl = document.getElementById('emergency-phone');
        const match = emergencyPhone.match(/^(\+\d+)\s*(.*)$/);
        if (phoneCodeEl) phoneCodeEl.value = (match && match[1]) || '+65';
        if (phoneEl) phoneEl.value = (match && match[2] ? match[2].replace(/\D+/g, '') : emergencyPhone.replace(/\D+/g, ''));

        const safety = profile.safety || {};
        const safetyValue = document.getElementById('safety-score-value');
        const safetyFill = document.getElementById('safety-score-fill');
        const safetyBadge = document.getElementById('safety-score-badge');
        const safetyEvents = document.getElementById('safety-events');
        if (safetyValue) safetyValue.textContent = safety.score ?? '--';
        if (safetyFill && typeof safety.score === 'number') {
          safetyFill.style.width = Math.min(100, Math.max(0, safety.score)) + '%';
          if (safety.tier === 'green') safetyFill.style.background = '#22c55e';
          else if (safety.tier === 'yellow') safetyFill.style.background = '#f59e0b';
          else safetyFill.style.background = '#ef4444';
        }
        if (safetyBadge) safetyBadge.style.display = safety.trusted ? '' : 'none';
        if (safetyEvents) {
          const events = Array.isArray(safety.events) ? safety.events : [];
          safetyEvents.innerHTML = events.length
            ? events.map(e => {
                const sign = e.points > 0 ? '+' : '';
                return `<div>${sign}${e.points} ${escapeHtml(e.details || e.event_type)}</div>`;
              }).join('')
            : '<div>No recent safety events yet.</div>';
        }

        const notifications = profile.notifications || {};
        if (document.getElementById('notif-messages')) document.getElementById('notif-messages').checked = notifications.messages ?? true;
        if (document.getElementById('notif-matches')) document.getElementById('notif-matches').checked = notifications.matches ?? true;
        if (document.getElementById('notif-circles')) document.getElementById('notif-circles').checked = notifications.circles ?? true;
        if (document.getElementById('notif-challenges')) document.getElementById('notif-challenges').checked = notifications.challenges ?? false;
        if (document.getElementById('notif-badges')) document.getElementById('notif-badges').checked = notifications.badges ?? true;

        const privacy = profile.privacy || {};
        if (document.getElementById('privacy-age')) document.getElementById('privacy-age').checked = privacy.show_age ?? true;
        if (document.getElementById('privacy-location')) document.getElementById('privacy-location').checked = privacy.show_location ?? true;
        if (document.getElementById('privacy-badges')) document.getElementById('privacy-badges').checked = privacy.show_badges ?? false;
        if (document.getElementById('privacy-direct')) document.getElementById('privacy-direct').checked = privacy.allow_direct ?? true;

        const verifiedBadge = document.getElementById('verification-badge');
        const verificationTitle = document.getElementById('verification-title');
        const verificationDesc = document.getElementById('verification-desc');
        const verified = ['email', 'phone', 'singpass', 'nric'].indexOf(profile.verified_with) !== -1;
        if (verifiedBadge) verifiedBadge.style.display = verified ? '' : 'none';
        if (verificationTitle) verificationTitle.textContent = verified ? 'Contact Verified' : 'Not Verified Yet';
        if (verificationDesc) {
          if (profile.verified_with === 'email') {
            verificationDesc.textContent = 'Your email address has been verified.';
          } else if (profile.verified_with === 'phone') {
            verificationDesc.textContent = 'Your phone number has been verified.';
          } else if (verified) {
            verificationDesc.textContent = `Your account is verified via ${String(profile.verified_with || '').toUpperCase()}.`;
          } else {
            verificationDesc.textContent = 'Verify your email or phone number to protect your account.';
          }
        }
      }
    })
    .catch(error => {
      console.error('Error loading profile:', error);
    });
}

function updateBio(bio) {
  fetch('/api/profile', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ bio: bio }),
  })
  .then(response => response.json())
  .then(data => {
    if (data.ok) {
      // Reload profile to update display
      loadProfile();
      // Restore UI
      const textarea = document.querySelector('.bio-edit-textarea');
      const buttonContainer = textarea ? textarea.nextSibling : null;
      if (textarea) textarea.remove();
      if (buttonContainer && buttonContainer.tagName === 'DIV') buttonContainer.remove();
      document.getElementById('bio-text').style.display = '';
      document.getElementById('edit-bio-btn').style.display = '';
    } else {
      uiAlert('Failed to update bio', 'Save Failed');
    }
  })
  .catch(error => {
    console.error('Error updating bio:', error);
    uiAlert('Error updating bio', 'Save Failed');
  });
}

async function saveProfile(payload) {
  try {
    const res = await fetch('/api/profile', {
      method: 'POST',
      headers: demoHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      uiAlert(data.error || 'Could not save changes.', 'Save Failed');
      return;
    }
    loadProfile();
  } catch (err) {
    uiAlert('Could not save changes.', 'Save Failed');
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text ?? '';
  return div.innerHTML;
}

