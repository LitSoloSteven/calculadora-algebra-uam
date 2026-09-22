/**
 * Scalaris — Splash Screen Animation Overlay
 */
(function () {
  if (sessionStorage.getItem('splash-shown')) return;
  sessionStorage.setItem('splash-shown', '1');
  var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var dur = reduced ? 400 : 3000;
  var tema = document.documentElement.getAttribute('data-theme');
  var logo = (tema === 'medianoche') ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';

  var overlay = document.createElement('div');
  overlay.id = 'agy-splash-overlay';
  overlay.style.cssText = 'position: fixed; inset: 0; z-index: 99999; background: var(--bg-page); display: flex; flex-direction: column; align-items: center; justify-content: center; view-transition-name: none; transform-origin: center;';

  overlay.innerHTML = `
      <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 120px; height: 120px;">
        <img id="splash-logo" src="${logo}" style="width: 80px; height: 80px; object-fit: contain; opacity: 0; transform: scale(0.88);" alt="Logo">
        <svg id="splash-ring" style="position: absolute; inset: 0; width: 100%; height: 100%; transform: rotate(-90deg);" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="58" fill="none" stroke="var(--accent)" stroke-width="2" stroke-dasharray="365" stroke-dashoffset="365"></circle>
        </svg>
      </div>
      <div style="margin-top: 20px; font-family: 'Space Grotesk', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;">
        <span id="splash-t1" style="font-size: 28px; font-weight: 700; letter-spacing: -0.02em; color: var(--text-main); clip-path: inset(0 100% 0 0); display: inline-block;">Scalaris</span>
        <span id="splash-t2" style="font-size: 11px; font-weight: 700; letter-spacing: 0.25em; text-transform: uppercase; opacity: 0; color: var(--accent); margin-top: 2px;">UAM</span>
      </div>
    `;
  document.documentElement.appendChild(overlay);

  if (reduced) {
    overlay.animate([{ opacity: 1 }, { opacity: 0 }], { duration: dur, fill: 'forwards' });
    setTimeout(() => overlay.remove(), dur);
    return;
  }

  var logoEl = overlay.querySelector('#splash-logo');
  var ringCircle = overlay.querySelector('#splash-ring circle');
  var ringEl = overlay.querySelector('#splash-ring');
  var t1 = overlay.querySelector('#splash-t1');
  var t2 = overlay.querySelector('#splash-t2');

  // 0-600: Logo entra
  logoEl.animate(
    [{ transform: 'scale(0.88)', opacity: 0 }, { transform: 'scale(1)', opacity: 1 }],
    { duration: 600, easing: 'cubic-bezier(0.32, 0.72, 0, 1)', fill: 'forwards' }
  );

  // 600-1800: Anillo traza y textos
  ringCircle.animate(
    [{ strokeDashoffset: 365 }, { strokeDashoffset: 0 }],
    { duration: 1200, delay: 600, easing: 'ease-in-out', fill: 'forwards' }
  );
  if (t1) {
    t1.animate(
      [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)' }],
      { duration: 500, delay: 800, easing: 'cubic-bezier(0.16, 1, 0.3, 1)', fill: 'forwards' }
    );
  }
  if (t2) {
    t2.animate(
      [{ opacity: 0, transform: 'translateY(3px)' }, { opacity: 1, transform: 'translateY(0)' }],
      { duration: 400, delay: 1200, easing: 'ease-out', fill: 'forwards' }
    );
  }

  // 1800-2600: Pulso del anillo y barra
  ringEl.animate(
    [{ transform: 'rotate(-90deg) scale(1)' }, { transform: 'rotate(-90deg) scale(1.03)', offset: 0.5 }, { transform: 'rotate(-90deg) scale(1)' }],
    { duration: 800, delay: 1800, easing: 'ease-in-out' }
  );

  var bar = document.createElement('div');
  bar.style.cssText = 'height: 2px; background: var(--accent); width: 0; margin-top: 12px; border-radius: 2px;';
  overlay.appendChild(bar);
  bar.animate(
    [{ width: '0' }, { width: '120px' }],
    { duration: 600, delay: 1800, easing: 'ease-out', fill: 'forwards' }
  );

  // 2600-3000: Overlay se desvanece y body entra
  setTimeout(() => overlay.style.pointerEvents = 'none', 2600);
  overlay.animate(
    [{ opacity: 1, transform: 'scale(1)', filter: 'blur(0)' }, { opacity: 0, transform: 'scale(1.04)', filter: 'blur(4px)' }],
    { duration: 400, delay: 2600, easing: 'ease-in-out', fill: 'forwards' }
  );

  setTimeout(() => {
    if (document.body) {
      document.body.animate(
        [{ transform: 'translateY(16px)' }, { transform: 'translateY(0)' }],
        { duration: 400, easing: 'ease-out' }
      );
    }
  }, 2600);

  setTimeout(() => overlay.remove(), 3100);
})();
