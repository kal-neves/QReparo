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
  document.querySelectorAll('[data-tag-selector]').forEach((group) => {
    const inputs = [...group.querySelectorAll('input[type="checkbox"]')];
    const status = group.querySelector('[data-tag-status]');
    const min = Number(group.dataset.min), max = Number(group.dataset.max);
    const update = (event) => {
      let count = inputs.filter(input => input.checked).length;
      const exceeded = count > max;
      if (exceeded && event?.target.checked) { event.target.checked = false; count--; }
      status.textContent = `${count} de ${max} selecionados.${exceeded ? ` Selecione no máximo ${max} opções.` : ''}`;
      const anchor = inputs.find(input => !input.disabled);
      anchor?.setCustomValidity(count < min ? `Selecione pelo menos ${min} opção.` : count > max ? `Selecione no máximo ${max} opções.` : '');
    };
    group.addEventListener('change', update);
    group.closest('form')?.addEventListener('reset', () => setTimeout(update, 0));
    window.addEventListener('pageshow', () => update());
    update();
  });
  document.querySelectorAll('[data-photo-input]').forEach((group) => {
    const input = group.querySelector('input[type="file"]');
    const preview = group.querySelector('[data-photo-preview]');
    const status = group.querySelector('[data-photo-status]');
    const remove = group.querySelector('[data-photo-remove]');
    if (!input) return;
    let objectUrl;
    const release = () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = null;
      preview.hidden = true;
      preview.removeAttribute('src');
    };
    const update = () => {
      release();
      input.setCustomValidity('');
      const file = input.files[0];
      remove.hidden = !file;
      status.textContent = '';
      if (!file) return;
      if (file.size > Number(group.dataset.maxBytes)) {
        status.textContent = 'O arquivo excede o tamanho permitido.';
        input.setCustomValidity(status.textContent);
        return;
      }
      if (!/\.(png|jpe?g|heic)$/i.test(file.name)) {
        status.textContent = 'Selecione uma foto PNG, JPEG ou HEIC.';
        input.setCustomValidity(status.textContent);
        return;
      }
      status.textContent = `${file.name} — ${(file.size / 1048576).toFixed(1)} MB. Selecionada apenas neste navegador.`;
      if (/\.heic$/i.test(file.name)) {
        status.textContent += ' Prévia HEIC indisponível; o servidor validará a imagem no envio.';
        return;
      }
      objectUrl = URL.createObjectURL(file);
      preview.src = objectUrl;
      preview.hidden = false;
    };
    preview.addEventListener('error', () => {
      release();
      status.textContent = 'Não foi possível exibir a prévia. O servidor deve validar o arquivo no envio.';
    });
    input.addEventListener('change', update);
    remove.addEventListener('click', () => { input.value = ''; update(); input.focus(); });
    input.form?.addEventListener('reset', () => setTimeout(update, 0));
    window.addEventListener('pagehide', release);
    window.addEventListener('pageshow', update);
    update();
  });
  document.querySelector("[data-error-summary]")?.focus();
})();
