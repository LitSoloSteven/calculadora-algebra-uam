/**
 * Scalaris — MatrixCapturePanel Interactions
 */
(function () {
  if (window.__matrix_ops_listeners_active) return;
  window.__matrix_ops_listeners_active = true;

  // Navegación con teclado
  document.addEventListener('keydown', function (e) {
    let active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
    let r = parseInt(active.dataset.matrixRow), c = parseInt(active.dataset.matrixCol);
    let mId = active.dataset.matrixId;
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      if (e.key === 'ArrowLeft' && active.selectionStart !== 0) return;
      if (e.key === 'ArrowRight' && active.selectionEnd !== active.value.length) return;
      if (e.key === 'ArrowRight') c++; if (e.key === 'ArrowLeft') c--;
      if (e.key === 'ArrowDown') r++; if (e.key === 'ArrowUp') r--;
    } else if (e.key === 'Enter') r++;
    else return;

    let next = document.querySelector(`input[data-matrix-id="${mId}"][data-matrix-row="${r}"][data-matrix-col="${c}"]`);
    if (next) { next.focus(); setTimeout(() => next.select(), 10); e.preventDefault(); }
  });

  // Soporte Paste TSV
  document.addEventListener('paste', function (e) {
    let active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
    e.preventDefault();
    let pasteData = (e.clipboardData || window.clipboardData).getData('text');
    let rows = pasteData.trim().split('\n');
    let startR = parseInt(active.dataset.matrixRow), startC = parseInt(active.dataset.matrixCol);
    let mId = active.dataset.matrixId;

    rows.forEach((rowStr, rIdx) => {
      let cols = rowStr.split('\t');
      cols.forEach((val, cIdx) => {
        let input = document.querySelector(`input[data-matrix-id="${mId}"][data-matrix-row="${startR + rIdx}"][data-matrix-col="${startC + cIdx}"]`);
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
    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
    let r = active.dataset.matrixRow;
    let c = active.dataset.matrixCol;
    let mId = active.dataset.matrixId;

    document.querySelectorAll(`input[data-matrix-id="${mId}"]`).forEach(inp => {
      let isSame = (inp.dataset.matrixRow === r || inp.dataset.matrixCol === c);
      let control = inp.closest('.q-field__control');
      if (control && isSame) {
        control.style.background = 'color-mix(in srgb, var(--accent) 15%, var(--input-bg))';
      }
    });
  });

  document.addEventListener('focusout', function (e) {
    let active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
    let mId = active.dataset.matrixId;

    document.querySelectorAll(`input[data-matrix-id="${mId}"]`).forEach(inp => {
      let control = inp.closest('.q-field__control');
      if (control) control.style.background = '';
    });
  });
})();
