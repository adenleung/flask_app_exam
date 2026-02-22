document.addEventListener("DOMContentLoaded", function () {
  const notifBtn = document.getElementById("notif-btn");
  const dropdown = document.getElementById("notifications-dropdown");
  const badge = document.querySelector(".notification-badge");
  const markReadBtn = document.querySelector(".mark-read-btn");
  const listEl = document.getElementById("notifications-list");

  function demoHeaders(extra) {
    const headers = extra ? { ...extra } : {};
    const demoId = sessionStorage.getItem("demo_user_id");
    if (demoId) headers["X-Demo-User"] = demoId;
    return headers;
  }

  function updateBadge(count) {
    if (!badge) return;
    const unread = Number.isFinite(count) ? count : 0;
    badge.textContent = String(unread);
    badge.style.display = unread > 0 ? "inline-flex" : "none";
  }

  function toggleDropdown() {
    if (!dropdown) return;
    dropdown.classList.toggle("show");
    if (dropdown.classList.contains("show")) {
      requestAnimationFrame(positionDropdown);
    }
  }

  function positionDropdown() {
    if (!dropdown || !notifBtn) return;
    const rect = notifBtn.getBoundingClientRect();
    const width = dropdown.offsetWidth || 320;
    const margin = 8;
    let left = rect.left + rect.width / 2 - width / 2;
    if (left < margin) left = margin;
    let top = rect.bottom + margin;
    dropdown.style.top = `${top}px`;
    dropdown.style.left = `${left}px`;
    dropdown.style.right = "auto";
  }

  async function apiListNotifications() {
    const res = await fetch("/api/notifications", { headers: demoHeaders() });
    if (!res.ok) return { notifications: [], unread_count: 0 };
    return await res.json();
  }

  async function apiMarkRead() {
    const res = await fetch("/api/notifications/mark_read", {
      method: "POST",
      headers: demoHeaders(),
    });
    if (!res.ok) return false;
    return true;
  }

  async function apiRespondRequest(requestId, action) {
    const res = await fetch(`/api/match_requests/${requestId}/respond`, {
      method: "POST",
      headers: demoHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ action }),
    });
    if (!res.ok) return false;
    return true;
  }

  function renderNotifications(items) {
    if (!listEl) return;
    listEl.innerHTML = "";

    if (!items || items.length === 0) {
      listEl.innerHTML = `
        <div style="padding: 1rem; color: var(--muted-foreground); font-size: 0.95rem;">
          No notifications yet.
        </div>
      `;
      return;
    }

    items.forEach((n) => {
      const item = document.createElement("div");
      item.className = "notification-item";
      if (n.unread) item.classList.add("unread");

      if (n.type === "match_request") {
        item.innerHTML = `
          <div class="notif-icon teal">&#x1F91D;</div>
          <div class="notif-content">
            <p><strong>${n.sender_name}</strong> sent a match request</p>
            <span class="notif-time">${n.sender_location || "Nearby"} &#x2022; Pending</span>
            <div class="notif-actions">
              <button class="notif-action-btn accept" data-action="accept" data-id="${n.request_id}">Accept</button>
              <button class="notif-action-btn decline" data-action="decline" data-id="${n.request_id}">Decline</button>
            </div>
          </div>
        `;
      } else if (n.type === "match_decision") {
        const status = n.status === "accepted" ? "accepted" : "declined";
        item.innerHTML = `
          <div class="notif-icon ${status === "accepted" ? "success" : "orange"}">&#x1F514;</div>
          <div class="notif-content">
            <p>Your request to <strong>${n.receiver_name}</strong> was ${status}.</p>
            <span class="notif-time">Just now</span>
          </div>
        `;
      } else {
        item.innerHTML = `
          <div class="notif-icon orange">&#x1F514;</div>
          <div class="notif-content">
            <p>${n.message || "New notification"}</p>
            <span class="notif-time">Just now</span>
          </div>
        `;
      }

      listEl.appendChild(item);
    });

    listEl.querySelectorAll(".notif-action-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-id");
        const action = btn.getAttribute("data-action");
        if (!id || !action) return;
        const ok = await apiRespondRequest(id, action);
        if (!ok) {
          alert("Could not update request.");
          return;
        }
        await refreshNotifications();
      });
    });
  }

  async function refreshNotifications() {
    const out = await apiListNotifications();
    renderNotifications(out.notifications || []);
    updateBadge(out.unread_count || 0);
  }

  if (notifBtn && dropdown) {
    notifBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      toggleDropdown();
      refreshNotifications();
    });

    document.addEventListener("click", function (e) {
      if (!dropdown.contains(e.target) && e.target !== notifBtn) {
        dropdown.classList.remove("show");
      }
    });
  }

  if (markReadBtn && dropdown) {
    markReadBtn.addEventListener("click", async function () {
      await apiMarkRead();
      await refreshNotifications();
    });
  }

  refreshNotifications();
  setInterval(refreshNotifications, 5000);

  window.addEventListener("resize", () => {
    if (dropdown && dropdown.classList.contains("show")) positionDropdown();
  });
  window.addEventListener("scroll", () => {
    if (dropdown && dropdown.classList.contains("show")) positionDropdown();
  });
});
