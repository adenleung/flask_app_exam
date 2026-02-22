document.addEventListener("DOMContentLoaded", function () {
  const postForm = document.getElementById("forum-post-form");
  const postsGrid = document.querySelector(".wisdom-grid");

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

  function buildPostCard(post) {
    const card = document.createElement("div");
    card.className = "wisdom-card";
    card.setAttribute("data-post-id", post.id);
    card.style.cssText = "background: white; border: 2px solid #e5e7eb; border-radius: 1.25rem; padding: 1.5rem; display: flex; flex-direction: column; height: 100%;";

    const controls = post.can_edit ? `
      <div class="wisdom-controls" style="margin: 12px 0 18px; border-top: 1px dashed #cbd5e1; padding-top: 12px; display: flex; gap: 12px; justify-content: center;">
        <button type="button" class="forum-delete-btn" data-post-id="${escapeHtml(post.id)}"
          style="background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; padding: 4px 12px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 600; min-width: 96px;">
          🗑️ Delete
        </button>
        <button type="button" class="forum-edit-btn" data-post-id="${escapeHtml(post.id)}" data-post-content="${escapeHtml(post.content)}"
          style="background: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; padding: 4px 12px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 600; min-width: 96px;">
          ✏️ Edit
        </button>
      </div>
    ` : "";

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
        <span style="font-size: 1.5rem;">💡</span>
        <span style="background: #eff6ff; color: #1d4ed8; padding: 4px 12px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; border: 1px solid #dbeafe;">
          ${escapeHtml(post.category)}
        </span>
      </div>
      <h3 style="font-size: 1.25rem; margin-bottom: 0.25rem; color: #1e293b;">${escapeHtml(post.title)}</h3>
      <p style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.75rem;">✍️ By: <strong>${escapeHtml(post.author)}</strong></p>
      <p class="forum-post-content" style="color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem; line-height: 1.5; flex-grow: 1;">
        ${escapeHtml(post.content.slice(0, 100))}${post.content.length > 100 ? "..." : ""}
      </p>
      <div style="margin-top: auto;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #f1f5f9; padding-top: 1rem; margin-bottom: 1rem;">
          <div style="display: flex; gap: 1rem; align-items: center;">
            <form action="/forum/posts/${escapeHtml(post.id)}/like#tab-wisdom-forum" method="post" class="like-form" data-post-id="${escapeHtml(post.id)}" style="display: inline;">
              <button type="submit" style="background: #fff1f2; border: 1px solid #fecdd3; color: #e11d48; padding: 4px 10px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; display: flex; align-items: center; gap: 4px;">
                ❤️ <span class="like-count" data-like-count="${escapeHtml(post.id)}">${escapeHtml(post.likes)}</span>
              </button>
            </form>
            <span style="color: #94a3b8; font-size: 0.85rem;">💬 ${escapeHtml(post.comment_count)}</span>
          </div>
          <span style="color: #94a3b8; font-size: 0.75rem;">${escapeHtml(post.created_at)}</span>
        </div>
        ${controls}
        <a href="/forum/posts/${escapeHtml(post.id)}" style="display: inline-block; width: 100%; padding: 0.75rem; text-align: center; background: var(--orange); color: white; border-radius: 0.75rem; font-weight: 600; text-decoration: none;">
          View & Comment
        </a>
      </div>
    `;

    return card;
  }

  async function handleLikeSubmit(form) {
    const postId = form.getAttribute("data-post-id");
    if (!postId) return;
    try {
      const res = await fetch(`/api/forum/posts/${encodeURIComponent(postId)}/like`, { method: "POST" });
      const out = await res.json().catch(() => null);
      if (!res.ok || !out || !out.ok) {
        return alert((out && out.error) || "Could not like post.");
      }
      const countEl = document.querySelector(`[data-like-count="${postId}"]`);
      if (countEl) countEl.textContent = String(out.likes ?? 0);
    } catch (e) {
      alert("Could not like post.");
    }
  }

  document.addEventListener("submit", function (e) {
    const form = e.target.closest(".like-form");
    if (!form) return;
    e.preventDefault();
    handleLikeSubmit(form);
  });

  document.addEventListener("click", function (e) {
    const editBtn = e.target.closest(".forum-edit-btn");
    if (editBtn) {
      const postId = editBtn.getAttribute("data-post-id");
      const current = editBtn.getAttribute("data-post-content") || "";
      openModal({
        title: "Edit your post",
        bodyHtml: `<textarea class="ui-textarea" id="forum-edit-textarea" style="width:100%; min-height:120px;">${escapeHtml(current)}</textarea>`,
        actionsHtml: `
          <button class="ui-btn" id="forum-edit-cancel">Cancel</button>
          <button class="ui-btn" id="forum-edit-save">Save</button>
        `,
      });
      const cancel = document.getElementById("forum-edit-cancel");
      const save = document.getElementById("forum-edit-save");
      if (cancel) cancel.addEventListener("click", closeModal);
      if (save) {
        save.addEventListener("click", async () => {
          const textarea = document.getElementById("forum-edit-textarea");
          const next = (textarea && textarea.value ? textarea.value : "").trim();
          if (!next) return alert("Content is required.");
          try {
            const res = await fetch(`/api/forum/posts/${encodeURIComponent(postId)}`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ content: next }),
            });
            const out = await res.json().catch(() => null);
            if (!res.ok || !out || !out.ok) return alert((out && out.error) || "Update failed.");
            const card = document.querySelector(`.wisdom-card[data-post-id="${postId}"]`);
            if (card) {
              const contentEl = card.querySelector(".forum-post-content");
              if (contentEl) contentEl.textContent = next.length > 100 ? (next.slice(0, 100) + "...") : next;
              editBtn.setAttribute("data-post-content", next);
            }
            closeModal();
          } catch (err) {
            alert("Update failed.");
          }
        });
      }
    }

    const deleteBtn = e.target.closest(".forum-delete-btn");
    if (deleteBtn) {
      const postId = deleteBtn.getAttribute("data-post-id");
      openModal({
        title: "Delete post?",
        bodyHtml: `<div style="color: var(--muted-foreground); font-weight: 700;">This will remove the post permanently.</div>`,
        actionsHtml: `
          <button class="ui-btn" id="forum-delete-cancel">Cancel</button>
          <button class="ui-btn danger" id="forum-delete-confirm">Delete</button>
        `,
      });
      const cancel = document.getElementById("forum-delete-cancel");
      const confirmBtn = document.getElementById("forum-delete-confirm");
      if (cancel) cancel.addEventListener("click", closeModal);
      if (confirmBtn) {
        confirmBtn.addEventListener("click", async () => {
          try {
            const res = await fetch(`/api/forum/posts/${encodeURIComponent(postId)}`, { method: "DELETE" });
            const out = await res.json().catch(() => null);
            if (!res.ok || !out || !out.ok) return alert((out && out.error) || "Delete failed.");
            const card = document.querySelector(`.wisdom-card[data-post-id="${postId}"]`);
            if (card) card.remove();
            closeModal();
          } catch (err) {
            alert("Delete failed.");
          }
        });
      }
    }
  });

  if (postForm) {
    postForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const titleInput = postForm.querySelector('input[name="title"]');
      const catSelect = postForm.querySelector('select[name="category"]');
      const contentInput = postForm.querySelector('textarea[name="content"]');
      const title = (titleInput && titleInput.value ? titleInput.value : "").trim();
      const category = (catSelect && catSelect.value ? catSelect.value : "").trim();
      const content = (contentInput && contentInput.value ? contentInput.value : "").trim();
      if (!title || !category || !content) return alert("Please complete the form.");
      try {
        const res = await fetch("/api/forum/posts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, category, content }),
        });
        const out = await res.json().catch(() => null);
        if (!res.ok || !out || !out.ok) return alert((out && out.error) || "Could not post.");
        if (titleInput) titleInput.value = "";
        if (catSelect) catSelect.value = "";
        if (contentInput) contentInput.value = "";
        if (postsGrid && out.post) {
          const newCard = buildPostCard(out.post);
          postsGrid.prepend(newCard);
        }
      } catch (err) {
        alert("Could not post.");
      }
    });
  }
});
