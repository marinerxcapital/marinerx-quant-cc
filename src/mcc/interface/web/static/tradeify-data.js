/* Tradeify / Tradovate connector telemetry — polls /api/tradeify/150k/data/* */
(function () {
  'use strict';

  var API = '/api/tradeify/150k';
  var POLL_MS = 30000;
  var STALE_WARN_SEC = 60;
  var STALE_BLOCK_SEC = 180;

  var _timer = null;
  var _syncBound = false;
  var _cache = {
    health: null,
    latest: null,
    status: null,
    reconcile: null,
    eval: null,
    payout: null
  };

  function fetchJson(path, opts) {
    return fetch(path, opts).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function postJson(path, body) {
    return fetchJson(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {})
    });
  }

  function fmtUsd(n) {
    if (n == null || isNaN(n)) return '—';
    var sign = n >= 0 ? '+$' : '-$';
    return sign + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
  }

  function fmtTs(iso) {
    if (!iso) return '—';
    try {
      return new Date(iso).toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
    } catch (e) {
      return '—';
    }
  }

  function ageSeconds(iso) {
    if (!iso) return null;
    var t = Date.parse(iso);
    if (isNaN(t)) return null;
    return Math.max(0, Math.floor((Date.now() - t) / 1000));
  }

  function connectorBadge(state) {
    var s = String(state || '').toLowerCase();
    if (s === 'connected' || s === 'healthy' || s === 'ok' || s === 'active' || s === 'success') {
      return { cls: 'green', text: 'CONNECTED' };
    }
    if (s === 'pending_implementation' || s === 'scaffold_ready' || s === 'configured' || s === 'not_implemented' || s === 'not_available') {
      return { cls: 'amber', text: 'PENDING' };
    }
    if (s === 'disabled' || s === 'not_configured') {
      return { cls: 'neutral', text: 'NOT CONFIGURED' };
    }
    return { cls: 'red', text: String(state || 'UNKNOWN').toUpperCase().replace(/_/g, ' ') };
  }

  function gateBadge(decision) {
    var d = String(decision || '').toUpperCase();
    if (d === 'ALLOW') return { cls: 'green', text: 'ALLOW' };
    if (d === 'REDUCE_SIZE') return { cls: 'amber', text: 'REDUCE SIZE' };
    if (d === 'FLATTEN') return { cls: 'red', text: 'FLATTEN' };
    return { cls: 'red', text: d || 'BLOCK' };
  }

  function staleLevel(seconds) {
    if (seconds == null) return { level: 'unknown', label: 'Sync age unknown', cls: 'amber' };
    if (seconds <= 15) return { level: 'fresh', label: 'Data fresh (' + seconds + 's)', cls: 'green' };
    if (seconds <= STALE_WARN_SEC) return { level: 'caution', label: 'Data aging (' + seconds + 's) — confirm before staging', cls: 'amber' };
    if (seconds <= STALE_BLOCK_SEC) return { level: 'warn', label: 'Stale (' + seconds + 's) — new trades blocked', cls: 'amber' };
    return { level: 'stale', label: 'Data stale (' + seconds + 's) — trading actions disabled', cls: 'red' };
  }

  function reconciliationOk(rec) {
    if (!rec) return null;
    var status = String(rec.status || rec.reconciliation || '').toLowerCase();
    if (status === 'ok' || status === 'matched' || status === 'success') return true;
    if (status === 'not_implemented' || status === 'unavailable' || status === 'pending') return null;
    return false;
  }

  function snapshotFromLatest(latest) {
    if (!latest) return null;
    return latest.snapshot || latest.account_snapshot || latest.merged_snapshot || null;
  }

  function gateFromLatest(latest) {
    if (!latest) return null;
    return latest.gate_result || latest.gate || latest.trade_gate || null;
  }

  function mxBadge(cls, text) {
    return '<span class="badge badge-' + cls + '">' + text + '</span>';
  }

  function renderConnectorCards(health, status, latest) {
    var tradovate = health && health.tradovate_connector;
    var dashboard = health && health.tradeify_dashboard_connector;
    var tv = connectorBadge(tradovate);
    var td = connectorBadge(dashboard);
    var observed = (latest && latest.observed_at) || (health && health.observed_at) || (status && status.observed_at);
    var age = ageSeconds(observed);
    var stale = staleLevel(age);
    var rec = _cache.reconcile;
    var recOk = reconciliationOk(rec);
    var recBadge = recOk === true ? mxBadge('green', 'MATCHED') :
      recOk === false ? mxBadge('red', 'MISMATCH') : mxBadge('amber', 'UNAVAILABLE');

    var staleBanner = '';
    if (stale.level !== 'fresh' && stale.level !== 'unknown') {
      staleBanner = '<div class="live-banner" style="background:var(--mx-' + stale.cls + '-bg);border:1px solid var(--mx-' + stale.cls + '-text);color:var(--mx-primary);margin-bottom:12px">' +
        '<strong>Stale Data Warning</strong><p>' + stale.label + '</p></div>';
    }

    var reconnectNote = '';
    if (dashboard && String(dashboard).toLowerCase().indexOf('pending') >= 0) {
      reconnectNote = '<p style="font-size:11px;color:var(--mx-muted);margin-top:8px">Tradeify dashboard session not connected. Run local sync with headed browser + 2FA to establish storage_state, then retry sync.</p>';
    } else if (status && !status.tradeify_dashboard_enabled) {
      reconnectNote = '<p style="font-size:11px;color:var(--mx-muted);margin-top:8px">Dashboard connector disabled (MARINERX_TRADEIFY_DASHBOARD_ENABLED=false). Enable after local session validation.</p>';
    }

    return staleBanner +
      '<div class="section-header" style="margin-bottom:12px"><div class="section-title">Tradeify 150K Data Connectors</div>' +
      mxBadge(status && status.mode ? 'blue' : 'neutral', (status && status.mode) || 'PAPER_FIRST') + '</div>' +
      '<div class="grid-2" style="margin-bottom:12px">' +
      '<div class="card" style="margin:0"><div class="card-title">Tradovate API</div>' + mxBadge(tv.cls, tv.text) +
      '<p style="font-size:11px;color:var(--mx-muted);margin-top:8px">Broker positions, balance, fills, and realized P&amp;L.</p>' +
      '<ul class="kv-list" style="margin-top:8px"><li><span class="kv-key">Connector</span><span class="kv-val mono">' + (tradovate || '—') + '</span></li>' +
      '<li><span class="kv-key">Enabled</span><span class="kv-val">' + (status && status.tradovate_enabled ? 'Yes' : 'No') + '</span></li></ul></div>' +
      '<div class="card" style="margin:0"><div class="card-title">Tradeify Dashboard</div>' + mxBadge(td.cls, td.text) +
      '<p style="font-size:11px;color:var(--mx-muted);margin-top:8px">Prop-firm phase, winning days, payout progress, drawdown floor.</p>' +
      '<ul class="kv-list" style="margin-top:8px"><li><span class="kv-key">Connector</span><span class="kv-val mono">' + (dashboard || '—') + '</span></li>' +
      '<li><span class="kv-key">Enabled</span><span class="kv-val">' + (status && status.tradeify_dashboard_enabled ? 'Yes' : 'No') + '</span></li></ul>' +
      reconnectNote + '</div></div>' +
      '<div class="grid-3" style="margin-bottom:12px">' +
      '<div class="stat-card"><div class="stat-card-label">Last Snapshot</div><div class="stat-card-value" style="font-size:13px">' + fmtTs(observed) + '</div></div>' +
      '<div class="stat-card"><div class="stat-card-label">Reconciliation</div><div style="margin-top:6px">' + recBadge + '</div></div>' +
      '<div class="stat-card"><div class="stat-card-label">Safe Default</div><div class="stat-card-value" style="font-size:12px">' + ((health && health.safe_default) || 'BLOCK_NEW_TRADES') + '</div></div></div>' +
      '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">' +
      '<button type="button" class="btn-primary" id="tradeify-sync-btn">Manual Sync</button>' +
      '<span id="tradeify-sync-status" style="font-size:11px;color:var(--mx-muted)">Pull Tradovate + Tradeify metrics and refresh cache.</span></div>';
  }

  function hydrateSettings() {
    var el = document.getElementById('tradeify-connector-live');
    if (!el) return;

    Promise.all([
      fetchJson(API + '/data/status').catch(function () { return null; }),
      postJson(API + '/data/reconcile', {}).catch(function () { return null; })
    ]).then(function (results) {
      _cache.status = results[0];
      _cache.reconcile = results[1];
      el.innerHTML = renderConnectorCards(_cache.health, _cache.status, _cache.latest);
      wireSyncButton();
      updateFeedTableRow();
    });
  }

  function updateFeedTableRow() {
    var rows = document.querySelectorAll('.data-table tbody tr');
    rows.forEach(function (row) {
      var first = row.querySelector('td');
      if (!first) return;
      if (first.textContent.trim() === 'Tradovate') {
        var badge = row.querySelector('.badge');
        var lat = row.querySelector('td.mono');
        var tv = connectorBadge(_cache.health && _cache.health.tradovate_connector);
        if (badge) {
          badge.className = 'badge badge-' + tv.cls;
          badge.textContent = tv.text === 'CONNECTED' ? 'CONNECTED' : tv.text;
        }
        if (lat && _cache.latest && _cache.latest.observed_at) {
          var age = ageSeconds(_cache.latest.observed_at);
          lat.textContent = age != null ? age + 's ago' : '—';
        }
      }
      if (first.textContent.trim() === 'Tradeify Sync') {
        var badge2 = row.querySelector('.badge');
        var lat2 = row.querySelector('td.mono');
        var td = connectorBadge(_cache.health && _cache.health.tradeify_dashboard_connector);
        if (badge2) {
          badge2.className = 'badge badge-' + td.cls;
          badge2.textContent = td.text === 'CONNECTED' ? 'SYNCED' : td.text;
        }
        if (lat2 && _cache.latest && _cache.latest.observed_at) {
          var age2 = ageSeconds(_cache.latest.observed_at);
          lat2.textContent = age2 != null ? age2 + 's ago' : '—';
        }
      }
    });
  }

  function renderRiskPanel(latest, health) {
    var snap = snapshotFromLatest(latest);
    var gate = gateFromLatest(latest);
    var headroom = snap && (snap.drawdown_headroom != null ? snap.drawdown_headroom :
      (snap.balance != null && snap.eod_drawdown_floor != null ? snap.balance - snap.eod_drawdown_floor : null));
    var dailyPnl = snap && snap.realized_day_pnl;
    var decision = gate && (gate.decision || gate.trade_decision);
    var reason = gate && (gate.reason || gate.block_reason);
    var gb = gateBadge(decision || (health && health.safe_default === 'BLOCK_NEW_TRADES' ? 'BLOCK' : '—'));
    var stale = staleLevel(ageSeconds(latest && latest.observed_at));

    if (!snap && latest && latest.status === 'not_available') {
      return '<div class="card-title">Tradeify 150K Trade Gate</div>' +
        mxBadge('amber', 'NO SNAPSHOT') +
        '<p style="font-size:12px;margin:12px 0;color:var(--mx-muted)">' + (latest.message || 'Awaiting first successful sync.') + '</p>' +
        '<p style="font-size:11px">Safe default: <strong>' + (latest.safe_default || 'BLOCK_NEW_TRADES') + '</strong></p>';
    }

    return '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">' +
      '<div class="card-title" style="margin:0">Tradeify 150K Trade Gate</div>' + mxBadge(gb.cls, gb.text) + '</div>' +
      '<div class="grid-3" style="margin-bottom:12px">' +
      '<div><div style="font-size:10px;color:var(--mx-muted)">Drawdown Headroom</div><div class="mono" style="font-size:20px;font-weight:800">' + fmtUsd(headroom).replace('+', '') + '</div></div>' +
      '<div><div style="font-size:10px;color:var(--mx-muted)">Daily Realized P&amp;L</div><div class="mono ' + ((dailyPnl || 0) >= 0 ? 'positive' : 'negative') + '" style="font-size:20px;font-weight:800">' + fmtUsd(dailyPnl) + '</div></div>' +
      '<div><div style="font-size:10px;color:var(--mx-muted)">Data Age</div><div class="mono" style="font-size:14px;font-weight:700">' + stale.label + '</div></div></div>' +
      (reason ? '<div style="padding:10px;background:var(--mx-bg);border-radius:6px;font-size:12px"><strong>Gate Reason:</strong> <span class="mono">' + reason + '</span></div>' : '') +
      (gate && gate.approved_contracts != null ? '<p style="font-size:11px;margin-top:8px;color:var(--mx-muted)">Approved contracts: <span class="mono">' + gate.approved_contracts + '</span></p>' : '');
  }

  function hydrateRisk() {
    var el = document.getElementById('tradeify-risk-live');
    if (!el) return;
    el.innerHTML = renderRiskPanel(_cache.latest, _cache.health);

    var pg = document.getElementById('risk-propguardian-live');
    var snap = snapshotFromLatest(_cache.latest);
    if (pg && snap && snap.balance != null && snap.eod_drawdown_floor != null) {
      var headroom = snap.drawdown_headroom != null ? snap.drawdown_headroom : snap.balance - snap.eod_drawdown_floor;
      var maxDd = 4500;
      var pct = Math.min(100, Math.max(0, Math.round(headroom / maxDd * 100)));
      var bars = pg.querySelectorAll('.progress-fill');
      if (bars[0]) {
        bars[0].style.width = pct + '%';
        bars[0].className = 'progress-fill ' + (pct >= 50 ? 'green' : pct >= 25 ? 'amber' : 'red');
      }
      var headroomEl = pg.querySelector('.mono.positive, .mono.negative, .mono');
      if (headroomEl) headroomEl.textContent = 'Remaining Headroom $' + Math.round(headroom).toLocaleString();
      if (snap.realized_day_pnl != null && bars[1]) {
        var dailyLimit = 750;
        var dailyPct = Math.min(100, Math.round(Math.abs(Math.min(0, snap.realized_day_pnl)) / dailyLimit * 100));
        bars[1].style.width = dailyPct + '%';
        bars[1].className = 'progress-fill ' + (dailyPct < 50 ? 'green' : dailyPct < 80 ? 'amber' : 'red');
      }
    }
  }

  function renderPayoutPanel(evalData, payoutData, snap) {
    var phase = snap && snap.phase;
    var isEval = !phase || String(phase).toUpperCase().indexOf('EVAL') >= 0;

    if (isEval && evalData) {
      return '<div class="card-title">Tradeify 150K — Evaluation Progress</div>' +
        '<div class="grid-4" style="margin:12px 0">' +
        '<div><span class="mono" style="font-size:18px;font-weight:800">' + fmtUsd(evalData.total_profit).replace('+', '') + '</span><div style="font-size:10px;color:var(--mx-muted)">Total Profit</div></div>' +
        '<div><span class="mono" style="font-size:18px;font-weight:800">' + fmtUsd(evalData.remaining_profit_to_target).replace('+', '') + '</span><div style="font-size:10px;color:var(--mx-muted)">To $9K Target</div></div>' +
        '<div><span class="mono" style="font-size:18px;font-weight:800">' + (evalData.pass_eligible ? 'YES' : 'NO') + '</span><div style="font-size:10px;color:var(--mx-muted)">Pass Eligible</div></div>' +
        '<div><span class="mono" style="font-size:18px;font-weight:800">' + fmtUsd(evalData.largest_winning_day).replace('+', '') + '</span><div style="font-size:10px;color:var(--mx-muted)">Largest Win Day</div></div></div>' +
        '<div class="progress-bar" style="margin-bottom:8px"><div class="progress-fill green" style="width:' + Math.min(100, Math.round((evalData.total_profit || 0) / 9000 * 100)) + '%"></div></div>' +
        '<p style="font-size:11px;color:var(--mx-muted)">' + (evalData.warning || '') + '</p>';
    }

    if (payoutData) {
      return '<div class="card-title">Tradeify 150K — Flex Payout Progress</div>' +
        '<div class="grid-4" style="margin:12px 0">' +
        '<div><span class="mono" style="font-size:18px;font-weight:800">' + payoutData.winning_days + ' / 5</span><div style="font-size:10px;color:var(--mx-muted)">Winning Days</div></div>' +
        '<div><span class="mono positive" style="font-size:18px;font-weight:800">' + fmtUsd(payoutData.gross_payout_available).replace('+', '') + '</span><div style="font-size:10px;color:var(--mx-muted)">Gross Payout Avail.</div></div>' +
        '<div><span class="mono positive" style="font-size:18px;font-weight:800">' + fmtUsd(payoutData.trader_net_payout).replace('+', '') + '</span><div style="font-size:10px;color:var(--mx-muted)">Trader Net (90%)</div></div>' +
        '<div><span class="mono" style="font-size:18px;font-weight:800">' + (payoutData.safe_to_request_under_marinerx_policy ? 'SAFE' : 'HOLD') + '</span><div style="font-size:10px;color:var(--mx-muted)">MarinerX Policy</div></div></div>' +
        '<p style="font-size:11px;color:var(--mx-muted)">' + (payoutData.risk_note || '') + '</p>';
    }

    return '<div class="card-title">Tradeify 150K — Account Progress</div>' +
      '<p style="font-size:12px;color:var(--mx-muted);margin-top:8px">Awaiting synced account snapshot. Run Manual Sync from Settings after connectors are configured.</p>';
  }

  function hydratePerformance() {
    var el = document.getElementById('tradeify-payout-live');
    if (!el) return;

    var snap = snapshotFromLatest(_cache.latest);
    if (!snap) {
      el.innerHTML = renderPayoutPanel(null, null, null);
      return;
    }

    var totalProfit = snap.total_eval_profit != null ? snap.total_eval_profit : Math.max(0, (snap.balance || 150000) - 150000);
    var largestWin = snap.largest_winning_day || 0;
    var phase = snap.phase;
    var isEval = !phase || String(phase).toUpperCase().indexOf('EVAL') >= 0;

    var promises = [];
    if (isEval) {
      promises.push(postJson(API + '/eval/status', { total_profit: totalProfit, largest_winning_day: largestWin }));
    } else {
      promises.push(Promise.resolve(null));
    }
    var dayResults = snap.funded_day_results || snap.day_results || [];
    promises.push(postJson(API + '/payout/status', { balance: snap.balance || 150000, day_results: dayResults }));

    Promise.all(promises).then(function (results) {
      _cache.eval = results[0];
      _cache.payout = results[1];
      el.innerHTML = renderPayoutPanel(_cache.eval, _cache.payout, snap);
    }).catch(function () {
      el.innerHTML = renderPayoutPanel(null, null, snap);
    });
  }

  function dataHealthVetoStatus() {
    var rec = _cache.reconcile;
    var latest = _cache.latest;
    var age = ageSeconds(latest && latest.observed_at);
    var stale = staleLevel(age);
    var recOk = reconciliationOk(rec);

    if (recOk === false) return { status: 'FAIL', msg: 'Tradovate vs Tradeify reconciliation mismatch' };
    if (stale.level === 'stale' || stale.level === 'warn') return { status: 'FAIL', msg: stale.label };
    if (!latest || latest.status === 'not_available') return { status: 'WARN', msg: 'No cached Tradeify snapshot — default BLOCK' };
    if (recOk === null) return { status: 'WARN', msg: 'Reconciliation unavailable — confirm before staging' };
    return { status: 'OK', msg: 'Broker and dashboard metrics aligned' };
  }

  function hydrateDecision() {
    var banner = document.getElementById('tradeify-decision-live');
    var veto = dataHealthVetoStatus();
    var color = veto.status === 'OK' ? 'var(--mx-green-text)' : veto.status === 'WARN' ? 'var(--mx-amber-text)' : 'var(--mx-red-text)';
    var icon = veto.status === 'OK' ? '✓' : veto.status === 'WARN' ? '⚠' : '✗';

    if (banner) {
      banner.innerHTML = '<div class="card" style="margin:0;border-left:4px solid ' + color + '">' +
        '<div style="display:flex;justify-content:space-between;align-items:center">' +
        '<strong>Tradeify Data Health Veto</strong>' + mxBadge(veto.status === 'OK' ? 'green' : veto.status === 'WARN' ? 'amber' : 'red', veto.status) +
        '</div><p style="font-size:12px;margin-top:8px;color:' + color + '">' + icon + ' ' + veto.msg + '</p></div>';
    }

    var detail = document.getElementById('decision-detail-live');
    if (detail) {
      var items = detail.querySelectorAll('ul li');
      items.forEach(function (li) {
        if (li.textContent.indexOf('Data Health') >= 0) {
          li.style.color = color;
          li.innerHTML = icon + ' Data Health — <strong>' + veto.status + '</strong> — ' + veto.msg;
        }
      });
    }

    var vetoEl = document.getElementById('tradeify-data-health-veto');
    if (vetoEl) {
      vetoEl.style.color = color;
      vetoEl.innerHTML = icon + ' Data Health — <strong>' + veto.status + '</strong> — ' + veto.msg;
    }
  }

  function wireSyncButton() {
    var btn = document.getElementById('tradeify-sync-btn');
    var status = document.getElementById('tradeify-sync-status');
    if (!btn || _syncBound) return;
    _syncBound = true;
    btn.addEventListener('click', function () {
      btn.disabled = true;
      if (status) status.textContent = 'Syncing…';
      postJson(API + '/data/sync', {})
        .then(function (res) {
          if (status) status.textContent = res.message || ('Sync: ' + (res.status || 'complete'));
          return refreshCore();
        })
        .then(function () {
          var page = typeof window.__mxCurrentPage === 'function' ? window.__mxCurrentPage() : null;
          if (page) hydrate(page);
        })
        .catch(function (err) {
          if (status) status.textContent = 'Sync failed: ' + (err.message || 'error');
        })
        .finally(function () {
          btn.disabled = false;
        });
    });
  }

  function refreshCore() {
    return Promise.all([
      fetchJson(API + '/data/health').then(function (d) { _cache.health = d; }).catch(function () {}),
      fetchJson(API + '/data/latest').then(function (d) { _cache.latest = d; }).catch(function () {})
    ]);
  }

  function hydrate(page) {
    page = page || 'home';
    if (page === 'settings') hydrateSettings();
    if (page === 'risk') hydrateRisk();
    if (page === 'performance') hydratePerformance();
    if (page === 'decision') hydrateDecision();
  }

  function startPolling(getPage) {
    if (_timer) clearInterval(_timer);
    refreshCore().then(function () {
      hydrate(typeof getPage === 'function' ? getPage() : 'home');
    });
    _timer = setInterval(function () {
      refreshCore().then(function () {
        hydrate(typeof getPage === 'function' ? getPage() : 'home');
      });
    }, POLL_MS);
  }

  function reset() {
    _syncBound = false;
  }

  window.TradeifyData = {
    hydrate: hydrate,
    startPolling: startPolling,
    reset: reset,
    getCache: function () { return _cache; }
  };
})();