/* Research Lab / Backtest — real API wiring */
(function () {
  'use strict';

  function hydrate() {
    var el = document.getElementById('research-live');
    if (!el) return;
    el.innerHTML = '<div class="card"><div class="card-title">Backtest Runner</div><p style="font-size:12px;color:var(--mx-muted)">Loading…</p></div>';
    fetch('/api/strategies').then(function (r) { return r.json(); }).then(function (j) {
      var opts = (j.strategies || []).map(function (s) {
        return '<option value="' + s.strategy_id + '">' + s.name + ' (' + s.strategy_id + ')</option>';
      }).join('');
      el.innerHTML = '<div class="card"><div class="card-title">Backtest Runner</div>' +
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px">' +
        '<select id="bt-strategy">' + (opts || '<option value="">No strategies</option>') + '</select>' +
        '<input id="bt-symbol" placeholder="Symbol" value="NQ" style="padding:8px">' +
        '<input id="bt-equity" placeholder="Initial equity" value="100000" style="padding:8px">' +
        '</div><label style="font-size:11px"><input type="checkbox" id="bt-demo"> Use labeled DEMO DATA if no bars</label>' +
        '<div style="margin-top:12px"><button class="btn-primary" id="bt-run">Run Backtest</button></div>' +
        '<div id="bt-result" style="margin-top:16px;font-size:12px"></div></div>';
      var btn = document.getElementById('bt-run');
      if (btn) btn.addEventListener('click', runBacktest);
    }).catch(function () {
      el.innerHTML = '<div class="card" style="color:var(--mx-red-text)">Failed to load backtest UI.</div>';
    });
  }

  function runBacktest() {
    var result = document.getElementById('bt-result');
    if (!result) return;
    result.textContent = 'Running…';
    var body = {
      strategy_id: (document.getElementById('bt-strategy') || {}).value,
      symbol: (document.getElementById('bt-symbol') || {}).value || 'NQ',
      initial_equity: parseFloat((document.getElementById('bt-equity') || {}).value) || 100000,
      use_demo_data: !!(document.getElementById('bt-demo') || {}).checked
    };
    fetch('/api/backtests/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) {
          result.innerHTML = '<span style="color:var(--mx-red-text)">' + (res.j.detail || res.j.message || 'Error') + '</span>';
          return;
        }
        var j = res.j;
        var demo = j.demo_labeled ? ' <span class="badge badge-amber">DEMO DATA</span>' : '';
        result.innerHTML = '<strong>Run #' + (j.backtest_run_id || '—') + '</strong>' + demo +
          '<br>Trades: ' + j.total_trades + ' | Win rate: ' + (j.win_rate * 100).toFixed(1) + '%' +
          ' | Net P&amp;L: $' + j.net_pnl + ' | Max DD: $' + j.max_drawdown +
          '<br>Config hash: <span class="mono">' + j.config_hash + '</span>';
      }).catch(function () { result.textContent = 'Backtest request failed.'; });
  }

  window.BacktestData = { hydrate: hydrate };
})();