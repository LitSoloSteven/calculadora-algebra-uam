(function () {
  var KEY = 'scalaris:recent', MAX = 4;
  function read() {
    try {
      var raw = localStorage.getItem(KEY);
      var arr = raw ? JSON.parse(raw) : [];
      if (!Array.isArray(arr)) return { ok: false, ids: [] };
      return { ok: true, ids: arr.filter(function (x) { return typeof x === 'string'; }) };
    } catch (_) { return { ok: false, ids: [] }; }
  }
  window.scalarisReadRecent = read;
  window.scalarisRecordVisit = function (id) {
    if (typeof id !== 'string' || !id) return;
    try {
      var ids = read().ids.filter(function (x) { return x !== id; });
      ids.unshift(id);
      localStorage.setItem(KEY, JSON.stringify(ids.slice(0, MAX)));
    } catch (_) { }
  };
})();

(function () {
  var pendingTimer = null;
  if (window.location && window.location.pathname === '/') {
    document.documentElement.setAttribute('data-glosa', 'closed');
    if (document.body) document.body.classList.add('hub-page');
    document.documentElement.setAttribute('data-hub-pending', '');
    pendingTimer = setTimeout(function () {
      document.documentElement.removeAttribute('data-hub-pending');
      pendingTimer = null;
    }, 1200);
  }

  function clearPending() {
    if (pendingTimer) {
      clearTimeout(pendingTimer);
      pendingTimer = null;
    }
    document.documentElement.removeAttribute('data-hub-pending');
  }

  function motionAllowed() {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return false;
    }
    return window.scalarisMotionOK ? window.scalarisMotionOK() : true;
  }

  var currentIdx = 0;
  var isDragging = false;
  var isPointerDown = false;
  var suppressClick = false;
  var startX = 0, startY = 0;
  var startTranslateX = 0, currentTranslateX = 0;
  var lastX = 0, lastTime = 0, velocity = 0;
  var isHorizontal = null;

  function getElements() {
    var carousel = document.querySelector('.hub-carousel');
    var viewport = document.querySelector('.hub-viewport');
    var track = document.querySelector('.hub-track');
    var cards = document.querySelectorAll('.hub-card');
    var panels = document.querySelectorAll('.hub-aug .hub-panel');
    var prevBtn = document.querySelector('.hub-prev');
    var nextBtn = document.querySelector('.hub-next');
    return {
      carousel: carousel,
      viewport: viewport,
      track: track,
      cards: cards ? Array.prototype.slice.call(cards) : [],
      panels: panels ? Array.prototype.slice.call(panels) : [],
      prevBtn: prevBtn,
      nextBtn: nextBtn
    };
  }

  function getCenterGap(viewport, card) {
    if (!viewport || !card) return 0;
    return (viewport.clientWidth - card.offsetWidth) / 2;
  }

  function getTargetTranslateX(idx, els) {
    els = els || getElements();
    if (!els.viewport || !els.cards[idx]) return 0;
    var card = els.cards[idx];
    return -card.offsetLeft + getCenterGap(els.viewport, card);
  }

  function applyCardsDepth(trackOffset, els) {
    els = els || getElements();
    if (!els.viewport || els.cards.length === 0) return;

    var gap = 0;
    if (els.track && window.getComputedStyle) {
      var cs = window.getComputedStyle(els.track);
      gap = parseFloat(cs.columnGap) || parseFloat(cs.gap) || 0;
    }
    var vpCenter = els.viewport.clientWidth / 2;

    for (var i = 0; i < els.cards.length; i++) {
      var card = els.cards[i];
      var body = card.querySelector('.hub-card-body');
      if (!body) continue;

      var dist = Math.abs(trackOffset + card.offsetLeft + card.offsetWidth / 2 - vpCenter);
      var paso = card.offsetWidth + gap;
      var factor = Math.max(0, Math.min(1, 1 - (paso > 0 ? dist / paso : 0)));

      body.style.setProperty('--hub-focus', factor.toFixed(3));
    }
  }

  function clearCardsDepth(els) {
    els = els || getElements();
    for (var i = 0; i < els.cards.length; i++) {
      var card = els.cards[i];
      var body = card.querySelector('.hub-card-body');
      if (body) {
        body.style.removeProperty('--hub-focus');
      }
    }
  }

  function updateCarouselPosition(instant) {
    var els = getElements();
    if (!els.track || els.cards.length === 0) return;

    var targetX = getTargetTranslateX(currentIdx, els);
    currentTranslateX = targetX;

    if (instant || !motionAllowed()) {
      els.track.classList.remove('is-ready');
      els.track.style.transition = 'none';
      els.track.style.transform = 'translateX(' + targetX + 'px)';
      clearCardsDepth(els);
      // Forzar layout para que la siguiente transicion sea suave
      void els.track.offsetHeight;
      requestAnimationFrame(function () {
        els.track.classList.add('is-ready');
        els.track.style.transition = '';
      });
    } else {
      els.track.classList.add('is-ready');
      els.track.style.transition = '';
      els.track.style.transform = 'translateX(' + targetX + 'px)';
      clearCardsDepth(els);
    }

    if (els.prevBtn) {
      if (currentIdx === 0) {
        els.prevBtn.setAttribute('aria-disabled', 'true');
        els.prevBtn.disabled = true;
      } else {
        els.prevBtn.removeAttribute('aria-disabled');
        els.prevBtn.disabled = false;
      }
    }
    if (els.nextBtn) {
      if (currentIdx >= els.cards.length - 1) {
        els.nextBtn.setAttribute('aria-disabled', 'true');
        els.nextBtn.disabled = true;
      } else {
        els.nextBtn.removeAttribute('aria-disabled');
        els.nextBtn.disabled = false;
      }
    }
  }

  function selectPillar(pillarId, opts) {
    opts = opts || {};
    clearPending();
    var els = getElements();
    if (els.cards.length === 0) return;

    var targetIdx = -1;
    for (var i = 0; i < els.cards.length; i++) {
      var cid = els.cards[i].id.replace(/^hub-tab-/, '');
      if (cid === pillarId) {
        targetIdx = i;
        break;
      }
    }
    if (targetIdx === -1) targetIdx = 0;
    currentIdx = targetIdx;

    var instant = Boolean(opts.instant || !motionAllowed());

    // Actualizar tabs (E20: JS posee aria-selected, tabindex, is-active)
    for (var k = 0; k < els.cards.length; k++) {
      var c = els.cards[k];
      if (k === currentIdx) {
        c.classList.add('is-active');
        c.setAttribute('aria-selected', 'true');
        c.setAttribute('tabindex', '0');
      } else {
        c.classList.remove('is-active');
        c.setAttribute('aria-selected', 'false');
        c.setAttribute('tabindex', '-1');
      }
    }

    // Actualizar panels (E20: JS posee inert, is-active)
    for (var j = 0; j < els.panels.length; j++) {
      var p = els.panels[j];
      var pid = p.id.replace(/^hub-panel-/, '');
      if (pid === pillarId) {
        p.classList.add('is-active');
        p.inert = false;
        p.removeAttribute('inert');
      } else {
        p.classList.remove('is-active');
        p.inert = true;
        p.setAttribute('inert', '');
      }
    }

    updateCarouselPosition(instant);
  }

  window.scalarisHubSelect = selectPillar;

  // Pointer drag & swipe handling
  function onPointerDown(e) {
    if (!e.isPrimary || (e.button !== undefined && e.button !== 0)) return;
    var els = getElements();
    if (!els.track || els.cards.length === 0) return;

    isPointerDown = true;
    isDragging = false;
    isHorizontal = null;
    startX = e.clientX;
    startY = e.clientY;
    lastX = startX;
    lastTime = performance.now();
    velocity = 0;

    // Calcular translate actual
    var matrix = window.getComputedStyle(els.track).transform;
    if (matrix && matrix !== 'none') {
      var match = matrix.match(/matrix\(([^)]+)\)/);
      if (match) {
        var parts = match[1].split(', ');
        startTranslateX = parseFloat(parts[4]) || getTargetTranslateX(currentIdx, els);
      } else {
        startTranslateX = getTargetTranslateX(currentIdx, els);
      }
    } else {
      startTranslateX = getTargetTranslateX(currentIdx, els);
    }
    currentTranslateX = startTranslateX;
  }

  function onPointerMove(e) {
    if (!isPointerDown) return;
    if (!e.isPrimary) return;
    if (e.pointerType === 'mouse' && e.buttons === 0) {
      isPointerDown = false;
      isDragging = false;
      return;
    }
    var dx = e.clientX - startX;
    var dy = e.clientY - startY;

    if (isHorizontal === null) {
      if (Math.hypot(dx, dy) >= 6) {
        if (Math.abs(dx) > Math.abs(dy)) {
          isHorizontal = true;
          isDragging = true;
          var els = getElements();
          if (els.carousel) {
            els.carousel.classList.add('is-dragging');
          }
          if (els.track) {
            els.track.classList.remove('is-ready');
            els.track.style.transition = 'none';
          }
          try {
            e.currentTarget.setPointerCapture(e.pointerId);
          } catch (_) {}
        } else {
          isHorizontal = false;
        }
      }
    }

    if (!isHorizontal || !isDragging) return;

    var now = performance.now();
    var dt = now - lastTime;
    if (dt > 8) {
      velocity = (e.clientX - lastX) / dt;
      lastX = e.clientX;
      lastTime = now;
    }

    var elsMove = getElements();
    var maxX = getTargetTranslateX(0, elsMove);
    var minX = getTargetTranslateX(elsMove.cards.length - 1, elsMove);
    var targetX = startTranslateX + dx;

    // Fricción creciente en los extremos
    if (targetX > maxX) {
      var over = targetX - maxX;
      targetX = maxX + over * 0.3;
    } else if (targetX < minX) {
      var under = minX - targetX;
      targetX = minX - under * 0.3;
    }

    currentTranslateX = targetX;
    elsMove.track.style.transform = 'translateX(' + targetX.toFixed(1) + 'px)';
    applyCardsDepth(targetX, elsMove);
  }

  function onPointerUp(e) {
    if (!isPointerDown) return;
    isPointerDown = false;
    if (!e.isPrimary) return;
    try {
      if (e.currentTarget.hasPointerCapture && e.currentTarget.hasPointerCapture(e.pointerId)) {
        e.currentTarget.releasePointerCapture(e.pointerId);
      }
    } catch (_) {}

    var els = getElements();
    if (els.carousel) {
      els.carousel.classList.remove('is-dragging');
    }

    if (isDragging) {
      isDragging = false;
      var targetIdx = currentIdx;

      // Flick rápido (> 0.11 px/ms)
      if (Math.abs(velocity) > 0.11) {
        if (velocity < -0.11 && currentIdx < els.cards.length - 1) {
          targetIdx = currentIdx + 1;
        } else if (velocity > 0.11 && currentIdx > 0) {
          targetIdx = currentIdx - 1;
        }
      } else {
        // Snap al más cercano
        var minDiff = Infinity;
        for (var i = 0; i < els.cards.length; i++) {
          var snapX = getTargetTranslateX(i, els);
          var diff = Math.abs(currentTranslateX - snapX);
          if (diff < minDiff) {
            minDiff = diff;
            targetIdx = i;
          }
        }
      }

      var pillarId = els.cards[targetIdx].id.replace(/^hub-tab-/, '');
      selectPillar(pillarId, { instant: false });

      suppressClick = true;
      setTimeout(function () { suppressClick = false; }, 60);
    }
  }

  function onPointerCancel(e) {
    if (!isPointerDown) return;
    isPointerDown = false;
    if (!e.isPrimary) return;
    try {
      if (e.currentTarget.hasPointerCapture && e.currentTarget.hasPointerCapture(e.pointerId)) {
        e.currentTarget.releasePointerCapture(e.pointerId);
      }
    } catch (_) {}

    var els = getElements();
    if (els.carousel) {
      els.carousel.classList.remove('is-dragging');
    }
    isDragging = false;
    updateCarouselPosition(false);
  }

  var wheelTimer = null;
  function onWheel(e) {
    var dx = e.deltaX;
    if (e.shiftKey && !dx) dx = e.deltaY;
    if (Math.abs(dx) > 30) {
      if (wheelTimer) return;
      var els = getElements();
      if (dx > 0 && currentIdx < els.cards.length - 1) {
        var nextId = els.cards[currentIdx + 1].id.replace(/^hub-tab-/, '');
        selectPillar(nextId);
      } else if (dx < 0 && currentIdx > 0) {
        var prevId = els.cards[currentIdx - 1].id.replace(/^hub-tab-/, '');
        selectPillar(prevId);
      }
      wheelTimer = setTimeout(function () {
        wheelTimer = null;
      }, 250);
    }
  }

  var observersAttached = false;

  function initObservers() {
    if (observersAttached) return true;
    var els = getElements();
    if (!els.viewport) return false;

    observersAttached = true;

    els.viewport.addEventListener('pointerdown', onPointerDown);
    els.viewport.addEventListener('pointermove', onPointerMove);
    els.viewport.addEventListener('pointerup', onPointerUp);
    els.viewport.addEventListener('pointercancel', onPointerCancel);
    els.viewport.addEventListener('wheel', onWheel, { passive: true });

    if (window.ResizeObserver) {
      var ro = new ResizeObserver(function () {
        updateCarouselPosition(true);
      });
      ro.observe(els.viewport);
      if (els.track) ro.observe(els.track);
    }

    requestAnimationFrame(function () {
      updateCarouselPosition(true);
    });

    return true;
  }

  function startMountObserver() {
    if (initObservers()) return;

    var mo = null;
    var moTimer = null;

    function cleanup() {
      if (moTimer) {
        clearTimeout(moTimer);
        moTimer = null;
      }
      if (mo) {
        mo.disconnect();
        mo = null;
      }
    }

    moTimer = setTimeout(cleanup, 5000);

    if (window.MutationObserver) {
      mo = new MutationObserver(function () {
        if (initObservers()) {
          cleanup();
        }
      });
      var rootTarget = document.body || document.documentElement;
      if (rootTarget) {
        mo.observe(rootTarget, { childList: true, subtree: true });
      }
    }
  }

  var delegatedRegistered = false;

  function registerDelegatedListeners() {
    if (delegatedRegistered) return;
    delegatedRegistered = true;

    window.addEventListener('resize', function () { updateCarouselPosition(true); });
    document.addEventListener('scalaris:glosa', function (e) {
      if (window.location && window.location.pathname === '/' && e.detail && e.detail.open) {
        if (window.scalarisGlosa && window.scalarisGlosa.close) {
          window.scalarisGlosa.close({ instant: true });
        }
      }
      updateCarouselPosition(true);
    });
    document.addEventListener('scalaris:layout', function () { updateCarouselPosition(true); });

    // Clic en tarjetas y botones prev/next
    document.addEventListener('click', function (e) {
      if (suppressClick) {
        e.preventDefault();
        e.stopPropagation();
        return;
      }

      var prevBtn = e.target.closest('.hub-prev');
      if (prevBtn) {
        var elsPrev = getElements();
        if (currentIdx > 0) {
          var isKeyboardPrev = (e.detail === 0);
          var pidPrev = elsPrev.cards[currentIdx - 1].id.replace(/^hub-tab-/, '');
          selectPillar(pidPrev, { instant: isKeyboardPrev });
          if (elsPrev.cards[currentIdx]) {
            elsPrev.cards[currentIdx].focus({ preventScroll: true });
          }
        }
        return;
      }

      var nextBtn = e.target.closest('.hub-next');
      if (nextBtn) {
        var elsNext = getElements();
        if (currentIdx < elsNext.cards.length - 1) {
          var isKeyboardNext = (e.detail === 0);
          var pidNext = elsNext.cards[currentIdx + 1].id.replace(/^hub-tab-/, '');
          selectPillar(pidNext, { instant: isKeyboardNext });
          if (elsNext.cards[currentIdx]) {
            elsNext.cards[currentIdx].focus({ preventScroll: true });
          }
        }
        return;
      }

      var card = e.target.closest('.hub-card');
      if (!card) return;
      var id = card.id.replace(/^hub-tab-/, '');
      if (!id) return;
      var isKeyboard = (e.detail === 0);
      selectPillar(id, { instant: isKeyboard });
    });

    // Teclado WAI-ARIA
    document.addEventListener('keydown', function (e) {
      if (e.defaultPrevented) return;
      if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;

      var active = document.activeElement;
      if (!active) return;

      var cardEl = active.closest ? active.closest('.hub-card') : null;
      var tileEl = active.closest ? active.closest('.hub-tile') : null;

      if (cardEl && cardEl.closest('.hub-track')) {
        var currentEls = getElements();
        var cards = currentEls.cards;
        var cardIdx = cards.indexOf(cardEl);
        if (cardIdx === -1) return;

        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight' || e.key === 'Home' || e.key === 'End') {
          var targetIdx;
          if (e.key === 'ArrowLeft') {
            targetIdx = (cardIdx - 1 + cards.length) % cards.length;
          } else if (e.key === 'ArrowRight') {
            targetIdx = (cardIdx + 1) % cards.length;
          } else if (e.key === 'Home') {
            targetIdx = 0;
          } else if (e.key === 'End') {
            targetIdx = cards.length - 1;
          }
          var targetCard = cards[targetIdx];
          if (targetCard && targetCard !== cardEl) {
            e.preventDefault();
            var id = targetCard.id.replace(/^hub-tab-/, '');
            selectPillar(id, { instant: true });
            targetCard.focus({ preventScroll: true });
          }
        } else if (e.key === 'ArrowDown') {
          var activeTiles = Array.prototype.slice.call(
            document.querySelectorAll('.hub-panel.is-active .hub-tile')
          );
          if (activeTiles.length > 0) {
            e.preventDefault();
            activeTiles[0].focus({ preventScroll: true });
          }
        }
      } else if (tileEl && tileEl.closest('.hub-panel.is-active')) {
        if (e.key === 'ArrowUp') {
          var tiles = Array.prototype.slice.call(
            document.querySelectorAll('.hub-panel.is-active .hub-tile')
          );
          var tileIdx = tiles.indexOf(tileEl);
          if (tileIdx === 0) {
            var currentEls2 = getElements();
            if (currentEls2.cards[currentIdx]) {
              e.preventDefault();
              currentEls2.cards[currentIdx].focus({ preventScroll: true });
            }
          } else if (tileIdx > 0) {
            e.preventDefault();
            tiles[tileIdx - 1].focus({ preventScroll: true });
          }
        } else if (e.key === 'ArrowDown') {
          var tilesDown = Array.prototype.slice.call(
            document.querySelectorAll('.hub-panel.is-active .hub-tile')
          );
          var tIdx = tilesDown.indexOf(tileEl);
          if (tIdx !== -1 && tIdx < tilesDown.length - 1) {
            e.preventDefault();
            tilesDown[tIdx + 1].focus({ preventScroll: true });
          }
        } else if (e.key === 'ArrowLeft') {
          var currentEls3 = getElements();
          if (currentEls3.cards[currentIdx]) {
            e.preventDefault();
            currentEls3.cards[currentIdx].focus({ preventScroll: true });
          }
        }
      }
    });
  }

  registerDelegatedListeners();
  startMountObserver();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      startMountObserver();
    });
  }
})();
