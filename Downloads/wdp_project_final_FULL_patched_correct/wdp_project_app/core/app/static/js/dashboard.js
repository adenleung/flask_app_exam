// Dashboard JavaScript

// Show main dashboard after welcome screen
window.addEventListener('DOMContentLoaded', function() {
  const welcomeScreen = document.getElementById('welcome-screen');
  const mainDashboard = document.getElementById('main-dashboard');

  function demoHeaders(extra) {
    const headers = extra ? { ...extra } : {};
    const demoId = sessionStorage.getItem('demo_user_id');
    if (demoId) headers['X-Demo-User'] = demoId;
    return headers;
  }

  // Show main dashboard after 2 seconds
  setTimeout(function() {
    mainDashboard.classList.remove('hidden');
  }, 2000);

  // Remove welcome screen from DOM after animation
  setTimeout(function() {
    if (welcomeScreen) {
      welcomeScreen.remove();
    }
  }, 2500);

  const nameEl = document.getElementById('user-name');
  const welcomeTimeEl = document.getElementById('welcome-time');
  const welcomeContext = document.getElementById('welcome-context');
  const welcomeSupport = document.getElementById('welcome-support');

  function timeGreeting(name) {
    const hour = new Date().getHours();
    if (hour < 12) return '🌅 Good Morning, ' + name;
    if (hour < 18) return '☀️ Good Afternoon, ' + name;
    return '🌙 Good Evening, ' + name;
  }

  if (nameEl || welcomeTimeEl) {
    fetch('/api/session', { headers: demoHeaders() })
      .then((res) => res.ok ? res.json() : null)
      .then((data) => {
        let currentName = 'User';
        if (data && data.logged_in && data.name) {
          currentName = data.name;
          if (nameEl) nameEl.textContent = data.name;
        }
        if (welcomeTimeEl) {
          const tg = timeGreeting(currentName);
          welcomeTimeEl.textContent = tg.split(',')[0];
        }

        const navAvatar = document.querySelector('img.nav-avatar');
        if (navAvatar) {
          if (data && data.logged_in && data.avatar_url) {
            navAvatar.src = data.avatar_url;
            navAvatar.dataset.sessionAvatar = '1';
          } else if (data && data.logged_in && data.name) {
            const generated = 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + encodeURIComponent(data.name);
            navAvatar.src = generated;
            navAvatar.dataset.sessionAvatar = '1';
          }
        }
      })
      .catch(() => {});
  }

  const statConnections = document.getElementById('stat-connections');
  const statMemories = document.getElementById('stat-memories');
  const statRepoints = document.getElementById('stat-repoints');
  const statCircles = document.getElementById('stat-circles');
  const statBadges = document.getElementById('stat-badges');
  if (statConnections || statMemories || statRepoints || statCircles || statBadges) {
    fetch('/api/profile', { headers: demoHeaders() })
      .then((res) => res.ok ? res.json() : null)
      .then((data) => {
        if (!data || !data.ok || !data.profile) return;
        const profile = data.profile;
        if (statConnections) statConnections.textContent = profile.connections_count ?? statConnections.textContent;
        if (statMemories) statMemories.textContent = profile.memories_count ?? statMemories.textContent;
        if (statRepoints) statRepoints.textContent = profile.repoints ?? statRepoints.textContent;
        if (statCircles) statCircles.textContent = profile.circles_count ?? statCircles.textContent;
        if (statBadges) statBadges.textContent = profile.badges_count ?? statBadges.textContent;
      })
      .catch(() => {});
  }

  const wellbeingWidget = document.getElementById('wellbeing-widget');
  if (wellbeingWidget) {
    const moodButtons = wellbeingWidget.querySelectorAll('.mood-btn');
    const summary = document.getElementById('wellbeing-summary');
    const recosWrap = document.getElementById('wellbeing-recos');
    const currentEl = document.getElementById('wellbeing-current');
    const updatedEl = document.getElementById('wellbeing-last-updated');
    const trendEl = document.getElementById('wellbeing-trend');
    const weeklyMicroEl = document.getElementById('wellbeing-social');
    const nudgeEl = document.getElementById('wellbeing-nudge');
    const riskEl = document.getElementById('wellbeing-risk');
    let selectedMood = '';

    function moodLabel(mood) {
      const map = {
        happy: '😊 Feeling Happy Today',
        good: '🙂 Feeling Good',
        neutral: '😐 Feeling Neutral',
        stressed: '😟 Feeling Stressed',
        sad: '😞 Feeling Low'
      };
      return map[mood] || '😐 Feeling Neutral';
    }

    function renderSummary(checkin, insight) {
      if (!summary) return;
      if (!checkin) {
        summary.style.display = 'none';
        return;
      }
      summary.textContent = (insight || '').trim();
      summary.style.display = '';
    }

    function renderWelcomeContext(data) {
      if (!welcomeContext) return;
      const checkin = data && data.latest_checkin ? data.latest_checkin : null;
      const mood = checkin && checkin.mood ? checkin.mood : 'neutral';
      const activity = data && data.activity ? data.activity : { circles: 0, messages: 0, challenges: 0 };
      const risk = data && data.risk ? data.risk : null;
      let line = 'Ready to connect and learn today?';
      let supportLine = 'We are glad you are here.';
      if (risk && risk.show) {
        line = 'We are here to support you and take things at your pace.';
        supportLine = 'A gentle step today is enough.';
      } else if (mood === 'happy' || mood === 'good') {
        line = 'Great to see you feeling positive today.';
        supportLine = 'Your positive energy can brighten someone’s day.';
      } else if (mood === 'stressed' || mood === 'sad') {
        line = 'You are not alone today.';
        supportLine = 'Take one calm step and we will support you.';
      } else if ((activity.circles || 0) === 0 && (activity.messages || 0) === 0) {
        line = 'It has been a while. Let’s reconnect gently.';
        supportLine = 'A short hello can make a meaningful difference.';
      }
      welcomeContext.textContent = line;
      if (welcomeSupport) welcomeSupport.textContent = supportLine;
    }

    function renderRecos(recos) {
      if (!recosWrap) return;
      if (!recos || !recos.length) {
        recosWrap.style.display = 'none';
        return;
      }
      const iconMap = {
        circle: '📚',
        forum: '🧠',
        challenge: '🎯',
        match: '🤝'
      };
      recosWrap.innerHTML = recos.map(r => (
        '<a class="support-action" href="' + (r.link || '#') + '">' +
          '<span class="icon">' + (iconMap[r.type] || '💬') + '</span>' +
          '<span>' + r.title + '</span>' +
        '</a>'
      )).join('');
      recosWrap.style.display = '';
    }

    function setCheckedIn(checkin, insight, recos) {
      moodButtons.forEach(btn => btn.classList.remove('active'));
      if (checkin && checkin.mood) {
        moodButtons.forEach(btn => {
          if ((btn.dataset.mood || '') === checkin.mood) btn.classList.add('active');
        });
      }
      renderSummary(checkin, insight);
      renderRecos(recos);
    }

    function loadSummary() {
      fetch('/api/wellbeing/dashboard', { headers: demoHeaders() })
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (!data || !data.ok) return;
          const checkin = data.latest_checkin || null;
          if (currentEl && checkin) currentEl.textContent = moodLabel(checkin.mood);
          if (updatedEl) updatedEl.textContent = 'Last check-in: ' + (data.last_updated_human || 'No check-ins yet');
          if (trendEl && data.trend) trendEl.innerHTML = '<span>' + (data.trend.arrow || '➡') + '</span><span>' + (data.trend.label || 'Stable') + '</span>';
          if (weeklyMicroEl && data.activity) {
            weeklyMicroEl.textContent = 'This week: ' +
              String(data.activity.circles || 0) + ' circles • ' +
              String(data.activity.messages || 0) + ' messages • ' +
              String(data.activity.challenges || 0) + ' challenges';
          }
          if (nudgeEl) nudgeEl.textContent = data.nudge || 'You have been quiet this week - reconnect when you feel ready.';
          renderWelcomeContext(data);
          if (riskEl) {
            if (data.risk && data.risk.show) {
              riskEl.style.display = '';
              riskEl.textContent = '⚠ ' + (data.risk.message || 'We are here for you — explore support circles.');
            } else {
              riskEl.style.display = 'none';
              riskEl.textContent = '';
            }
          }
          const trendSentence = 'Trend: ' + ((data.trend && data.trend.label) || 'Stable') + ' this week.';
          if (checkin) {
            setCheckedIn(checkin, trendSentence, data.recommendations || []);
          } else {
            renderSummary({ mood: 'neutral' }, trendSentence);
            renderRecos(data.recommendations || []);
          }
        })
        .catch(() => {});
    }

    moodButtons.forEach(btn => {
      btn.addEventListener('click', async () => {
        selectedMood = btn.dataset.mood || '';
        if (!selectedMood) return;
        moodButtons.forEach(b => { b.disabled = true; });
        const payload = {
          mood: selectedMood
        };
        const res = await fetch('/api/wellbeing/checkin', {
          method: 'POST',
          headers: demoHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify(payload)
        });
        const out = await res.json().catch(() => ({}));
        if (!res.ok) {
          moodButtons.forEach(b => { b.disabled = false; });
          alert(out.error || 'Could not save check-in.');
          return;
        }
        setCheckedIn({ mood: selectedMood }, out.insight || '', out.recommendations || []);
        moodButtons.forEach(b => { b.disabled = false; });
        loadSummary();
      });
    });

    loadSummary();
  }
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});
