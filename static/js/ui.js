/* Progressive enhancements only: no API requests or persisted form content. */
(() => {
  const refresh = () => {
    document.querySelectorAll("[data-character-count]").forEach((counter) => {
      const input = document.getElementById(counter.dataset.characterCount);
      if (!input || input.maxLength < 0) return;
      counter.hidden = false;
      const update = () => { counter.textContent = `${Array.from(input.value).length} de ${input.maxLength} caracteres`; };
      if (!input.dataset.counterBound) {
        input.addEventListener("input", update);
        input.dataset.counterBound = "true";
      }
      update();
    });
    document.querySelectorAll("[data-selection-group]").forEach((group) => {
      const items = [...group.querySelectorAll("[data-select-item]")];
      const all = group.querySelector("[data-select-all]");
      const update = () => {
        const enabled = items.filter((item) => !item.disabled);
        const count = enabled.filter((item) => item.checked).length;
        group.querySelectorAll("[data-selection-count]").forEach((label) => {
          label.hidden = false;
          label.textContent = `${count} ${count === 1 ? "selecionado" : "selecionados"}`;
        });
        group.querySelectorAll("[data-requires-selection]").forEach((button) => { button.disabled = count === 0; });
        if (all) {
          all.checked = enabled.length > 0 && count === enabled.length;
          all.indeterminate = count > 0 && count < enabled.length;
          all.disabled = enabled.length === 0;
          all.closest("[data-select-all-container]").hidden = false;
        }
      };
      if (!group.dataset.selectionBound) {
        items.forEach((item) => item.addEventListener("change", update));
        all?.addEventListener("change", () => {
          items.filter((item) => !item.disabled).forEach((item) => { item.checked = all.checked; });
          update();
        });
        group.dataset.selectionBound = "true";
      }
      update();
    });
  };
  document.querySelectorAll("form[data-submit-lock]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (event.defaultPrevented) return;
      if (form.dataset.submitting) { event.preventDefault(); return; }
      form.dataset.submitting = "true";
      form.setAttribute("aria-busy", "true");
      form.querySelectorAll('button[type="submit"]').forEach((button) => {
        button.dataset.originalHtml = button.innerHTML;
        button.setAttribute("aria-disabled", "true");
        button.textContent = form.dataset.submitLock || "Enviando…";
      });
    });
  });
  window.addEventListener("pageshow", () => {
    document.querySelectorAll("form[data-submitting]").forEach((form) => {
      delete form.dataset.submitting;
      form.removeAttribute("aria-busy");
      form.querySelectorAll("[data-original-html]").forEach((button) => {
        button.innerHTML = button.dataset.originalHtml;
        button.removeAttribute("aria-disabled");
        delete button.dataset.originalHtml;
      });
    });
    refresh();
  });
  refresh();
  document.querySelector("[data-error-summary]")?.focus();
})();
