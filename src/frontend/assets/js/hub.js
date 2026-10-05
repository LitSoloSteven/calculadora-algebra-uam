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
  if (window.__scalarisHubKeysActive) return;
  window.__scalarisHubKeysActive = true;

  var ARROWS = { ArrowLeft: true, ArrowRight: true, ArrowUp: true, ArrowDown: true };

  function center(rect) {
    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
  }

  function pickTarget(current, tiles, key) {
    var currentRect = current.getBoundingClientRect();
    var currentCenter = center(currentRect);
    var rowTolerance = currentRect.height / 2;
    var best = null;
    var bestScore = Infinity;

    tiles.forEach(function (tile) {
      if (tile === current) return;
      var rect = tile.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return;
      var c = center(rect);
      var sameRow = Math.abs(c.y - currentCenter.y) < rowTolerance;
      var score;

      if (key === 'ArrowLeft' || key === 'ArrowRight') {
        if (!sameRow) return;
        var dx = c.x - currentCenter.x;
        if (key === 'ArrowRight' ? dx <= 0 : dx >= 0) return;
        score = Math.abs(dx);
      } else {
        if (sameRow) return;
        var dy = c.y - currentCenter.y;
        if (key === 'ArrowDown' ? dy <= 0 : dy >= 0) return;
        score = Math.abs(dy) * 1000 + Math.abs(c.x - currentCenter.x);
      }

      if (score < bestScore) {
        bestScore = score;
        best = tile;
      }
    });
    return best;
  }

  document.addEventListener('keydown', function (e) {
    if (!ARROWS[e.key] || e.defaultPrevented) return;
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var active = document.activeElement;
    if (!active || !active.classList || !active.classList.contains('hub-tile')) return;
    var tiles = Array.prototype.slice.call(document.querySelectorAll('.hub-tile'));
    var target = pickTarget(active, tiles, e.key);
    if (!target) return;
    e.preventDefault();
    target.focus();
  });
})();
