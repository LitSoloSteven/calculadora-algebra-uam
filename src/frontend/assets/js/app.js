/**
 * Scalaris — Global App Interactions, Animations & Utilities
 */

// Detección de método de entrada para accesibilidad de movimiento
document.addEventListener('keydown', () => {
  document.documentElement.setAttribute('data-input', 'keyboard');
}, { capture: true, passive: true });

document.addEventListener('pointerdown', () => {
  document.documentElement.setAttribute('data-input', 'pointer');
}, { capture: true, passive: true });

window.scalarisMotionOK = function () {
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return false;
  }
  if (document.documentElement.getAttribute('data-input') === 'keyboard') {
    return false;
  }
  return true;
};

// Constantes de movimiento (espejo de los tokens CSS para uso en JS)
window.MOTION = { fast: 120, med: 240, slow: 500 };

window.replayResultAnimation = function (elId) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.classList.remove('animate-slide-up');
  void el.offsetWidth; // reflow para reiniciar
  el.classList.add('animate-slide-up');
  const done = (e) => {
    if (e.target !== el) return; // ignorar animationend de hijos (.timeline-expansion)
    el.classList.remove('animate-slide-up');
    el.removeEventListener('animationend', done);
  };
  el.addEventListener('animationend', done);
};

// Rastreador del clic del mouse para animación de onda expansiva
window.lastMouseClick = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
document.addEventListener('click', e => {
  window.lastMouseClick = { x: e.clientX, y: e.clientY };
}, { capture: true });

// Delegated tooltip para celdas con contenido truncado
document.addEventListener('mouseover', e => {
  const target = e.target;
  if (target && target.matches && target.matches('.matrix-input input')) {
    if (target.scrollWidth > target.clientWidth) {
      target.title = target.value || '';
    } else if (target.hasAttribute('title')) {
      target.removeAttribute('title');
    }
  }
});
document.addEventListener('focusin', e => {
  const target = e.target;
  if (target && target.matches && target.matches('.matrix-input input')) {
    if (target.scrollWidth > target.clientWidth) {
      target.title = target.value || '';
    }
  }
});

// Función global robusta para MathJax con fallback de carga asíncrona
window.typesetMathWhenReady = function (elementIds, maxWaitMs) {
  maxWaitMs = maxWaitMs || 5000;
  var start = Date.now();
  function attempt() {
    if (window.MathJax && window.MathJax.typesetPromise) {
      if (elementIds && elementIds.length) {
        var els = elementIds.map(id => document.getElementById(id)).filter(Boolean);
        if (els.length > 0) {
          window.MathJax.typesetClear(els);
          window.MathJax.typesetPromise(els).catch(err => console.log(err));
        }
      } else {
        window.MathJax.typesetClear();
        window.MathJax.typesetPromise().catch(err => console.log(err));
      }
    } else if (Date.now() - start < maxWaitMs) {
      setTimeout(attempt, 100);
    }
  }
  attempt();
};

// Máquina de escribir para explicaciones
window.typewriterEffect = function (elementId, text, speed = 18) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const el = document.getElementById(elementId);
    if (el) el.textContent = text;
    return;
  }
  const el = document.getElementById(elementId);
  if (!el) return;

  el.innerHTML = '<span class="tw-text"></span><span class="tw-cursor">▌</span>';
  const textSpan = el.querySelector('.tw-text');
  const cursorSpan = el.querySelector('.tw-cursor');
  let i = 0;

  const skip = () => {
    textSpan.textContent = text;
    cursorSpan.style.display = 'none';
    el.removeEventListener('click', skip);
  };
  el.addEventListener('click', skip);

  function type() {
    if (i < text.length) {
      textSpan.textContent += text.charAt(i);
      i++;
      setTimeout(type, speed);
    } else {
      cursorSpan.style.display = 'none';
      el.removeEventListener('click', skip);
    }
  }
  type();
};

function updatePlotlyTheme(theme) {
  let textColor = '#23262E';
  let gridColor = 'rgba(128,128,128,0.2)';
  if (theme === 'medianoche') { textColor = '#EAF6FF'; gridColor = 'rgba(255,255,255,0.06)'; }
  if (theme === 'marea') { textColor = '#0B1F33'; gridColor = 'rgba(11,31,51,0.1)'; }

  document.querySelectorAll('.js-plotly-plot').forEach(plot => {
    if (!plot.isConnected || !plot._fullLayout) return;
    if (window.Plotly && window.Plotly.relayout) {
      try {
        Plotly.relayout(plot, {
          'font.color': textColor,
          'scene.xaxis.gridcolor': gridColor,
          'scene.yaxis.gridcolor': gridColor,
          'scene.zaxis.gridcolor': gridColor
        }).catch(() => { });
      } catch(e) {}
    }
  });
}

window.updatePlotlyThemeWhenReady = function (maxWaitMs = 5000) {
  var start = Date.now();
  function attempt() {
    let plots = document.querySelectorAll('.js-plotly-plot');
    let ready = Array.from(plots).some(p => p.isConnected && p._fullLayout);
    if (ready) {
      let currentTheme = document.documentElement.getAttribute('data-theme') || 'papel';
      updatePlotlyTheme(currentTheme);
    } else if (Date.now() - start < maxWaitMs) {
      setTimeout(attempt, 100);
    } else {
      console.warn("updatePlotlyThemeWhenReady: maxWaitMs expiró sin encontrar gráficas inicializadas.");
    }
  }
  attempt();
};

// === ANIMACIÓN DE RECOLECCIÓN DE BASURA ===
function animateGarbageCollection() {
  if (!window.scalarisMotionOK()) return;
  const btn = document.getElementById('btn-limpiar-main');
  if (!btn) return;

  const iconElem = btn.querySelector('.q-icon');
  if (iconElem) {
    iconElem.textContent = 'delete_sweep';
    iconElem.classList.add('text-err');
  }

  const btnRect = btn.getBoundingClientRect();
  const inputs = document.querySelectorAll('.matrix-input input');

  let delay = 0;
  let animatedCount = 0;

  Array.from(inputs).filter(i => {
    const r = i.getBoundingClientRect();
    return i.value && i.value !== '0' && r.bottom > 0 && r.top < window.innerHeight && r.right > 0 && r.left < window.innerWidth;
  }).slice(0, 40).forEach((input) => {
    if (!input.value || input.value === '0' || input.value.trim() === '') return;
    animatedCount++;

    const rect = input.getBoundingClientRect();
    const clone = document.createElement('div');

    // Igualar estilos del input clonado
    clone.textContent = input.value;
    clone.style.position = 'fixed';
    clone.style.left = rect.left + 'px';
    clone.style.top = rect.top + 'px';
    clone.style.width = rect.width + 'px';
    clone.style.height = rect.height + 'px';
    clone.style.margin = '0';
    clone.style.zIndex = 'var(--z-modal)';
    clone.style.display = 'flex';
    clone.style.alignItems = 'center';
    clone.style.justifyContent = 'center';

    // Copiar diseño del contenedor padre (caja neumórfica)
    const container = input.closest('.q-field__control');
    if (container) {
      const style = window.getComputedStyle(container);
      clone.style.background = style.background;
      clone.style.borderRadius = style.borderRadius;
      clone.style.boxShadow = style.boxShadow;
    }

    const inputStyle = window.getComputedStyle(input);
    clone.style.fontFamily = inputStyle.fontFamily;
    clone.style.fontSize = inputStyle.fontSize;
    clone.style.color = inputStyle.color;

    clone.style.transition = 'transform 240ms cubic-bezier(0.32, 0.72, 0, 1), opacity 240ms cubic-bezier(0.32, 0.72, 0, 1)';
    clone.style.pointerEvents = 'none';

    // Ocultar texto original
    input.style.color = 'transparent';

    document.body.appendChild(clone);

    setTimeout(() => {
      input.value = ''; // Vaciar la celda visualmente

      const targetX = btnRect.left + btnRect.width / 2 - rect.width / 2;
      const targetY = btnRect.top + btnRect.height / 2 - rect.height / 2;
      clone.style.transform = `translate(${targetX - rect.left}px, ${targetY - rect.top}px) scale(0.1)`;
      clone.style.opacity = '0';
    }, delay);

    setTimeout(() => clone.remove(), delay + 240);

    delay += 30; // Stagger effect
  });

  // Efecto de Squash & Bounce al final
  if (animatedCount > 0) {
    setTimeout(() => {
      btn.classList.add('squash-bounce');
      setTimeout(() => {
        btn.classList.remove('squash-bounce');
        if (iconElem) {
          iconElem.textContent = 'delete';
          iconElem.classList.remove('text-err');
        }
        // Restaurar colores transparentes
        inputs.forEach(i => i.style.color = '');
      }, MOTION.slow);
    }, delay + MOTION.med);
  } else {
    if (iconElem) {
      iconElem.textContent = 'delete';
      iconElem.classList.remove('text-err');
    }
    inputs.forEach(i => i.style.color = '');
  }
}
