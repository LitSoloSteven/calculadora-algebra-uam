/**
 * Scalaris — EquationGrid Interactions and Animations
 */
(function () {
  if (window.__matrix_listeners_active) return;
  window.__matrix_listeners_active = true;

  // Navegación con teclado
  document.addEventListener('keydown', function (e) {
    let active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
    let r = parseInt(active.dataset.row), c = parseInt(active.dataset.col);
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      if (e.key === 'ArrowLeft' && active.selectionStart !== 0) return;
      if (e.key === 'ArrowRight' && active.selectionEnd !== active.value.length) return;
      if (e.key === 'ArrowRight') c++; if (e.key === 'ArrowLeft') c--;
      if (e.key === 'ArrowDown') r++; if (e.key === 'ArrowUp') r--;
    } else if (e.key === 'Enter') r++;
    else return;

    let next = document.querySelector(`input[data-row="${r}"][data-col="${c}"]`);
    if (next) { next.focus(); setTimeout(() => next.select(), 10); e.preventDefault(); }
  });

  // Soporte Paste TSV (Excel/Portapapeles)
  document.addEventListener('paste', function (e) {
    let active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
    e.preventDefault();
    let pasteData = (e.clipboardData || window.clipboardData).getData('text');
    let rows = pasteData.replace(/\s+$/, '').split('\n');
    let startR = parseInt(active.dataset.row), startC = parseInt(active.dataset.col);

    rows.forEach((rowStr, rIdx) => {
      let cols = rowStr.split('\t');
      cols.forEach((val, cIdx) => {
        let input = document.querySelector(`input[data-row="${startR + rIdx}"][data-col="${startC + cIdx}"]`);
        if (input) {
          input.value = val.trim();
          input.dispatchEvent(new Event('input', { bubbles: true }));
        }
      });
    });
  });

  // Cross-highlighting de celdas
  document.addEventListener('focusin', function (e) {
    let active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
    let r = active.dataset.row;
    let c = active.dataset.col;

    let container = active.closest('.panel-card');
    if (!container) return;

    container.querySelectorAll('input[data-row]').forEach(inp => {
      let isSame = (inp.dataset.row === r || inp.dataset.col === c);
      let control = inp.closest('.q-field__control');
      if (control && isSame) {
        control.style.background = 'color-mix(in srgb, var(--accent) 15%, var(--input-bg))';
      }
    });
  });

  document.addEventListener('focusout', function (e) {
    let active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;

    let container = active.closest('.panel-card');
    if (!container) return;

    container.querySelectorAll('input[data-row]').forEach(inp => {
      let control = inp.closest('.q-field__control');
      if (control) control.style.background = '';
    });
  });
})();

window.animateGridCellRemoval = function (target, isM, idxRow) {
  return new Promise(resolve => {
    let cells = document.querySelectorAll(`input${target}`);
    const anims = [];
    cells.forEach((input, i) => {
      let ctrl = input.closest('.q-field__control');
      if (ctrl) {
        anims.push(ctrl.animate(
          [{ opacity: 1, transform: 'scale(1)', filter: 'blur(0)' },
          { opacity: 0, transform: 'scale(0.85) translateY(-8px)', filter: 'blur(2px)' }],
          { duration: 240, delay: i * 25, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards' }
        ).finished);
      }
    });
    if (isM) {
      let rowContainer = document.querySelector(`[data-grid-row="${idxRow}"]`);
      if (rowContainer) {
        rowContainer.style.overflow = 'hidden';
        anims.push(rowContainer.animate(
          [{ height: rowContainer.offsetHeight + 'px', opacity: 1, marginTop: '0px', marginBottom: '8px' },
          { height: '0px', opacity: 0, marginTop: '0px', marginBottom: '0px' }],
          { duration: 240, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards' }
        ).finished);
      }
    }
    Promise.all(anims).then(resolve);
  });
};

window.animateGridCellAddition = function (target) {
  return new Promise(resolve => {
    let cells = document.querySelectorAll(`input${target}`);
    const anims = [];
    cells.forEach((input, i) => {
      let ctrl = input.closest('.q-field__control');
      if (ctrl) {
        anims.push(ctrl.animate(
          [{ opacity: 0, transform: 'scale(0.85) translateY(8px)', filter: 'blur(2px)' },
          { opacity: 1, transform: 'scale(1)', filter: 'blur(0)' }],
          { duration: 240, delay: i * 25, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards' }
        ).finished);
      }
    });
    if (anims.length > 0) {
      Promise.all(anims).then(resolve);
    } else {
      resolve();
    }
  });
};
