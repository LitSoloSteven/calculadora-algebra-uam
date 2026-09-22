/**
 * Scalaris — Theming and View Transitions
 */

// Prevenir FOUC (Flash of Unstyled Content) de tema claro
(function () {
  var mapa = { claro: 'papel', aqua: 'marea', oscuro: 'medianoche' };
  var t = localStorage.getItem('theme') || 'papel';
  if (mapa[t]) { t = mapa[t]; localStorage.setItem('theme', t); }
  var r = document.documentElement;
  r.setAttribute('data-theme', t);
  r.style.colorScheme = (t === 'medianoche') ? 'dark' : 'light';
})();

function applyTheme(themeName) {
  document.documentElement.setAttribute('data-theme', themeName);
  document.documentElement.style.colorScheme = (themeName === 'medianoche') ? 'dark' : 'light';
  localStorage.setItem('theme', themeName);

  var logoSrc = (themeName === 'medianoche') ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';
  document.querySelectorAll('img.brand-logo-reactive').forEach(function (img) {
    img.src = logoSrc;
  });

  if (typeof updatePlotlyTheme === 'function') {
    setTimeout(() => updatePlotlyTheme(themeName), 100);
  }
}

/* 1. Guardar el origen del clic antes de navegar */
addEventListener('click', function (e) {
  try {
    sessionStorage.setItem('nav-origin', JSON.stringify({ x: e.clientX, y: e.clientY }));
  } catch (_) { }
}, { capture: true });

/* 2. Animar el documento entrante con el mismo reveal circular */
addEventListener('pagereveal', function (e) {
  if (!e.viewTransition) return;
  var o = { x: innerWidth / 2, y: innerHeight / 2 };
  try { o = JSON.parse(sessionStorage.getItem('nav-origin')) || o; } catch (_) { }
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  e.viewTransition.ready.then(function () {
    var r = Math.hypot(Math.max(o.x, innerWidth - o.x), Math.max(o.y, innerHeight - o.y));
    document.documentElement.animate(
      {
        clipPath: ['circle(0px at ' + o.x + 'px ' + o.y + 'px)',
        'circle(' + r + 'px at ' + o.x + 'px ' + o.y + 'px)']
      },
      {
        duration: 500, easing: 'cubic-bezier(0.32, 0.72, 0, 1)',
        pseudoElement: '::view-transition-new(root)'
      }
    );
  });
});

function setTheme(themeName) {
  if (!document.startViewTransition) {
    applyTheme(themeName);
    return;
  }

  var x = (window.lastMouseClick && window.lastMouseClick.x !== undefined) ? window.lastMouseClick.x : window.innerWidth / 2;
  var y = (window.lastMouseClick && window.lastMouseClick.y !== undefined) ? window.lastMouseClick.y : window.innerHeight / 2;
  var endRadius = Math.hypot(
    Math.max(x, window.innerWidth - x),
    Math.max(y, window.innerHeight - y)
  );

  var transition = document.startViewTransition(() => {
    applyTheme(themeName);
  });

  transition.ready.then(() => {
    var dur = (window.MOTION && window.MOTION.slow) ? window.MOTION.slow : 500;
    document.documentElement.animate(
      [
        { clipPath: `circle(0px at ${x}px ${y}px)` },
        { clipPath: `circle(${endRadius}px at ${x}px ${y}px)` }
      ],
      {
        duration: dur,
        easing: 'ease-in-out',
        pseudoElement: '::view-transition-new(root)',
      }
    );
  });
}
