/* Header system truth — polls /api/system-state (no hardcoded NOMINAL). */
(function () {
  'use strict';

  var POLL_MS = 10000;
  var _timer = null;

  var STATUS_CLASS = {
    NOMINAL: 'green',
    DEGRADED: 'amber',
    STALE: 'amber',
    LOCKED: 'red'
  };

  var STATUS_TEXT = {
    NOMINAL: 'SYSTEM NOMINAL',
    DEGRADED: 'SYSTEM DEGRADED',
    STALE: 'DATA STALE',
    LOCKED: 'SYSTEM LOCKED'
  };

  function fetchJson(path) {
    return fetch(path).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function fmtUsd(n) {
    if (n == null || isNaN(n)) return '—';
    var sign = n >= 0 ? '+$' : '-$';
    return sign + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
  }

  function hydrateHeader(state) {
    var statusHdr = document.querySelector('.header-status');
    if (statusHdr) {
      var label = state.status || 'DEGRADED';
      var dotClass = STATUS_CLASS[label] || 'amber';
      var text = STATUS_TEXT[label] || ('STATUS ' + label);
      statusHdr.innerHTML = '<span class="status-dot ' + dotClass + '"></span> ' + text;
      if (state.message) {
        statusHdr.title = state.message;
      }
    }

    var metrics = document.querySelectorAll('.header-metric');
    var hm = state.header_metrics || {};
    if (metrics[0]) {
      var dayEl = metrics[0].querySelector('.header-metric-value');
      if (dayEl) {
        if (hm.day_pnl != null) {
          dayEl.textContent = fmtUsd(hm.day_pnl);
          dayEl.className = 'header-metric-value ' + (hm.day_pnl >= 0 ? 'positive' : 'negative');
        } else {
          dayEl.textContent = '—';
          dayEl.className = 'header-metric-value';
        }
      }
    }
    if (metrics[1]) {
      var weekEl = metrics[1].querySelector('.header-metric-value');
      if (weekEl) {
        if (hm.week_pnl != null) {
          weekEl.textContent = fmtUsd(hm.week_pnl);
          weekEl.className = 'header-metric-value ' + (hm.week_pnl >= 0 ? 'positive' : 'negative');
        } else {
          weekEl.textContent = '—';
          weekEl.className = 'header-metric-value';
        }
      }
    }
    if (metrics[2]) {
      var headEl = metrics[2].querySelector('.header-metric-value');
      if (headEl) {
        if (hm.drawdown_headroom != null) {
          headEl.textContent = '$' + Math.round(hm.drawdown_headroom).toLocaleString();
          headEl.className = 'header-metric-value';
        } else {
          headEl.textContent = 'Awaiting sync';
          headEl.className = 'header-metric-value';
        }
      }
    }
  }

  function showLoading() {
    var statusHdr = document.querySelector('.header-status');
    if (statusHdr) {
      statusHdr.innerHTML = '<span class="status-dot neutral"></span> CHECKING SYSTEM STATE…';
    }
  }

  function showError() {
    var statusHdr = document.querySelector('.header-status');
    if (statusHdr) {
      statusHdr.innerHTML = '<span class="status-dot red"></span> SYSTEM STATE UNAVAILABLE';
    }
  }

  function poll() {
    fetchJson('/api/system-state')
      .then(hydrateHeader)
      .catch(showError);
  }

  function start() {
    showLoading();
    poll();
    if (_timer) clearInterval(_timer);
    _timer = setInterval(poll, POLL_MS);
  }

  window.SystemState = { start: start, poll: poll };
})();