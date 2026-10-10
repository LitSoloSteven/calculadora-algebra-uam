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
  var splashObserver = null;
  var splashWasPresent = false;
  var pendingDeadline = 0;
  if (window.location && window.location.pathname === '/') {
    document.documentElement.setAttribute('data-glosa', 'closed');
    if (document.body) document.body.classList.add('hub-page');
    document.documentElement.setAttribute('data-hub-pending', '');
    pendingDeadline = Date.now() + 3400;
    splashWasPresent = Boolean(document.getElementById('agy-splash-overlay'));
    if (window.MutationObserver) {
      splashObserver = new MutationObserver(function () {
        var splashExists = Boolean(document.getElementById('agy-splash-overlay'));
        if (splashExists) splashWasPresent = true;
        else if (splashWasPresent) finishPending();
      });
      splashObserver.observe(document.documentElement, { childList: true, subtree: true });
    }
    pendingTimer = setTimeout(function () {
      pendingTimer = null;
      if (document.getElementById('agy-splash-overlay')) {
        pendingTimer = setTimeout(finishPending, Math.max(0, pendingDeadline - Date.now()));
      } else {
        finishPending();
      }
    }, 1200);
  }

  function finishPending() {
    if (pendingTimer) {
      clearTimeout(pendingTimer);
      pendingTimer = null;
    }
    if (splashObserver) {
      splashObserver.disconnect();
      splashObserver = null;
    }
    document.documentElement.removeAttribute('data-hub-pending');
  }

  function clearPending() {
    if (!document.getElementById('agy-splash-overlay')) finishPending();
  }

  var activeDialog = null;
  var activeOrigin = null;
  var closeTimer = null;
  var closeTransitionHandler = null;
  var closingDialog = null;
  var spotPositions = new WeakMap();
  var spotFrames = new WeakMap();

  function setInputMode(instant) {
    if (instant) document.documentElement.setAttribute('data-input', 'keyboard');
    else document.documentElement.removeAttribute('data-input');
  }

  function cancelCloseWait() {
    if (closeTimer) {
      clearTimeout(closeTimer);
      closeTimer = null;
    }
    if (closeTransitionHandler && closingDialog) {
      var card = closingDialog.querySelector('.hub-pop-card');
      if (card) card.removeEventListener('transitionend', closeTransitionHandler);
    }
    closeTransitionHandler = null;
    closingDialog = null;
  }

  function finishClose(dialog, restoreFocus) {
    var pillarId = dialog.id.replace(/^hub-pop-/, '');
    var origin = activeOrigin || document.getElementById('hub-row-' + pillarId);
    cancelCloseWait();
    if (dialog.open) dialog.close();
    dialog.removeAttribute('data-open');
    document.documentElement.removeAttribute('data-hub-dialog-open');
    var card = dialog.querySelector('.hub-pop-card');
    if (card) card.style.removeProperty('transform-origin');
    if (activeDialog === dialog) {
      activeDialog = null;
      activeOrigin = null;
    }
    if (restoreFocus !== false && origin && origin.isConnected) {
      origin.focus({ preventScroll: true });
    }
  }

  function calcOffset(offset) {
    return offset < 0 ? '- ' + Math.abs(offset) + 'px' : '+ ' + offset + 'px';
  }

  function setPopoverOrigin(card, row) {
    var rect = row.getBoundingClientRect();
    var centerX = rect.left + rect.width / 2;
    var centerY = rect.top + rect.height / 2;
    var xOffset = centerX - window.innerWidth / 2;
    var originY;
    if (window.matchMedia('(max-width: 639px)').matches) {
      originY = 'calc(100% ' + calcOffset(centerY - window.innerHeight) + ')';
    } else {
      originY = 'calc(50% ' + calcOffset(centerY - window.innerHeight / 2) + ')';
    }
    card.style.transformOrigin = 'calc(50% ' + calcOffset(xOffset) + ') ' + originY;
  }

  function open(pillarId, { instant, originEl } = {}) {
    clearPending();
    var row = originEl || document.getElementById('hub-row-' + pillarId);
    var dialog = document.getElementById('hub-pop-' + pillarId);
    if (!row || !dialog || typeof dialog.showModal !== 'function') return;

    setInputMode(Boolean(instant));
    if (activeDialog && activeDialog !== dialog) {
      finishClose(activeDialog, false);
    }
    cancelCloseWait();

    var card = dialog.querySelector('.hub-pop-card');
    if (card) {
      if (instant) card.style.removeProperty('transform-origin');
      else setPopoverOrigin(card, row);
    }
    if (!dialog.open) dialog.showModal();

    dialog.setAttribute('data-open', '');
    row.setAttribute('aria-expanded', 'true');
    activeDialog = dialog;
    activeOrigin = row;
    document.documentElement.setAttribute('data-hub-dialog-open', '');

    var initialFocus = dialog.querySelector('.hub-tile.is-featured')
      || dialog.querySelector('.hub-tile')
      || dialog.querySelector('.hub-pop-close');
    if (initialFocus) initialFocus.focus({ preventScroll: true });
  }

  function close({ instant } = {}) {
    var dialog = activeDialog || document.querySelector('dialog.hub-pop[open]');
    if (!dialog) return;

    if (instant) setInputMode(true);
    var expandedRows = document.querySelectorAll('.hub-row[aria-expanded="true"]');
    for (var i = 0; i < expandedRows.length; i++) {
      expandedRows[i].setAttribute('aria-expanded', 'false');
    }

    dialog.removeAttribute('data-open');
    if (instant || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      finishClose(dialog);
      return;
    }

    if (closeTimer && closingDialog === dialog) return;
    cancelCloseWait();
    closingDialog = dialog;
    var card = dialog.querySelector('.hub-pop-card');
    if (!card) {
      finishClose(dialog);
      return;
    }
    closeTransitionHandler = function (event) {
      if (event.target === card && event.propertyName === 'opacity') finishClose(dialog);
    };
    card.addEventListener('transitionend', closeTransitionHandler);
    closeTimer = setTimeout(function () { finishClose(dialog); }, 180);
  }

  function haloDisabled(event) {
    return event.pointerType === 'touch'
      || document.documentElement.getAttribute('data-input') === 'keyboard'
      || !window.matchMedia('(hover: hover) and (pointer: fine)').matches
      || window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function moveSpot(row, event) {
    var spot = row.querySelector('.hub-spot');
    if (!spot) return;
    var rect = row.getBoundingClientRect();
    spotPositions.set(row, {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    });
    if (spotFrames.has(row)) return;

    var frame = window.requestAnimationFrame(function () {
      spotFrames.delete(row);
      var position = spotPositions.get(row);
      if (!position || !row.isConnected) return;
      spot.style.transform = 'translate3d(' + position.x + 'px, ' + position.y + 'px, 0)';
    });
    spotFrames.set(row, frame);
  }

  function clearSpotForPointerOut(event) {
    var target = event.target;
    if (!target || typeof target.closest !== 'function') return;
    var row = target.closest('.hub-row');
    var related = event.relatedTarget;
    var nextRow = related && typeof related.closest === 'function'
      ? related.closest('.hub-row')
      : null;
    if (row && row !== nextRow) row.removeAttribute('data-spot-active');
  }

  function registerDelegatedListeners() {
    if (window.__scalarisHubDelegated) return;
    window.__scalarisHubDelegated = true;

    document.addEventListener('click', function (event) {
      var target = event.target;
      if (!target || typeof target.closest !== 'function') return;

      var closeButton = target.closest('.hub-pop-close');
      if (closeButton) {
        var closeFromKeyboard = event.detail === 0;
        setInputMode(closeFromKeyboard);
        close({ instant: closeFromKeyboard });
        return;
      }

      var dialog = target.closest('dialog.hub-pop');
      if (dialog && target === dialog) {
        var scrimCloseFromKeyboard = event.detail === 0;
        setInputMode(scrimCloseFromKeyboard);
        close({ instant: scrimCloseFromKeyboard });
        return;
      }

      var row = target.closest('.hub-row');
      if (!row) return;
      var pillarId = row.id.replace(/^hub-row-/, '');
      if (!pillarId) return;
      var openedFromKeyboard = event.detail === 0;
      open(pillarId, { instant: openedFromKeyboard, originEl: row });
    });

    document.addEventListener('cancel', function (event) {
      var dialog = event.target;
      if (!dialog || !dialog.matches || !dialog.matches('dialog.hub-pop')) return;
      event.preventDefault();
      close({ instant: true });
    }, true);

    document.addEventListener('keydown', function (event) {
      if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return;

      var target = event.target;
      if (!target || typeof target.closest !== 'function') return;
      var row = target.closest('.hub-row');
      var dialog = activeDialog || target.closest('dialog.hub-pop[open]');
      if (row || dialog) setInputMode(true);

      if (row && !dialog) {
        var rows = Array.prototype.slice.call(document.querySelectorAll('.hub-row'));
        var rowIndex = rows.indexOf(row);
        var nextIndex = rowIndex;
        if (event.key === 'ArrowUp') nextIndex = Math.max(0, rowIndex - 1);
        else if (event.key === 'ArrowDown') nextIndex = Math.min(rows.length - 1, rowIndex + 1);
        else if (event.key === 'Home') nextIndex = 0;
        else if (event.key === 'End') nextIndex = rows.length - 1;
        else return;

        event.preventDefault();
        if (rows[nextIndex]) rows[nextIndex].focus({ preventScroll: true });
        return;
      }

      var tile = target.closest('.hub-tile');
      if (!dialog || !tile || (event.key !== 'ArrowUp' && event.key !== 'ArrowDown')) return;

      var tiles = Array.prototype.slice.call(dialog.querySelectorAll('.hub-tile'));
      var tileIndex = tiles.indexOf(tile);
      if (tileIndex < 0) return;
      event.preventDefault();
      var tileNextIndex = event.key === 'ArrowUp'
        ? Math.max(0, tileIndex - 1)
        : Math.min(tiles.length - 1, tileIndex + 1);
      if (tiles[tileNextIndex]) tiles[tileNextIndex].focus({ preventScroll: true });
    });

    document.addEventListener('pointermove', function (event) {
      var target = event.target;
      if (!target || typeof target.closest !== 'function') return;
      var row = target.closest('.hub-row');
      if (!row || haloDisabled(event)) return;
      setInputMode(false);
      row.setAttribute('data-spot-active', '');
      moveSpot(row, event);
    });

    document.addEventListener('pointerout', clearSpotForPointerOut);
    document.addEventListener('pointercancel', clearSpotForPointerOut);

    document.addEventListener('scalaris:glosa', function (event) {
      if (
        window.location
        && window.location.pathname === '/'
        && event.detail
        && event.detail.open
        && window.scalarisGlosa
        && window.scalarisGlosa.close
      ) {
        window.scalarisGlosa.close({ instant: true });
      }
    });
  }

  registerDelegatedListeners();
})();
