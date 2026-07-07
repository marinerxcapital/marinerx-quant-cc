/* Risk Command — real API wiring */
(function () {
  'use strict';

  function hydrate() {
    var el = document.getElementById('risk-metrics-live');
    if (!el) return;
    el.innerHTML = '<div class="card"><p>Loading risk state…</p></div>';
    fetch('/api/risk/state').then(function (r) { return r.json(); }).then(function (s) {
      var kill = s.kill_switch_active ? '<span class="badge badge-red">KILL SWITCH ACTIVE</span>' : '<span class="badge badge-green">Kill switch off</span>';
      var live = s.live_execution_enabled ? 'ENABLED' : 'DISABLED';
      el.innerHTML = '<div class="card"><div class="card-title">Risk State</div>' + kill +
        '<ul class="kv-list"><li><span class="kv-key">Day P&amp;L</span><span class="kv-val mono">$' + (s.current_day_pnl || 0) + '</span></li>' +
        '<li><span class="kv-key">Daily loss remaining</span><span class="kv-val mono">$' + (s.daily_loss_remaining || 0).toFixed(0) + '</span></li>' +
        '<li><span class="kv-key">Drawdown headroom</span><span class="kv-val mono">$' + (s.drawdown_headroom || 0).toFixed(0) + '</span></li>' +
        '<li><span class="kv-key">Paper trading</span><span class="kv-val">' + (s.paper_trading_enabled ? 'ON' : 'OFF') + '</span></li>' +
        '<li><span class="kv-key">Live execution</span><span class="kv-val">' + live + ' (NOT LIVE)</span></li>' +
        '<li><span class="kv-key">Last updated</span><span class="kv-val mono">' + (s.last_updated || '—') + '</span></li></ul>' +
        '<div style="margin-top:12px;display:flex;gap:8px">' +
        '<button class="btn-kill" id="risk-kill-on">Activate Kill Switch</button>' +
        '<button class="btn-secondary" id="risk-kill-off">Clear Kill Switch</button></div></div>';
      var on = document.getElementById('risk-kill-on');
      var off = document.getElementById('risk-kill-off');
      if (on) on.addEventListener('click', function () { fetch('/api/risk/kill-switch', { method: 'POST' }).then(function () { hydrate(); }); });
      if (off) off.addEventListener('click', function () { fetch('/api/risk/clear-kill-switch', { method: 'POST' }).then(function () { hydrate(); }); });
    }).catch(function () {
      el.innerHTML = '<div class="card" style="color:var(--mx-red-text)">Failed to load risk state.</div>';
    });
  }

  window.RiskData = { hydrate: hydrate };
})();