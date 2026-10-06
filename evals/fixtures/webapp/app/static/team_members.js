// Settings > Team: change a member's role or remove them, without a page reload.
(function () {
  const section = document.getElementById("team-members");
  if (!section) return;

  const teamId = section.dataset.teamId;
  const errorBox = section.querySelector(".error");

  function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
  }

  function clearError() {
    errorBox.hidden = true;
    errorBox.textContent = "";
  }

  async function send(method, memberId, body) {
    const response = await fetch(`/api/teams/${teamId}/members/${memberId}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    if (response.ok) return null;
    const data = await response.json().catch(() => ({}));
    return data.error || "Something went wrong. Try again.";
  }

  section.addEventListener("change", async (event) => {
    const select = event.target.closest(".js-role");
    if (!select) return;
    clearError();
    const row = select.closest("tr");
    const previous = select.dataset.previous || select.defaultValue;
    select.disabled = true;
    const problem = await send("PATCH", row.dataset.memberId, { role: select.value });
    select.disabled = false;
    if (problem) {
      select.value = previous;
      showError(problem);
    } else {
      select.dataset.previous = select.value;
    }
  });

  section.addEventListener("click", async (event) => {
    const button = event.target.closest(".js-remove");
    if (!button) return;
    const row = button.closest("tr");
    if (!window.confirm(`Remove ${row.dataset.memberName} from the team?`)) return;
    clearError();
    button.disabled = true;
    const problem = await send("DELETE", row.dataset.memberId);
    if (problem) {
      button.disabled = false;
      showError(problem);
    } else {
      row.remove();
    }
  });
})();
