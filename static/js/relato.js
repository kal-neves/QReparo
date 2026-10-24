/* validação visual sem armazenar o relato */
(() => {
  const section = document.querySelector('[data-report-fields]');
  if (!section) return;
  const problem = section.querySelector('select');
  const description = section.querySelector('textarea');
  const label = section.querySelector(`label[for="${description.id}"] span`);
  const update = () => {
    const required = problem.value === (problem.dataset.outroId || 'outro');
    description.required = required;
    label.textContent = required ? '(obrigatória)' : '(opcional)';
    label.className = required ? 'qr-required' : 'qr-muted';
  };
  problem.addEventListener('change', update);
  update();
})();
