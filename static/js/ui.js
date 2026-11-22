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
    input.setAttribute('aria-describedby', [input.getAttribute('aria-describedby'), status.id].filter(Boolean).join(' '));
    let objectUrl;
    const camera = group.querySelector('[data-photo-camera]');
    if (camera) {
      camera.hidden = false;
      camera.addEventListener('click', () => { input.setAttribute('capture', 'environment'); input.click(); });
      input.addEventListener('pointerdown', () => input.removeAttribute('capture'));
      input.addEventListener('keydown', () => input.removeAttribute('capture'));
    }
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
      status.textContent = `${file.name} — ${(file.size / 1000000).toFixed(1)} MB. Selecionada apenas neste navegador.`;
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
  document.querySelectorAll('[data-private-photo]').forEach((img) => {
    const unavailable = () => {
      img.hidden = true;
      const message = img.parentElement.querySelector('[data-photo-unavailable]');
      if (message) message.hidden = false;
    };
    img.addEventListener('error', unavailable);
    if (img.complete && img.naturalWidth === 0) unavailable();
  });
  const photoLinks = document.querySelectorAll('[data-photo-lightbox]');
  if (photoLinks.length && typeof HTMLDialogElement !== 'undefined' && HTMLDialogElement.prototype.showModal) {
    const dialog = document.createElement('dialog');
    dialog.className = 'qr-photo-lightbox';
    dialog.setAttribute('aria-label', 'Visualização da foto');
    const header = document.createElement('div');
    header.className = 'qr-photo-lightbox-header';
    const title = document.createElement('h2');
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'btn btn-outline-primary';
    close.textContent = 'Fechar';
    close.autofocus = true;
    const image = document.createElement('img');
    image.className = 'qr-photo-lightbox-image';
    const status = document.createElement('p');
    status.setAttribute('role', 'status');
    header.append(title, close);
    dialog.append(header, image, status);
    document.body.append(dialog);
    let opener;
    photoLinks.forEach(link => {
      link.setAttribute('aria-haspopup', 'dialog');
      link.addEventListener('click', event => {
        if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        opener = link;
        title.textContent = link.dataset.photoLabel || 'Foto do relato';
        image.alt = title.textContent;
        image.hidden = true;
        status.textContent = 'Carregando foto…';
        status.hidden = false;
        dialog.showModal();
        document.body.classList.add('qr-lightbox-open');
        image.src = link.dataset.photoLightbox;
      });
    });
    image.addEventListener('load', () => { image.hidden = false; status.hidden = true; });
    image.addEventListener('error', () => {
      image.hidden = true;
      status.textContent = 'Foto indisponível. Feche e atualize os relatos para conferir.';
      status.hidden = false;
    });
    close.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      const bounds = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right ||
          event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
    });
    dialog.addEventListener('close', () => {
      image.removeAttribute('src');
      document.body.classList.remove('qr-lightbox-open');
      opener?.focus();
    });
  }
  document.querySelector("[data-error-summary]")?.focus();
})();
