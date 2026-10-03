/**
 * Scalaris Geometry Visualizer — client-side helpers (F8a).
 *
 * Provides frame registration and instant restyle for the scalar slider,
 * plus cell-error marking. Zero server calls per frame.
 */
(function () {
  'use strict';

  var registry = {};  // wrapId -> { frames: [...], plotEl: null, reqFrame: null }

  /**
   * Register precomputed frames for a plotly figure wrapper.
   * @param {string} wrapId  - id of the wrapping div
   * @param {Array}  frames  - array of frame objects with {ku, ku_plus_v, k, k_exact}
   */
  function register(wrapId, frames) {
    registry[wrapId] = { frames: frames, plotEl: null, reqFrame: null };
  }

  /**
   * Find the .js-plotly-plot inside a wrapper div.
   */
  function _getPlotEl(wrapId) {
    var entry = registry[wrapId];
    if (!entry) return null;
    if (entry.plotEl && entry.plotEl.isConnected) return entry.plotEl;

    var wrap = document.getElementById(wrapId);
    if (!wrap) return null;
    var el = wrap.querySelector('.js-plotly-plot');
    if (el) entry.plotEl = el;
    return el;
  }

  /**
   * Set the visible frame by index (instant Plotly.restyle, no animation).
   * @param {string} wrapId
   * @param {number} idx - frame index (0..24)
   */
  function setFrame(wrapId, idx) {
    if (!window.Plotly) return;
    var entry = registry[wrapId];
    if (!entry || !entry.frames) return;
    var frame = entry.frames[idx];
    if (!frame) return;

    var el = _getPlotEl(wrapId);
    if (!el) return;

    var ku = frame.ku;
    var kupv = frame.ku_plus_v;
    var kLabel = frame.k_exact || String(frame.k);

    // Trace 0 = k·u, trace 2 = k·u + v
    // Update x, y (and z for 3D) data and name
    try {
      var dim = ku.length;
      if (dim === 2) {
        Plotly.restyle(el, {
          x: [[0, ku[0]], [0, kupv[0]]],
          y: [[0, ku[1]], [0, kupv[1]]],
          name: ['k\u00B7u (k=' + kLabel + ')', 'k\u00B7u + v']
        }, [0, 2]);
      } else if (dim === 3) {
        // In 3D we have pairs of traces per arrow (line + marker)
        // Trace 0,1 = k·u; Trace 2,3 = v; Trace 4,5 = k·u+v
        Plotly.restyle(el, { x: [[0, ku[0]]], y: [[0, ku[1]]], z: [[0, ku[2]]], name: ['k\u00B7u (k=' + kLabel + ')'] }, [0]);
        Plotly.restyle(el, { x: [[ku[0]]], y: [[ku[1]]], z: [[ku[2]]] }, [1]);
        Plotly.restyle(el, { x: [[0, kupv[0]]], y: [[0, kupv[1]]], z: [[0, kupv[2]]], name: ['k\u00B7u + v'] }, [4]);
        Plotly.restyle(el, { x: [[kupv[0]]], y: [[kupv[1]]], z: [[kupv[2]]] }, [5]);
      }
    } catch (e) {
      // Silently ignore restyle errors
    }
  }

  /**
   * Mark a cell as invalid (error border) or clear all marks.
   * @param {string|null} selector - CSS selector of the cell input, or null to clear all
   */
  function markInvalid(selector) {
    // Clear previous marks
    document.querySelectorAll('.geo-cell-error').forEach(function (el) {
      el.classList.remove('geo-cell-error');
      el.removeAttribute('aria-invalid');
    });

    if (!selector) return;

    var el = document.querySelector(selector);
    if (el) {
      var target = el.closest('.q-field__control') || el;
      target.classList.add('geo-cell-error');
      el.setAttribute('aria-invalid', 'true');
    }
  }

  // Delegated event listener for the slider
  document.addEventListener('input', function(e) {
    if (e.target && e.target.matches('input[type="range"][data-geo-slider]')) {
      var wrapId = e.target.getAttribute('data-geo-slider');
      var idx = parseInt(e.target.value, 10);
      var entry = registry[wrapId];
      if (entry && entry.frames && entry.frames[idx]) {
        var frame = entry.frames[idx];
        var kExact = frame.k_exact || String(frame.k);
        e.target.setAttribute('aria-valuetext', kExact);
        var row = e.target.closest('.geo-slider-row');
        if (row) {
          var labelEl = row.querySelector('.geo-slider-value');
          if (labelEl) labelEl.textContent = kExact;
        }
        
        if (entry.reqFrame) cancelAnimationFrame(entry.reqFrame);
        entry.reqFrame = requestAnimationFrame(function() {
          setFrame(wrapId, idx);
        });
      }
    }
  });

  // Expose public API
  window.scalarisGeo = {
    register: register,
    setFrame: setFrame,
    markInvalid: markInvalid,
  };
})();
