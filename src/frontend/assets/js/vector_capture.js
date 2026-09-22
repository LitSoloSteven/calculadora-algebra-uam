/**
 * Scalaris — VectorCapturePanel Interactions and Animations
 */
(function () {
  if (window.__vector_listeners_active) return;
  window.__vector_listeners_active = true;

  // Navegación con teclado
  document.addEventListener('keydown', function (e) {
    let active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;

    let idx = parseInt(active.dataset.vecIdx);
    let vId = active.dataset.vecId;
    let orientation = active.dataset.vecOrientation;

    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      if (e.key === 'ArrowLeft' && active.selectionStart !== 0) return;
      if (e.key === 'ArrowRight' && active.selectionEnd !== active.value.length) return;

      if (orientation === 'column') {
        if (e.key === 'ArrowDown') idx++;
        if (e.key === 'ArrowUp') idx--;
      } else {
        if (e.key === 'ArrowRight') idx++;
        if (e.key === 'ArrowLeft') idx--;
      }
    } else if (e.key === 'Enter') idx++;
    else return;

    let next = document.querySelector(`input[data-vec-id="${vId}"][data-vec-idx="${idx}"]`);
    if (next) { next.focus(); setTimeout(() => next.select(), 10); e.preventDefault(); }
  });

  // Soporte Paste TSV/CSV simple
  document.addEventListener('paste', function (e) {
    let active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
    e.preventDefault();
    let pasteData = (e.clipboardData || window.clipboardData).getData('text');

    let vals = pasteData.trim().split(/[\n\t,;]+/);
    let startIdx = parseInt(active.dataset.vecIdx);
    let vId = active.dataset.vecId;

    vals.forEach((val, i) => {
      let input = document.querySelector(`input[data-vec-id="${vId}"][data-vec-idx="${startIdx + i}"]`);
      if (input) {
        input.value = val.trim();
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  });

  // Cross-highlighting de celdas
  document.addEventListener('focusin', function (e) {
    let active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
    let idx = active.dataset.vecIdx;
    let vId = active.dataset.vecId;

    document.querySelectorAll(`input[data-vec-id="${vId}"]`).forEach(inp => {
      let isSame = (inp.dataset.vecIdx === idx);
      let control = inp.closest('.q-field__control');
      if (control && isSame) {
        control.style.background = 'color-mix(in srgb, var(--accent) 15%, var(--input-bg))';
      }
    });
  });

  document.addEventListener('focusout', function (e) {
    let active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
    let vId = active.dataset.vecId;

    document.querySelectorAll(`input[data-vec-id="${vId}"]`).forEach(inp => {
      let control = inp.closest('.q-field__control');
      if (control) control.style.background = '';
    });
  });
})();

window.animateVectorDimensionRemoval = function (idxRemove) {
  return new Promise(resolve => {
    let cells = document.querySelectorAll(`input[data-vec-idx='${idxRemove}']`);
    const anims = [];
    cells.forEach(input => {
      let control = input.closest('.q-field__control');
      if (control) {
        anims.push(control.animate(
          [{ opacity: 1, transform: 'scale(1)', filter: 'blur(0)' },
          { opacity: 0, transform: 'scale(0.85) translateY(-8px)', filter: 'blur(2px)' }],
          { duration: 240, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards' }
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

window.animateVectorDimensionAddition = function (idxAdd) {
  return new Promise(resolve => {
    let cells = document.querySelectorAll(`input[data-vec-idx='${idxAdd}']`);
    const anims = [];
    cells.forEach(input => {
      let control = input.closest('.q-field__control');
      if (control) {
        anims.push(control.animate(
          [{ opacity: 0, transform: 'scale(0.85) translateY(8px)', filter: 'blur(2px)' },
          { opacity: 1, transform: 'scale(1)', filter: 'blur(0)' }],
          { duration: 240, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards' }
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
