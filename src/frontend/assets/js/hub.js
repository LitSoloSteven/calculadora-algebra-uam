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
