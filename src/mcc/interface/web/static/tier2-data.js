/* Tier 2 platform pages — real API hydration (loading/error/empty/stale, no fake P&L) */
(function () {
  'use strict';

  var TIER2_PAGES = ['market-pulse', 'indicators', 'validation', 'execution', 'journal', 'performance', 'reports', 'settings'];
  var _selectedStrategy = null;
  var _selectedSymbol = 'NQ';

  function fetchJson(path, opts) {
    return fetch(path, opts).then(function (r) {
      return r.json().then(function (j) {
        return { ok: r.ok, status: r.status, j: j };
      });
    });
  }

  function mxBadge(cls, text) {
    return '<span class="badge badge-' + cls + '">' + text + '</span>';
  }

  function fmtUsd(n) {
    if (n == null || isNaN(n)) return '—';
    var sign = n >= 0 ? '+$' : '-$';
    return sign + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 2 });
  }

  function fmtPrice(n) {
    if (n == null || isNaN(n)) return '—';
    return Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtPct(pct) {
    if (pct == null || isNaN(pct)) return '—';
    var sign = pct >= 0 ? '+' : '';
    return sign + Number(pct).toFixed(2) + '%';
  }

  function verdictBadge(v) {
    if (!v) return mxBadge('neutral', '—');
    var c = v === 'GREEN' ? 'green' : v === 'RED' ? 'red' : 'amber';
    return mxBadge(c, v);
  }

  function statusBanner(type, title, body) {
    var colors = {
      loading: 'var(--mx-blue-soft)',
      error: 'var(--mx-red-bg)',
      empty: 'var(--mx-neutral-bg)',
      stale: 'var(--mx-amber-bg)'
    };
    return '<div class="live-banner" style="background:' + (colors[type] || colors.empty) + ';margin-bottom:12px">' +
      '<strong>' + title + '</strong><p style="font-size:12px;margin-top:4px">' + body + '</p></div>';
  }

  function setEl(id, html) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = html;
    return el;
  }

  function loadingBlock(msg) {
    return '<div style="padding:32px;text-align:center;color:var(--mx-muted)">' + (msg || 'Loading…') + '</div>';
  }

  function isStaleIso(iso, maxSec) {
    if (!iso) return true;
    maxSec = maxSec || 300;
    try {
      var ts = new Date(iso).getTime();
      return isNaN(ts) || (Date.now() - ts) / 1000 > maxSec;
    } catch (e) {
      return true;
    }
  }

  function plotSpark(id, y, color) {
    var el = document.getElementById(id);
    if (!el || typeof Plotly === 'undefined' || !y || !y.length) return;
    Plotly.newPlot(el, [{
      x: y.map(function (_, i) { return i; }),
      y: y,
      type: 'scatter',
      mode: 'lines',
      line: { color: color || '#1D4ED8', width: 1.5 }
    }], {
      paper_bgcolor: '#FFFFFF', plot_bgcolor: '#FFFFFF', margin: { t: 0, r: 0, b: 0, l: 0 },
      xaxis: { visible: false }, yaxis: { visible: false }, height: 40
    }, { displayModeBar: false, responsive: true });
  }

  function plotGauge(id, value, maxVal) {
    var el = document.getElementById(id);
    if (!el || typeof Plotly === 'undefined' || value == null) return;
    var pct = value / maxVal;
    Plotly.newPlot(el, [{
      type: 'indicator', mode: 'gauge+number', value: value,
      gauge: {
        axis: { range: [0, maxVal] },
        bar: { color: pct < 0.5 ? '#15803D' : pct < 0.8 ? '#B45309' : '#B91C1C' },
        bgcolor: '#E5E7EB', borderwidth: 0
      },
      number: { font: { size: 14 } }
    }], { paper_bgcolor: '#FFFFFF', margin: { t: 20, r: 20, b: 0, l: 20 }, height: 120 }, { displayModeBar: false });
  }

  /* ── Market Pulse ─────────────────────────────────────────────── */
  function hydrateMarketPulse() {
    var el = setEl('market-pulse-live', loadingBlock('Loading market pulse…'));
    if (!el) return;

    Promise.all([
      fetchJson('/api/market/snapshot').catch(function () { return { ok: false, j: {} }; }),
      fetchJson('/api/agents/market-pulse').catch(function () { return { ok: false, j: {} }; })
    ]).then(function (results) {
      var snapRes = results[0];
      var pulseRes = results[1];
      var snapWrap = snapRes.j || {};
      var snap = snapWrap.snapshot || {};
      var pulse = (pulseRes.j && pulseRes.j.snapshot) ? pulseRes.j.snapshot : null;
      var pulseStale = pulseRes.j && pulseRes.j.sync_status === 'awaiting_sync';
      var snapUnavailable = snapWrap.source === 'unavailable' || !snap.instruments || !snap.instruments.length;

      if (snapUnavailable && !pulse) {
        setEl('market-pulse-live', statusBanner('error', 'Market data unavailable',
          (snapWrap.error || 'Could not load /api/market/snapshot or /api/agents/market-pulse fallback.')));
        return;
      }

      var banners = '';
      if (pulseStale || isStaleIso(pulse && pulse.as_of)) {
        banners += statusBanner('stale', 'Data may be stale', 'Market pulse snapshot is older than expected. Verify before trading decisions.');
      }
      if (pulse && pulse.disclaimer) {
        banners += '<p style="font-size:11px;color:var(--mx-muted);margin-bottom:12px">' + pulse.disclaimer + '</p>';
      }

      var proxies = (pulse && pulse.proxies) || {};
      var sparks = [
        ['$TICK', proxies.tick, 'chart-tick-mp'],
        ['$TRIN', proxies.trin, 'chart-trin-mp'],
        ['$ADD', proxies.add, 'chart-add-mp'],
        ['$VOLD', proxies.vold, 'chart-vold-mp'],
        ['$VIX', pulse && pulse.vix ? pulse.vix.value : null, 'chart-vix-mp']
      ];
      var sc = '<div class="grid-5" style="margin-bottom:16px">';
      sparks.forEach(function (s) {
        var val = s[1];
        var display = val == null ? '—' : (s[0] === '$TRIN' || s[0] === '$VIX' ? val : (typeof val === 'number' && val > 0 && s[0] !== '$VOLD' ? '+' + val : val));
        sc += '<div class="sparkline-card"><div class="sparkline-label">' + s[0] + '</div>' +
          '<div class="sparkline-value mono">' + display + '</div>' +
          '<div id="' + s[2] + '" style="height:40px"></div>' +
          '<div class="sparkline-ts mono" style="font-size:10px;color:var(--mx-muted)">' +
          (pulse && pulse.as_of ? pulse.as_of.slice(0, 19) + ' UTC' : '—') + '</div></div>';
      });
      sc += '</div>';

      var regime = (pulse && pulse.regime) || '—';
      var regimeCls = regime === 'RISK-ON' ? 'green' : regime === 'RISK-OFF' ? 'red' : 'amber';
      var conf = (pulse && pulse.regime_confidence) || '—';
      var breadth = (pulse && pulse.breadth_score) != null ? pulse.breadth_score : '—';

      var instRows = '';
      if (snap.instruments && snap.instruments.length) {
        snap.instruments.forEach(function (q) {
          var chgCls = (q.change_pct || 0) >= 0 ? 'positive' : 'negative';
          instRows += '<tr><td><strong>' + (q.symbol || '—') + '</strong></td><td>' + (q.name || '—') + '</td>' +
            '<td class="mono">' + fmtPrice(q.price) + '</td><td class="mono ' + chgCls + '">' + fmtPct(q.change_pct) + '</td>' +
            '<td>' + (q.decision ? mxBadge(q.decision === 'GO' ? 'green' : q.decision === 'NO-GO' ? 'red' : 'amber', q.decision) : '—') + '</td></tr>';
        });
      } else {
        instRows = '<tr><td colspan="5" style="text-align:center;color:var(--mx-muted)">No instrument quotes — internals fallback only.</td></tr>';
      }

      var sourceLabel = snapWrap.source === 'live' ? 'LIVE' : (pulse ? 'PROXY' : 'DEGRADED');
      var html = banners +
        '<div class="card" style="margin-bottom:16px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">' +
        '<div class="card-title">Market Internals</div>' + mxBadge('blue', sourceLabel) + '</div>' + sc +
        '<div class="grid-2"><div><div class="badge badge-lg badge-' + regimeCls + '">' + regime + '</div>' +
        '<p style="margin-top:8px;font-weight:700">Confidence ' + conf + (typeof conf === 'number' ? '%' : '') + '</p>' +
        '<p style="font-size:12px;color:var(--mx-secondary)">Breadth score: <span class="mono">' + breadth + '</span></p></div>' +
        '<div><div id="chart-breadth-gauge-mp" style="height:140px"></div></div></div></div>' +
        '<div class="card table-wrap"><div class="card-title">Instrument Snapshot</div>' +
        '<table class="data-table"><thead><tr><th>Symbol</th><th>Name</th><th>Price</th><th>Change</th><th>Decision</th></tr></thead><tbody>' +
        instRows + '</tbody></table></div>';

      setEl('market-pulse-live', html);

      if (pulse && pulse.sparklines) {
        Object.keys(pulse.sparklines).forEach(function (k) {
          plotSpark('chart-' + k + '-mp', pulse.sparklines[k]);
        });
      }
      if (typeof breadth === 'number') plotGauge('chart-breadth-gauge-mp', breadth, 100);
    }).catch(function () {
      setEl('market-pulse-live', statusBanner('error', 'Request failed', 'Could not reach market pulse APIs.'));
    });
  }

  /* ── Indicators & Regime ──────────────────────────────────────── */
  function hydrateIndicators() {
    var el = setEl('indicators-regime-live', loadingBlock('Loading regime classification…'));
    if (!el) return;

    var sym = _selectedSymbol;
    Promise.all([
      fetchJson('/api/regime/current?symbol=' + encodeURIComponent(sym)),
      fetchJson('/api/market/bars?symbol=' + encodeURIComponent(sym) + '&timeframe=15m&limit=50')
    ]).then(function (results) {
      var regime = results[0].j || {};
      var barsWrap = results[1].j || {};
      if (!results[0].ok) {
        setEl('indicators-regime-live', statusBanner('error', 'Regime API error', 'GET /api/regime/current failed.'));
        return;
      }

      var demoTag = barsWrap.demo_labeled ? ' ' + mxBadge('amber', 'DEMO DATA') : '';
      var staleTag = regime.degraded ? ' ' + mxBadge('amber', 'DEGRADED') : '';
      var vol = regime.volatility_regime || 'NORMAL';
      var volCls = vol === 'HIGH' ? 'red' : vol === 'LOW' ? 'green' : 'amber';
      var trend = regime.trend_state || '—';
      var confPct = regime.confidence != null ? Math.round(regime.confidence * 100) + '%' : '—';

      var cap = document.getElementById('indicator-price-caption');
      if (cap && barsWrap.bars && barsWrap.bars.length) {
        var last = barsWrap.bars[barsWrap.bars.length - 1];
        var close = last.close;
        cap.textContent = sym + ' • 15m • ' + (barsWrap.demo_labeled ? 'DEMO ' : '') + fmtPrice(close) +
          ' • bars: ' + barsWrap.count + demoTag;
      } else if (cap) {
        cap.textContent = sym + ' • 15m • no bar data' + demoTag;
      }

      var barNote = '';
      if (!barsWrap.bars || !barsWrap.bars.length) {
        barNote = statusBanner('empty', 'No bar history', 'GET /api/market/bars returned empty — regime uses degraded classification.');
      } else if (barsWrap.demo_labeled) {
        barNote = statusBanner('stale', 'Demo bars', 'Bar series is labeled DEMO_DATA from provider fallback.');
      }

      var html = barNote +
        '<div class="grid-4">' +
        '<div class="regime-card ' + (vol === 'LOW' ? 'low' : vol === 'HIGH' ? 'high' : 'normal') + '">' +
        '<div style="display:flex;justify-content:space-between"><strong>' + sym + '</strong>' + mxBadge(volCls, vol) + staleTag + '</div>' +
        '<div style="margin:6px 0">' + mxBadge(volCls, trend) + ' <span class="mono">' + confPct + '</span></div>' +
        '<div class="regime-prob-bar"><div class="regime-prob-fill" style="width:' + confPct + ';background:var(--mx-' + volCls + '-text)"></div></div>' +
        '<p style="font-size:11px;color:var(--mx-muted);margin-top:8px">' + (regime.rationale || '—') + '</p>' +
        (regime.last_updated ? '<p class="mono" style="font-size:10px;color:var(--mx-muted)">Updated: ' + regime.last_updated + '</p>' : '') +
        '</div></div>';

      if (barsWrap.bars && barsWrap.bars.length) {
        html += '<div class="card table-wrap" style="margin-top:16px"><div class="card-title">Recent Bars (' + sym + ' • 15m)</div>' +
          '<table class="data-table"><thead><tr><th>Time</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Vol</th></tr></thead><tbody>';
        barsWrap.bars.slice(-8).forEach(function (b) {
          var ts = b.timestamp || b.ts || '—';
          html += '<tr><td class="mono">' + String(ts).slice(0, 19) + '</td><td class="mono">' + fmtPrice(b.open) +
            '</td><td class="mono">' + fmtPrice(b.high) + '</td><td class="mono">' + fmtPrice(b.low) +
            '</td><td class="mono">' + fmtPrice(b.close) + '</td><td class="mono">' + (b.volume || '—') + '</td></tr>';
        });
        html += '</tbody></table></div>';
      }

      setEl('indicators-regime-live', html);
    }).catch(function () {
      setEl('indicators-regime-live', statusBanner('error', 'Request failed', 'Could not load regime or bar data.'));
    });
  }

  function wireIndicatorTabs() {
    var tabs = document.getElementById('indicator-symbol-tabs');
    if (!tabs) return;
    tabs.querySelectorAll('.tab').forEach(function (btn) {
      btn.onclick = function () {
        tabs.querySelectorAll('.tab').forEach(function (t) { t.classList.remove('active'); });
        btn.classList.add('active');
        _selectedSymbol = btn.getAttribute('data-tv-symbol') || 'NQ';
        if (window.TradingViewMX) window.TradingViewMX.mount('tv-chart-indicators', _selectedSymbol, 420, true);
        hydrateIndicators();
      };
    });
  }

  /* ── Validation ───────────────────────────────────────────────── */
  function renderValidationDetail(result) {
    var el = document.getElementById('validation-detail-live');
    if (!el || !result) return;
    var wf = (result.walk_forward_folds || []).map(function (f) {
      var pnl = f.pnl != null ? f.pnl : 0;
      var cls = pnl >= 0 ? 'positive' : 'negative';
      var pass = pnl >= 0 ? mxBadge('green', 'PASS') : mxBadge('red', 'FAIL');
      return '<tr><td>' + f.fold + '</td><td class="mono ' + cls + '">' + fmtUsd(pnl) + '</td><td>' + pass + '</td></tr>';
    }).join('');

    el.innerHTML = '<div class="verdict-banner"><h3>VERDICT: ' + (result.verdict || '—') + '</h3>' +
      '<p>' + (result.rationale || '') + '</p></div>' +
      '<div class="stat-cards"><div class="stat-card"><div class="stat-card-label">OOS Profit Factor</div>' +
      '<div class="stat-card-value">' + (result.oos_profit_factor != null ? result.oos_profit_factor : '—') + '</div></div>' +
      '<div class="stat-card"><div class="stat-card-label">OOS Trade Count</div>' +
      '<div class="stat-card-value">' + (result.oos_trade_count != null ? result.oos_trade_count : '—') + '</div></div>' +
      '<div class="stat-card"><div class="stat-card-label">Probabilistic Sharpe</div>' +
      '<div class="stat-card-value">' + (result.probabilistic_sharpe != null ? result.probabilistic_sharpe : '—') + '</div></div>' +
      '<div class="stat-card"><div class="stat-card-label">Folds Passing</div>' +
      '<div class="stat-card-value">' + (result.folds_passing != null ? result.folds_passing : '—') + '</div></div></div>' +
      '<div class="card table-wrap" style="margin-top:16px"><table class="data-table"><thead><tr><th>Fold</th><th>Net P&amp;L</th><th>Pass/Fail</th></tr></thead><tbody>' +
      (wf || '<tr><td colspan="3" style="text-align:center;color:var(--mx-muted)">No fold data</td></tr>') +
      '</tbody></table></div>';
  }

  function runValidation(strategyId) {
    var detail = document.getElementById('validation-detail-live');
    if (detail) detail.innerHTML = loadingBlock('Running validation…');
    fetchJson('/api/validation/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy_id: strategyId })
    }).then(function (res) {
      if (!res.ok) {
        if (detail) detail.innerHTML = statusBanner('error', 'Validation failed', (res.j.detail || res.j.error || 'HTTP ' + res.status));
        return;
      }
      renderValidationDetail(res.j);
      hydrateValidation();
    }).catch(function () {
      if (detail) detail.innerHTML = statusBanner('error', 'Request failed', 'POST /api/validation/run failed.');
    });
  }

  function hydrateValidation() {
    var el = setEl('validation-live', loadingBlock('Loading strategies…'));
    if (!el) return;

    fetchJson('/api/strategies').then(function (res) {
      if (!res.ok) {
        setEl('validation-live', statusBanner('error', 'Strategies unavailable', 'GET /api/strategies failed.'));
        return;
      }
      var strategies = res.j.strategies || [];
      if (!strategies.length) {
        setEl('validation-live', statusBanner('empty', 'No strategies registered', 'Add strategies via Strategy Registry before running validation.'));
        return;
      }
      if (!_selectedStrategy) _selectedStrategy = strategies[0].strategy_id;

      var list = '<ul style="list-style:none">';
      strategies.forEach(function (s) {
        var sid = s.strategy_id || s.id;
        var selected = sid === _selectedStrategy;
        list += '<li data-strategy-id="' + sid + '" style="padding:10px;border-bottom:1px solid var(--mx-border);cursor:pointer;' +
          (selected ? 'background:var(--mx-blue-soft)' : '') + '"><strong>' + (s.name || sid) + '</strong> ' +
          verdictBadge(s.latest_verdict || s.status) +
          '<br><span class="mono" style="font-size:10px;color:var(--mx-muted)">' + sid + '</span></li>';
      });
      list += '</ul><button class="btn-primary" id="validation-run-btn" style="margin-top:12px;width:100%">Run Validation</button>' +
        '<p id="validation-run-status" style="font-size:11px;color:var(--mx-muted);margin-top:8px"></p>';

      setEl('validation-live', list);

      el.querySelectorAll('li[data-strategy-id]').forEach(function (li) {
        li.onclick = function () {
          _selectedStrategy = li.getAttribute('data-strategy-id');
          hydrateValidation();
        };
      });
      var btn = document.getElementById('validation-run-btn');
      if (btn) btn.onclick = function () { runValidation(_selectedStrategy); };
    }).catch(function () {
      setEl('validation-live', statusBanner('error', 'Request failed', 'Could not load strategies.'));
    });
  }

  /* ── Execution ────────────────────────────────────────────────── */
  function submitPaperOrder() {
    var statusEl = document.getElementById('paper-order-status');
    var body = {
      symbol: (document.getElementById('paper-symbol') || {}).value || 'NQ',
      side: (document.getElementById('paper-side') || {}).value || 'BUY',
      quantity: parseInt((document.getElementById('paper-qty') || {}).value, 10) || 1,
      order_type: 'MARKET'
    };
    if (statusEl) statusEl.textContent = 'Submitting…';
    fetchJson('/api/orders/paper', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }).then(function (res) {
      if (!res.ok) {
        if (statusEl) statusEl.innerHTML = '<span style="color:var(--mx-red-text)">' + (res.j.detail || 'Order rejected') + '</span>';
        return;
      }
      var labeled = res.j.labeled ? ' (' + res.j.labeled + ')' : '';
      if (statusEl) statusEl.innerHTML = '<span class="' + (res.j.status === 'FILLED' ? 'positive' : 'negative') + '">' +
        res.j.status + labeled + (res.j.reason ? ' — ' + res.j.reason : '') + '</span>';
      hydrateExecution();
    }).catch(function () {
      if (statusEl) statusEl.textContent = 'Paper order request failed.';
    });
  }

  function hydrateExecution() {
    var el = setEl('execution-live', loadingBlock('Loading paper execution state…'));
    if (!el) return;

    Promise.all([
      fetchJson('/api/orders'),
      fetchJson('/api/account/paper')
    ]).then(function (results) {
      var ordersRes = results[0];
      var acctRes = results[1];
      if (!ordersRes.ok && !acctRes.ok) {
        setEl('execution-live', statusBanner('error', 'Execution APIs unavailable', 'Could not load orders or paper account.'));
        return;
      }

      var orders = (ordersRes.j && ordersRes.j.orders) ? ordersRes.j.orders : [];
      var acct = acctRes.j || {};
      var simTag = acct.labeled === 'SIMULATED' ? mxBadge('amber', 'SIMULATED') : '';

      var orderRows = '';
      if (!orders.length) {
        orderRows = '<tr><td colspan="7" style="text-align:center;color:var(--mx-muted);padding:24px">No paper orders recorded.</td></tr>';
      } else {
        orders.slice(0, 20).forEach(function (o) {
          var sideCls = (o.side || '').toUpperCase() === 'BUY' ? 'positive' : 'negative';
          var stCls = o.status === 'FILLED' ? 'green' : o.status === 'REJECTED' ? 'red' : 'amber';
          orderRows += '<tr><td class="mono">' + (o.created_at || '—').slice(0, 19) + '</td><td>' + (o.symbol || '—') +
            '</td><td class="' + sideCls + '">' + (o.side || '—') + '</td><td>' + (o.quantity || '—') +
            '</td><td class="mono">' + (o.fill_price != null ? fmtPrice(o.fill_price) : '—') + '</td>' +
            '<td>PAPER</td><td>' + mxBadge(stCls, o.status || '—') + '</td></tr>';
        });
      }

      var html = statusBanner('stale', 'Paper mode only', 'Live execution disabled. All fills are SIMULATED — no fake open-position P&amp;L shown.') +
        '<div class="grid-3" style="margin-bottom:16px">' +
        '<div class="card"><div class="card-title">Paper Account</div>' + simTag +
        '<p style="font-size:12px;margin-top:8px">Equity: <span class="mono">' + fmtUsd(acct.equity) + '</span></p>' +
        '<p style="font-size:12px">Cash: <span class="mono">' + fmtUsd(acct.cash) + '</span></p>' +
        '<p style="font-size:12px">Day P&amp;L: <span class="mono">' + fmtUsd(acct.day_pnl) + '</span></p></div>' +
        '<div class="card" style="grid-column:span 2"><div class="card-title">Recent Orders</div>' +
        '<div class="table-wrap"><table class="data-table"><thead><tr><th>Time</th><th>Symbol</th><th>Side</th><th>Qty</th><th>Fill</th><th>Route</th><th>Status</th></tr></thead><tbody>' +
        orderRows + '</tbody></table></div></div></div>' +
        '<div class="card order-form"><div class="card-title">New Order (Paper)</div>' +
        '<div class="grid-4"><input id="paper-symbol" placeholder="Symbol" value="NQ" style="padding:8px;border:1px solid var(--mx-border);border-radius:6px">' +
        '<select id="paper-side" style="padding:8px;border:1px solid var(--mx-border);border-radius:6px"><option value="BUY">BUY</option><option value="SELL">SELL</option></select>' +
        '<input id="paper-qty" type="number" min="1" value="1" style="padding:8px;border:1px solid var(--mx-border);border-radius:6px">' +
        '<button class="btn-primary" id="paper-submit-btn">Submit Paper Order</button></div>' +
        '<p id="paper-order-status" style="font-size:11px;color:var(--mx-muted);margin-top:8px"></p></div>';

      setEl('execution-live', html);
      var btn = document.getElementById('paper-submit-btn');
      if (btn) btn.onclick = submitPaperOrder;
    }).catch(function () {
      setEl('execution-live', statusBanner('error', 'Request failed', 'Could not load execution data.'));
    });
  }

  /* ── Journal ──────────────────────────────────────────────────── */
  function submitJournalNote() {
    var statusEl = document.getElementById('journal-note-status');
    var body = {
      date: (document.getElementById('jnl-date') || {}).value || new Date().toISOString().slice(0, 10),
      symbol: (document.getElementById('jnl-symbol') || {}).value || '',
      strategy_id: (document.getElementById('jnl-strategy') || {}).value || '',
      setup: (document.getElementById('jnl-setup') || {}).value || '',
      execution_notes: (document.getElementById('jnl-notes') || {}).value || ''
    };
    if (statusEl) statusEl.textContent = 'Saving…';
    fetchJson('/api/journal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }).then(function (res) {
      if (!res.ok) {
        if (statusEl) statusEl.innerHTML = '<span style="color:var(--mx-red-text)">' + (res.j.detail || 'Save failed') + '</span>';
        return;
      }
      if (statusEl) statusEl.textContent = 'Note saved: ' + (res.j.entry_id || 'OK');
      hydrateJournal();
    }).catch(function () {
      if (statusEl) statusEl.textContent = 'Journal save failed.';
    });
  }

  function hydrateJournal() {
    var el = setEl('journal-live', loadingBlock('Loading journal entries…'));
    if (!el) return;

    fetchJson('/api/journal').then(function (res) {
      if (!res.ok) {
        setEl('journal-live', statusBanner('error', 'Journal unavailable', 'GET /api/journal failed.'));
        return;
      }
      var entries = res.j.entries || [];
      var rows = '';
      if (!entries.length) {
        rows = '<tr><td colspan="7" style="text-align:center;color:var(--mx-muted);padding:24px">No journal entries yet.</td></tr>';
      } else {
        entries.forEach(function (e) {
          rows += '<tr><td class="mono">' + (e.date || '—') + '</td><td>' + (e.symbol || '—') + '</td>' +
            '<td class="mono">' + (e.strategy_id || '—') + '</td><td>' + (e.setup || '—') + '</td>' +
            '<td style="max-width:240px;font-size:11px">' + (e.execution_notes || '—') + '</td>' +
            '<td>' + (e.tags || '—') + '</td><td class="mono">' + (e.entry_id || '—') + '</td></tr>';
        });
      }

      var html = '<div class="card table-wrap"><table class="data-table"><thead><tr>' +
        '<th>Date</th><th>Symbol</th><th>Strategy</th><th>Setup</th><th>Notes</th><th>Tags</th><th>Entry ID</th></tr></thead><tbody>' +
        rows + '</tbody></table></div>' +
        '<div class="card" style="margin-top:16px"><div class="card-title">New Note</div>' +
        '<div class="grid-3" style="margin-bottom:8px">' +
        '<input id="jnl-date" type="date" style="padding:8px;border:1px solid var(--mx-border);border-radius:6px">' +
        '<input id="jnl-symbol" placeholder="Symbol" style="padding:8px;border:1px solid var(--mx-border);border-radius:6px">' +
        '<input id="jnl-strategy" placeholder="Strategy ID" style="padding:8px;border:1px solid var(--mx-border);border-radius:6px"></div>' +
        '<input id="jnl-setup" placeholder="Setup tag" style="width:100%;padding:8px;border:1px solid var(--mx-border);border-radius:6px;margin-bottom:8px">' +
        '<textarea id="jnl-notes" placeholder="Execution notes…" rows="3" style="width:100%;padding:8px;border:1px solid var(--mx-border);border-radius:6px"></textarea>' +
        '<button class="btn-primary" id="jnl-save-btn" style="margin-top:8px">Save Note</button>' +
        '<p id="journal-note-status" style="font-size:11px;color:var(--mx-muted);margin-top:8px"></p></div>';

      setEl('journal-live', html);
      var btn = document.getElementById('jnl-save-btn');
      if (btn) btn.onclick = submitJournalNote;
    }).catch(function () {
      setEl('journal-live', statusBanner('error', 'Request failed', 'Could not load journal.'));
    });
  }

  /* ── Performance ────────────────────────────────────────────────── */
  function hydratePerformance() {
    var el = setEl('perf-stats-live', loadingBlock('Loading performance summary…'));
    if (!el) return;

    fetchJson('/api/performance/summary').then(function (res) {
      if (!res.ok) {
        setEl('perf-stats-live', statusBanner('error', 'Performance unavailable', 'GET /api/performance/summary failed.'));
        return;
      }
      var d = res.j || {};
      var empty = !d.trade_count;
      var label = d.labeled || (empty ? 'SIMULATED' : 'from_stored_orders');
      var labelBadge = mxBadge(empty || label === 'SIMULATED' ? 'amber' : 'blue', label.toUpperCase());

      var banners = labelBadge;
      if (empty) {
        banners += statusBanner('empty', 'No trade history', 'Performance metrics are SIMULATED placeholders until paper orders are recorded. No fabricated P&amp;L.');
      }

      var netCls = (d.daily_pnl || 0) >= 0 ? 'positive' : 'negative';
      var html = banners +
        '<div class="grid-4" style="margin-bottom:12px">' +
        '<div><span class="mono ' + netCls + '" style="font-size:18px;font-weight:800">' + fmtUsd(d.daily_pnl) + '</span>' +
        '<div style="font-size:10px;color:var(--mx-muted)">Daily P&amp;L</div></div>' +
        '<div><span class="mono" style="font-size:18px;font-weight:800">' + fmtUsd(d.weekly_pnl) + '</span>' +
        '<div style="font-size:10px;color:var(--mx-muted)">Weekly P&amp;L</div></div>' +
        '<div><span class="mono" style="font-size:18px;font-weight:800">' + (d.win_rate != null ? Math.round(d.win_rate * 100) + '%' : '—') + '</span>' +
        '<div style="font-size:10px;color:var(--mx-muted)">Win Rate</div></div>' +
        '<div><span class="mono" style="font-size:18px;font-weight:800">' + (d.trade_count != null ? d.trade_count : '—') + '</span>' +
        '<div style="font-size:10px;color:var(--mx-muted)">Trades</div></div></div>' +
        '<p class="mono" style="font-size:10px;color:var(--mx-muted)">As of: ' + (d.as_of || '—') + '</p>';

      setEl('perf-stats-live', html);

      var eqEl = document.getElementById('chart-equity-dd');
      if (eqEl && d.equity_curve && d.equity_curve.length && typeof Plotly !== 'undefined') {
        var dates = d.equity_curve.map(function (p) { return p.date; });
        var equity = d.equity_curve.map(function (p) { return p.equity; });
        var dd = d.drawdown_curve || d.equity_curve.map(function (p) { return p.drawdown; });
        Plotly.newPlot(eqEl, [
          { x: dates, y: equity, type: 'scatter', mode: 'lines', line: { color: '#1D4ED8', width: 2 }, name: 'Equity' },
          { x: dates, y: dd, type: 'scatter', mode: 'lines', fill: 'tozeroy', line: { color: '#FCA5A5' }, name: 'Drawdown' }
        ], {
          paper_bgcolor: '#FFFFFF', plot_bgcolor: '#FFFFFF', font: { color: '#5B6270', size: 10 },
          margin: { t: 10, r: 10, b: 30, l: 40 }, height: 280
        }, { displayModeBar: false, responsive: true });
      } else if (eqEl) {
        eqEl.innerHTML = '<p style="text-align:center;color:var(--mx-muted);padding:40px;font-size:12px">No equity curve data</p>';
      }
    }).catch(function () {
      setEl('perf-stats-live', statusBanner('error', 'Request failed', 'Could not load performance summary.'));
    });
  }

  /* ── Reports ──────────────────────────────────────────────────── */
  function generateReport() {
    var statusEl = document.getElementById('reports-gen-status');
    if (statusEl) statusEl.textContent = 'Generating…';
    fetchJson('/api/reports/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_type: 'DAILY_RESEARCH_BRIEF', title: 'Daily Research Brief', format: 'markdown' })
    }).then(function (res) {
      if (!res.ok) {
        if (statusEl) statusEl.innerHTML = '<span style="color:var(--mx-red-text)">' + (res.j.detail || 'Generate failed') + '</span>';
        return;
      }
      if (statusEl) statusEl.textContent = 'Report created: ' + (res.j.report_id || res.j.title || 'OK');
      hydrateReports();
    }).catch(function () {
      if (statusEl) statusEl.textContent = 'Report generation failed.';
    });
  }

  function hydrateReports() {
    var el = setEl('reports-live', loadingBlock('Loading reports…'));
    if (!el) return;

    fetchJson('/api/reports').then(function (res) {
      if (!res.ok) {
        setEl('reports-live', statusBanner('error', 'Reports unavailable', 'GET /api/reports failed.'));
        return;
      }
      var reports = res.j.reports || [];
      var rows = '';
      if (!reports.length) {
        rows = '<tr><td colspan="4" style="text-align:center;color:var(--mx-muted);padding:24px">No reports generated yet.</td></tr>';
      } else {
        reports.forEach(function (r) {
          rows += '<tr><td><strong>' + (r.title || r.report_id || '—') + '</strong><br>' +
            '<span style="font-size:10px;color:var(--mx-muted)">' + (r.report_type || '') + '</span></td>' +
            '<td>' + mxBadge('blue', (r.format || 'md').toUpperCase()) + '</td>' +
            '<td class="mono">' + (r.created_at || '—').slice(0, 19) + '</td>' +
            '<td>' + mxBadge('green', 'COMPLETED') + '</td></tr>';
        });
      }

      var html = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">' +
        '<div class="card-title">Generated Reports</div>' +
        '<button class="btn-primary" id="reports-gen-btn">Generate Report</button></div>' +
        '<div class="table-wrap"><table class="data-table"><thead><tr><th>Report</th><th>Format</th><th>Generated</th><th>Status</th></tr></thead><tbody>' +
        rows + '</tbody></table></div>' +
        '<p id="reports-gen-status" style="font-size:11px;color:var(--mx-muted);margin-top:8px"></p>';

      setEl('reports-live', html);
      var btn = document.getElementById('reports-gen-btn');
      if (btn) btn.onclick = generateReport;
    }).catch(function () {
      setEl('reports-live', statusBanner('error', 'Request failed', 'Could not load reports.'));
    });
  }

  /* ── Settings ─────────────────────────────────────────────────── */
  function statusDotClass(status) {
    if (status === 'NOMINAL' || status === 'fresh' || status === 'PRESENT' || status === 'ok') return 'green';
    if (status === 'STALE' || status === 'stale' || status === 'DEGRADED') return 'amber';
    if (status === 'LOCKED' || status === 'missing' || status === 'MISSING') return 'red';
    return 'neutral';
  }

  function hydrateSettings() {
    var el = setEl('settings-live', loadingBlock('Loading system configuration…'));
    if (!el) return;

    Promise.all([
      fetchJson('/config-check'),
      fetchJson('/api/system-state'),
      fetchJson('/api/data-freshness')
    ]).then(function (results) {
      var cfg = results[0].j || {};
      var state = results[1].j || {};
      var fresh = results[2].j || {};

      if (!results[0].ok && !results[1].ok) {
        setEl('settings-live', statusBanner('error', 'Settings unavailable', 'Could not load config or system state.'));
        return;
      }

      var sysStatus = state.status || 'DEGRADED';
      var statusCls = statusDotClass(sysStatus);
      var statusLabels = {
        NOMINAL: 'SYSTEM NOMINAL',
        DEGRADED: 'SYSTEM DEGRADED',
        STALE: 'DATA STALE',
        LOCKED: 'SYSTEM LOCKED'
      };

      var cfgRows = '';
      (cfg.checks || []).forEach(function (c) {
        var cls = c.presence === 'PRESENT' ? 'green' : 'red';
        cfgRows += '<tr><td class="mono">' + c.name + '</td><td>' + mxBadge(cls, c.presence) +
          '</td><td>' + c.level + '</td></tr>';
      });

      var feedRows = '';
      var sources = fresh.sources || {};
      Object.keys(sources).forEach(function (key) {
        var s = sources[key];
        var cls = statusDotClass(s.status);
        feedRows += '<tr><td>' + key.replace(/_/g, ' ') + '</td><td>' + mxBadge(cls, (s.status || '—').toUpperCase()) +
          '</td><td class="mono">' + (s.max_age_seconds != null ? s.max_age_seconds + 's' : '—') + '</td>' +
          '<td style="font-size:11px">' + (s.message || s.detail || '—') + '</td></tr>';
      });

      var detail = state.status_detail || {};
      var html = '<div class="card" style="margin-bottom:16px"><div style="display:flex;align-items:center;gap:8px">' +
        '<span class="status-dot ' + statusCls + '"></span><strong>' + (statusLabels[sysStatus] || sysStatus) + '</strong>' +
        (state.message ? '<span style="font-size:11px;color:var(--mx-muted)"> — ' + state.message + '</span>' : '') +
        '</div><p style="font-size:11px;color:var(--mx-muted);margin-top:8px">Live execution: ' +
        (detail.live_execution_enabled ? mxBadge('red', 'ENABLED') : mxBadge('green', 'DISABLED')) +
        ' &nbsp; Paper: ' + (detail.paper_trading_enabled !== false ? mxBadge('blue', 'ENABLED') : mxBadge('neutral', 'OFF')) +
        '</p></div>' +
        '<div class="grid-2" style="margin-bottom:16px">' +
        '<div class="card table-wrap"><div class="card-title">Config Check</div>' +
        '<table class="data-table"><thead><tr><th>Variable</th><th>Presence</th><th>Level</th></tr></thead><tbody>' +
        (cfgRows || '<tr><td colspan="3" style="text-align:center;color:var(--mx-muted)">No checks</td></tr>') +
        '</tbody></table><p style="font-size:10px;color:var(--mx-muted);margin-top:8px">Env: ' + (cfg.environment || '—') +
        ' &nbsp; OK: ' + (cfg.ok ? 'yes' : 'no') + '</p></div>' +
        '<div class="card table-wrap"><div class="card-title">Data Freshness</div>' +
        '<table class="data-table"><thead><tr><th>Source</th><th>Status</th><th>Max Age</th><th>Detail</th></tr></thead><tbody>' +
        (feedRows || '<tr><td colspan="4" style="text-align:center;color:var(--mx-muted)">No freshness data</td></tr>') +
        '</tbody></table>' +
        (fresh.critical_stale ? statusBanner('stale', 'Critical stale sources', 'One or more critical data sources are stale or missing.') : '') +
        '</div></div>';

      if (state.agents) {
        html += '<div class="card table-wrap"><div class="card-title">Agent Fleet (' + (state.agents.count || '—') + ')</div>' +
          '<p style="font-size:12px;color:var(--mx-muted)">Working: ' + (state.agents.working || 0) +
          ' &nbsp; Idle: ' + (state.agents.idle || 0) + ' &nbsp; Error: ' + (state.agents.error || 0) + '</p></div>';
      }

      setEl('settings-live', html);
    }).catch(function () {
      setEl('settings-live', statusBanner('error', 'Request failed', 'Could not load settings APIs.'));
    });
  }

  /* ── Router ───────────────────────────────────────────────────── */
  function hydrate(page) {
    page = page || 'home';
    if (TIER2_PAGES.indexOf(page) === -1) return;

    if (page === 'market-pulse') hydrateMarketPulse();
    if (page === 'indicators') {
      wireIndicatorTabs();
      if (window.TradingViewMX) window.TradingViewMX.mount('tv-chart-indicators', _selectedSymbol, 420);
      hydrateIndicators();
    }
    if (page === 'validation') hydrateValidation();
    if (page === 'execution') hydrateExecution();
    if (page === 'journal') hydrateJournal();
    if (page === 'performance') hydratePerformance();
    if (page === 'reports') hydrateReports();
    if (page === 'settings') hydrateSettings();
  }

  window.Tier2Data = { hydrate: hydrate };
})();