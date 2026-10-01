/** Scalaris — SquareMatrixPanel: animaciones de redimensionado y utilidades de la vista Matriz Inversa */
window.animateSquareResize = function (matrixId, idx, mode) {
  return new Promise(resolve => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { resolve(); return; }
    const sel = `input[data-matrix-id="${matrixId}"][data-matrix-row="${idx}"], input[data-matrix-id="${matrixId}"][data-matrix-col="${idx}"]`;
    const frames = mode === 'remove'
      ? [{ opacity: 1, transform: 'scale(1)', filter: 'blur(0)' }, { opacity: 0, transform: 'scale(0.85) translateY(-8px)', filter: 'blur(2px)' }]
      : [{ opacity: 0, transform: 'scale(0.85) translateY(8px)', filter: 'blur(2px)' }, { opacity: 1, transform: 'scale(1)', filter: 'blur(0)' }];
    const inputs = document.querySelectorAll(sel);
    const step = Math.min(25, 300 / Math.max(inputs.length, 1)); // tope: el stagger total nunca supera ~300 ms
    const anims = [];
    inputs.forEach((input, i) => {
      const ctrl = input.closest('.q-field__control');
      if (ctrl) anims.push(ctrl.animate(frames, { duration: 240, delay: i * step, easing: 'cubic-bezier(0.32,0.72,0,1)', fill: 'forwards' }).finished);
    });
    Promise.all(anims).then(resolve).catch(resolve);
  });
};

window.flashStepCard = function (elId) {
  const el = document.getElementById(elId);
  if (!el || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  el.animate([{ opacity: 0.55, transform: 'translateY(6px)' }, { opacity: 1, transform: 'translateY(0)' }],
             { duration: 180, easing: 'cubic-bezier(0.32,0.72,0,1)' });
};

window.shakeMatrixCell = function (matrixId, r, c) {
  const input = document.querySelector(`input[data-matrix-id="${matrixId}"][data-matrix-row="${r}"][data-matrix-col="${c}"]`);
  if (!input) return;
  input.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
  input.focus();
  const wrap = input.closest('.matrix-input');
  const ctrl = input.closest('.q-field__control');
  if (wrap) {
    wrap.classList.remove('animate-shake'); void wrap.offsetWidth; wrap.classList.add('animate-shake');
    wrap.addEventListener('animationend', () => wrap.classList.remove('animate-shake'), { once: true });
  }
  if (ctrl) { ctrl.style.outline = '2px solid var(--error)'; setTimeout(() => { ctrl.style.outline = ''; }, 1800); }
};
