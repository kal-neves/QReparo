(() => {
  const action = document.getElementById('imprimir-etiqueta');
  if (!action) return;
  action.hidden = false;
  action.querySelector('button').addEventListener('click', () => window.print());
})();
