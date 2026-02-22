document.addEventListener("DOMContentLoaded", function () {
  function demoHeaders(extra) {
    const headers = extra ? { ...extra } : {};
    const demoId = sessionStorage.getItem("demo_user_id");
    if (demoId) headers["X-Demo-User"] = demoId;
    return headers;
  }

  const submitBtn = document.getElementById("weekly-submit-btn");
  const formWrap = document.getElementById("challenge-entry-form");
  const cancelBtn = document.getElementById("challenge-entry-cancel");
  const postBtn = document.getElementById("challenge-entry-post");
  const textInput = document.getElementById("challenge-entry-text");
  const imageInput = document.getElementById("challenge-entry-image");
  const entriesWrap = document.getElementById("weekly-entries");

  const titleEl = document.getElementById("weekly-title");
  const labelEl = document.getElementById("weekly-label");
  const descEl = document.getElementById("weekly-description");
  const rewardEl = document.getElementById("weekly-reward");
  const participantsEl = document.getElementById("weekly-participants");
  const submissionsEl = document.getElementById("weekly-submissions");

  const uiModal = document.getElementById("ui-modal");
  const uiModalTitle = document.getElementById("ui-modal-title");
  const uiModalBody = document.getElementById("ui-modal-body");
  const uiModalActions = document.getElementById("ui-modal-actions");
  const uiModalClose = document.getElementById("ui-modal-close");

  function openModal({ title, bodyHtml, actionsHtml }) {
    if (!uiModal || !uiModalTitle || !uiModalBody || !uiModalActions) return;
    uiModalTitle.textContent = title;
    uiModalBody.innerHTML = bodyHtml;
    uiModalActions.innerHTML = actionsHtml;
    uiModal.classList.add("show");
  }

  function closeModal() {
    if (!uiModal) return;
    uiModal.classList.remove("show");
  }

  function showNotice(message, title) {
    openModal({
      title: title || "Notice",
      bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">${escapeHtml(message || "")}</div>`,
      actionsHtml: `<button class="ui-btn primary" id="challenge-notice-ok">OK</button>`,
    });
    const ok = document.getElementById("challenge-notice-ok");
    if (ok) ok.addEventListener("click", closeModal);
  }

  if (uiModalClose) uiModalClose.addEventListener("click", closeModal);
  if (uiModal) {
    uiModal.addEventListener("click", (e) => {
      if (e.target === uiModal) closeModal();
    });
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
  }

  function showForm(show) {
    if (!formWrap) return;
    formWrap.style.display = show ? "block" : "none";
  }

  async function fetchChallenge() {
    const res = await fetch("/api/challenges/current", { headers: demoHeaders() });
    if (!res.ok) throw new Error("Failed to load challenge");
    return await res.json();
  }

  function renderEntries(entries) {
    if (!entriesWrap) return;
    entriesWrap.innerHTML = "";

    if (!entries || entries.length === 0) {
      entriesWrap.innerHTML = `<div style="padding: 1rem; color: var(--muted-foreground);">No submissions yet. Be the first!</div>`;
      return;
    }

    entries.forEach((entry) => {
      const card = document.createElement("div");
      card.style.cssText = "background: white; border-radius: 1rem; padding: 1.5rem; border: 2px solid var(--border-color);";

      const imgHtml = entry.image_url
        ? `<img src="${escapeHtml(entry.image_url)}" alt="Entry image" style="width: 100%; border-radius: 0.75rem; margin: 0.75rem 0 1rem; border: 1px solid #eee;">`
        : "";

      const commentsHtml = (entry.comments || []).map((c) => `
        <div style="padding: 0.5rem 0; border-top: 1px solid #f1f5f9;">
          <strong>${escapeHtml(c.author_name)}</strong>: ${escapeHtml(c.content)}
        </div>
      `).join("");

      const actionsHtml = `
        <div style="display:flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.75rem;">
          <button type="button" class="btn btn-outline-teal" data-like-entry="${entry.id}">
            ❤️ <span data-like-count="${entry.id}">${escapeHtml(entry.likes || 0)}</span>
          </button>
          ${entry.can_edit ? `
            <button type="button" class="btn btn-outline-teal" data-entry-edit="${entry.id}" data-entry-content="${escapeHtml(entry.content || '')}" data-entry-image="${escapeHtml(entry.image_url || '')}">Edit</button>
            <button type="button" class="btn btn-outline-teal" data-entry-delete="${entry.id}">Delete</button>
          ` : ''}
        </div>
      `;

      card.innerHTML = `
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
          <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(entry.author_name || "User")}" alt="${escapeHtml(entry.author_name)}"
            style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid var(--orange);">
          <div>
            <div style="font-weight: 700;">${escapeHtml(entry.author_name)}</div>
            <div style="font-size: 0.875rem; color: var(--muted-foreground);">${escapeHtml(entry.created_at)}</div>
          </div>
        </div>
        <p style="margin-bottom: 0.5rem; line-height: 1.6;">${escapeHtml(entry.content)}</p>
        ${imgHtml}
        <div class="entry-comments">
          ${commentsHtml}
        </div>
        ${actionsHtml}
        <div style="display:flex; gap: 0.75rem; margin-top: 0.75rem;">
          <input type="text" placeholder="Add a comment..." data-comment-input="${entry.id}" style="flex:1; padding: 0.5rem 0.75rem; border-radius: 0.5rem; border: 1px solid #ddd;">
          <button type="button" class="btn btn-outline-teal" data-comment-btn="${entry.id}">Post</button>
        </div>
      `;

      entriesWrap.appendChild(card);
    });

    entriesWrap.querySelectorAll("[data-comment-btn]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const entryId = btn.getAttribute("data-comment-btn");
        const input = entriesWrap.querySelector(`[data-comment-input="${entryId}"]`);
        const content = (input && input.value ? input.value : "").trim();
        if (!content) return showNotice("Comment cannot be empty.", "Missing Comment");
        try {
          const res = await fetch(`/api/challenges/entries/${entryId}/comments`, {
            method: "POST",
            headers: demoHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({ content }),
          });
          if (!res.ok) throw new Error("Failed");
          if (input) input.value = "";
          await loadChallenge();
        } catch (e) {
          showNotice("Could not post comment.", "Post Failed");
        }
      });
    });

    entriesWrap.querySelectorAll("[data-like-entry]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const entryId = btn.getAttribute("data-like-entry");
        try {
          const res = await fetch(`/api/challenges/entries/${entryId}/like`, {
            method: "POST",
            headers: demoHeaders(),
          });
          const out = await res.json().catch(() => ({}));
          if (!res.ok || !out.ok) return showNotice(out.error || "Could not like entry.", "Like Failed");
          const countEl = entriesWrap.querySelector(`[data-like-count="${entryId}"]`);
          if (countEl) countEl.textContent = String(out.likes ?? 0);
        } catch (e) {
          showNotice("Could not like entry.", "Like Failed");
        }
      });
    });

    entriesWrap.querySelectorAll("[data-entry-edit]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const entryId = btn.getAttribute("data-entry-edit");
        const current = btn.getAttribute("data-entry-content") || "";
        const currentImage = btn.getAttribute("data-entry-image") || "";
        openModal({
          title: "Edit your entry",
          bodyHtml: `
            <textarea class="ui-textarea" id="entry-edit-content" style="width:100%; min-height:110px;">${escapeHtml(current)}</textarea>
            <input type="text" id="entry-edit-image" placeholder="Image URL (optional)" value="${escapeHtml(currentImage)}" style="width:100%; margin-top:0.75rem; padding:0.6rem 0.75rem; border-radius:0.5rem; border:1px solid #ddd;">
          `,
          actionsHtml: `
            <button class="ui-btn" id="entry-edit-cancel">Cancel</button>
            <button class="ui-btn" id="entry-edit-save">Save</button>
          `,
        });
        const cancel = document.getElementById("entry-edit-cancel");
        const save = document.getElementById("entry-edit-save");
        if (cancel) cancel.addEventListener("click", closeModal);
        if (save) {
          save.addEventListener("click", async () => {
            const nextContent = (document.getElementById("entry-edit-content")?.value || "").trim();
            const nextImage = (document.getElementById("entry-edit-image")?.value || "").trim();
            if (!nextContent) return showNotice("Content is required.", "Missing Content");
            try {
              const res = await fetch(`/api/challenges/entries/${entryId}`, {
                method: "PUT",
                headers: demoHeaders({ "Content-Type": "application/json" }),
                body: JSON.stringify({ content: nextContent, image_url: nextImage }),
              });
              const out = await res.json().catch(() => ({}));
              if (!res.ok || !out.ok) return showNotice(out.error || "Update failed.", "Update Failed");
              closeModal();
              await loadChallenge();
            } catch (e) {
              showNotice("Update failed.", "Update Failed");
            }
          });
        }
      });
    });

    entriesWrap.querySelectorAll("[data-entry-delete]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const entryId = btn.getAttribute("data-entry-delete");
        openModal({
          title: "Delete entry?",
          bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">This will remove the entry permanently.</div>`,
          actionsHtml: `
            <button class="ui-btn" id="entry-delete-cancel">Cancel</button>
            <button class="ui-btn danger" id="entry-delete-confirm">Delete</button>
          `,
        });
        const cancel = document.getElementById("entry-delete-cancel");
        const confirmBtn = document.getElementById("entry-delete-confirm");
        if (cancel) cancel.addEventListener("click", closeModal);
        if (confirmBtn) {
          confirmBtn.addEventListener("click", async () => {
            try {
              const res = await fetch(`/api/challenges/entries/${entryId}`, {
                method: "DELETE",
                headers: demoHeaders(),
              });
              const out = await res.json().catch(() => ({}));
              if (!res.ok || !out.ok) return showNotice(out.error || "Delete failed.", "Delete Failed");
              closeModal();
              await loadChallenge();
            } catch (e) {
              showNotice("Delete failed.", "Delete Failed");
            }
          });
        }
      });
    });
  }

  async function loadChallenge() {
    try {
      const data = await fetchChallenge();
      if (data && data.ok && data.challenge) {
        if (titleEl) titleEl.textContent = data.challenge.title;
        if (labelEl) labelEl.textContent = data.challenge.week_label;
        if (descEl) descEl.textContent = data.challenge.description;
        if (rewardEl) rewardEl.textContent = `+${data.challenge.reward_points} Points`;
      }

      const entries = data.entries || [];
      if (participantsEl) participantsEl.textContent = String(entries.length);
      if (submissionsEl) submissionsEl.textContent = String(entries.length);
      renderEntries(entries);
    } catch (e) {
      if (entriesWrap) {
        entriesWrap.innerHTML = `<div style="padding: 1rem; color: var(--muted-foreground);">Unable to load entries.</div>`;
      }
    }
  }

  if (submitBtn) {
    submitBtn.addEventListener("click", () => {
      showForm(true);
      if (textInput) textInput.focus();
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => showForm(false));
  }

  if (postBtn) {
    postBtn.addEventListener("click", async () => {
      const content = (textInput && textInput.value ? textInput.value : "").trim();
      const rawImageUrl = (imageInput && imageInput.value ? imageInput.value : "").trim();
      const image_url = /^https?:\/\/\S+$/i.test(rawImageUrl) ? rawImageUrl : "";
      if (!content) return showNotice("Please share your story before posting.", "Missing Story");
      try {
        const res = await fetch("/api/challenges/entries", {
          method: "POST",
          headers: demoHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ content, image_url }),
        });
        if (!res.ok) throw new Error("Failed");
        if (textInput) textInput.value = "";
        if (imageInput) imageInput.value = "";
        showForm(false);
        window.location.href = "/challenges#submissions";
      } catch (e) {
        showNotice("Could not submit entry.", "Submit Failed");
      }
    });
  }

  loadChallenge();
});
