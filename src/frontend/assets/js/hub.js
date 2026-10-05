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
  function motionAllowed() {
    return window.scalarisMotionOK ? window.scalarisMotionOK() : true;
  }

  function selectPillar(pillarId, opts) {
    opts = opts || {};
    var stage = document.querySelector('.hub-stage');
    var tab = document.getElementById('hub-tab-' + pillarId);
    var panel = document.getElementById('hub-panel-' + pillarId);
    if (!tab || !panel) return;

    var instant = Boolean(opts.instant || !motionAllowed());
    if (instant && stage) {
      stage.setAttribute('data-instant', '');
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          stage.removeAttribute('data-instant');
        });
      });
    }

    var tabs = document.querySelectorAll('.hub-matrix .hub-row');
    for (var i = 0; i < tabs.length; i++) {
      var t = tabs[i];
      if (t === tab) {
        t.classList.add('is-active');
        t.setAttribute('aria-selected', 'true');
        t.setAttribute('tabindex', '0');
      } else {
        t.classList.remove('is-active');
        t.setAttribute('aria-selected', 'false');
        t.setAttribute('tabindex', '-1');
      }
    }

    var panels = document.querySelectorAll('.hub-aug .hub-panel');
    for (var j = 0; j < panels.length; j++) {
      var p = panels[j];
      if (p === panel) {
        p.classList.add('is-active');
        p.inert = false;
        p.removeAttribute('inert');
      } else {
        p.classList.remove('is-active');
        p.inert = true;
        p.setAttribute('inert', '');
      }
    }
  }

  window.scalarisHubSelect = selectPillar;

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.hub-row');
    if (!btn) return;
    var id = btn.id.replace(/^hub-tab-/, '');
    if (!id) return;
    var isKeyboard = (e.detail === 0);
    selectPillar(id, { instant: isKeyboard });
  });

  document.addEventListener('keydown', function (e) {
    if (e.defaultPrevented) return;
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;

    var active = document.activeElement;
    if (!active) return;

    var tabEl = active.closest ? active.closest('.hub-row') : null;
    var tileEl = active.closest ? active.closest('.hub-tile') : null;

    if (tabEl && tabEl.closest('.hub-matrix')) {
      var tabs = Array.prototype.slice.call(document.querySelectorAll('.hub-matrix .hub-row'));
      var tabIdx = tabs.indexOf(tabEl);
      if (tabIdx === -1) return;

      if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Home' || e.key === 'End') {
        var targetIdx;
        if (e.key === 'ArrowDown') {
          targetIdx = (tabIdx + 1) % tabs.length;
        } else if (e.key === 'ArrowUp') {
          targetIdx = (tabIdx - 1 + tabs.length) % tabs.length;
        } else if (e.key === 'Home') {
          targetIdx = 0;
        } else if (e.key === 'End') {
          targetIdx = tabs.length - 1;
        }
        var targetTab = tabs[targetIdx];
        if (targetTab && targetTab !== tabEl) {
          e.preventDefault();
          var id = targetTab.id.replace(/^hub-tab-/, '');
          selectPillar(id, { instant: true });
          targetTab.focus();
        }
      } else if (e.key === 'ArrowRight') {
        var activeTiles = Array.prototype.slice.call(
          document.querySelectorAll('.hub-panel.is-active .hub-tile')
        );
        if (activeTiles.length > 0) {
          e.preventDefault();
          activeTiles[0].focus();
        }
      }
    } else if (tileEl && tileEl.closest('.hub-panel.is-active')) {
      if (e.key === 'ArrowLeft') {
        var activeTab = document.querySelector('.hub-matrix .hub-row.is-active');
        if (activeTab) {
          e.preventDefault();
          activeTab.focus();
        }
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        var tiles = Array.prototype.slice.call(
          document.querySelectorAll('.hub-panel.is-active .hub-tile')
        );
        var tileIdx = tiles.indexOf(tileEl);
        if (tileIdx !== -1 && tiles.length > 0) {
          e.preventDefault();
          var nextTileIdx;
          if (e.key === 'ArrowDown') {
            nextTileIdx = (tileIdx + 1) % tiles.length;
          } else {
            nextTileIdx = (tileIdx - 1 + tiles.length) % tiles.length;
          }
          tiles[nextTileIdx].focus();
        }
      }
    }
  });
})();
