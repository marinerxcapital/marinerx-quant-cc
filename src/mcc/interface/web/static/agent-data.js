/* Agent + account hydration — fetches /api/agents/* and /api/account/sync */
(function () {
  'use strict';

  var POLL_MS = 15000;
  var _timer = null;
  var _cache = {
    snapshot: null,
    journal: null,
    account: null,
    marketPulse: null
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

  function mxBadge(cls, text) {
    return '<span class="badge badge-' + cls + '">' + text + '</span>';
  }

  function awaitingBanner(page) {
    return '<div class="live-banner" style="background:var(--mx-amber-bg);border:1px solid var(--mx-amber-text);color:var(--mx-primary);margin-bottom:12px">' +
      '<strong>Awaiting sync</strong><p>Live ' + page + ' data not yet available from backend agents. Showing template until sync completes.</p></div>';
  }

  function hydrateHeader(account) {
    var wrap = document.getElementById('header-metrics-live');
    if (!wrap) return;

    if (!account || account.sync_status !== 'live') {
      wrap.querySelectorAll('.header-metric-value').forEach(function (el, i) {
        if (i === 0 || i === 1) {
          el.textContent = '—';
          el.className = 'header-metric-value';
        } else if (i === 2) {
          el.textContent = 'Awaiting sync';
          el.className = 'header-metric-value';
        }
      });
      return;
    }

    var metrics = wrap.querySelectorAll('.header-metric');
    if (metrics[0]) {
      var dayEl = metrics[0].querySelector('.header-metric-value');
      if (dayEl && account.day_pnl != null) {
        dayEl.textContent = fmtUsd(account.day_pnl);
        dayEl.className = 'header-metric-value ' + (account.day_pnl >= 0 ? 'positive' : 'negative');
      }
    }
    if (metrics[1]) {
      var weekEl = metrics[1].querySelector('.header-metric-value');
      if (weekEl) {
        if (account.week_pnl != null) {
          weekEl.textContent = fmtUsd(account.week_pnl);
          weekEl.className = 'header-metric-value ' + (account.week_pnl >= 0 ? 'positive' : 'negative');
        } else {
          weekEl.textContent = '—';
          weekEl.className = 'header-metric-value';
        }
      }
    }
    if (metrics[2]) {
      var headEl = metrics[2].querySelector('.header-metric-value');
      if (headEl && account.drawdown_headroom != null) {
        headEl.textContent = '$' + Math.round(account.drawdown_headroom).toLocaleString();
        headEl.className = 'header-metric-value';
      }
    }

    var statusHdr = document.querySelector('.header-status');
    if (statusHdr && account.stale) {
      statusHdr.innerHTML = '<span class="status-dot amber"></span> ACCOUNT DATA STALE';
    } else if (statusHdr && account.sync_status === 'live') {
      statusHdr.innerHTML = '<span class="status-dot green"></span> ACCOUNT SYNCED';
    }
  }

  function hydrateAgentGrid(snapshot) {
    var grid = document.getElementById('agent-grid-live');
    if (!grid || !snapshot || !snapshot.agents) return;

    Object.keys(snapshot.agents).forEach(function (name) {
      var info = snapshot.agents[name];
      var cards = grid.querySelectorAll('.agent-card-name');
      cards.forEach(function (el) {
        if (el.textContent.trim() !== name) return;
        var card = el.closest('.agent-card');
        if (!card) return;

        var dot = card.querySelector('.status-dot');
        if (dot) {
          dot.className = 'status-dot ' + (info.badge === 'green' ? 'green' : info.badge === 'red' ? 'red' : info.badge === 'blue' ? 'blue' : 'neutral');
        }

        var badge = card.querySelector('.badge');
        if (badge) {
          badge.className = 'badge badge-' + (info.badge || 'neutral');
          badge.textContent = info.label || info.status || '—';
        }

        var metric = card.querySelector('.agent-card-metric');
        if (metric && info.metric) {
          metric.textContent = info.metric;
        }
      });
    });

    var metricsPanel = document.getElementById('agent-grid-metrics');
    if (metricsPanel && snapshot.agent_count) {
      metricsPanel.textContent = snapshot.agent_count + ' agents tracked';
    }
  }

  function hydrateJournal(data) {
    var el = document.getElementById('journal-live');
    if (!el) return;

    if (!data || data.sync_status !== 'live' || !data.trades || !data.trades.length) {
      var tbody = el.querySelector('tbody');
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;color:var(--mx-muted);padding:24px">Awaiting sync — no trades in database yet.</td></tr>';
      }
      return;
    }

    var rows = '';
    data.trades.forEach(function (t, idx) {
      var sideCls = (t.side || '').toUpperCase() === 'LONG' || (t.side || '').toUpperCase() === 'BUY' ? 'green' : 'red';
      var sideLabel = (t.side || '').toUpperCase() === 'BUY' ? 'LONG' : (t.side || '').toUpperCase() === 'SELL' ? 'SHORT' : (t.side || '—');
      var pnl = t.pnl != null ? (t.pnl >= 0 ? '+$' + Math.abs(t.pnl).toFixed(2) : '-$' + Math.abs(t.pnl).toFixed(2)) : '—';
      var pnlCls = (t.pnl || 0) >= 0 ? 'positive' : 'negative';
      var decCls = (t.decision || 'GO') === 'GO' ? 'green' : 'red';
      rows += '<tr class="' + (idx === 0 ? 'selected' : '') + '">' +
        '<td>' + (t.date || '—') + '</td><td class="mono">' + (t.time || '—') + '</td><td>' + (t.symbol || '—') + '</td>' +
        '<td>' + mxBadge(sideCls, sideLabel) + '</td><td>' + (t.setup_tag || '—') + '</td><td class="mono">' + (t.strategy_id || '—') + '</td>' +
        '<td class="mono">' + (t.price != null ? t.price.toLocaleString() : '—') + '</td><td class="mono">—</td>' +
        '<td class="' + pnlCls + '">' + pnl + '</td><td>' + (t.regime || '—') + '</td>' +
        '<td>' + mxBadge(decCls, t.decision || 'GO') + '</td></tr>';
    });
    var tbody = el.querySelector('tbody');
    if (tbody) tbody.innerHTML = rows;
  }

  function hydrateStrategy(snapshot) {
    var el = document.getElementById('strategy-registry-live');
    if (!el) return;
    var strategies = snapshot && snapshot.strategies;
    if (!strategies || !strategies.length) {
      el.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--mx-muted);padding:24px">Awaiting sync — no strategies registered in database.</td></tr>';
      return;
    }
    var rows = '';
    strategies.forEach(function (s) {
      var bc = s.status === 'GREEN' ? 'green' : s.status === 'RED' ? 'red' : s.status === 'YELLOW' ? 'amber' : 'neutral';
      rows += '<tr><td class="mono">' + s.id + '</td><td>' + s.id + '</td><td>—</td><td>—</td>' +
        '<td>' + mxBadge(bc, s.status || 'DRAFT') + '</td><td class="mono">—</td><td>StrategyRunner</td><td>From registry</td></tr>';
    });
    el.innerHTML = rows;
  }

  function hydrateValidation(snapshot) {
    var el = document.getElementById('validation-live');
    if (!el) return;
    var logs = snapshot && snapshot.decision_logs;
    if (!logs || !logs.length) {
      el.innerHTML = awaitingBanner('validation');
      return;
    }
    var list = '<ul style="list-style:none">';
    logs.forEach(function (d, i) {
      var cls = d.decision === 'GO' ? 'green' : d.decision === 'NO-GO' ? 'red' : 'amber';
      list += '<li style="padding:10px;border-bottom:1px solid var(--mx-border);' + (i === 0 ? 'background:var(--mx-blue-soft)' : '') + '">' +
        '<strong>' + (d.symbol || '—') + '</strong> ' + mxBadge(cls, d.decision || '—') +
        '<br><span style="font-size:11px;color:var(--mx-muted)">' + (d.reason || '') + '</span></li>';
    });
    list += '</ul>';
    el.innerHTML = list;
  }

  function hydrateResearch() {
    var el = document.getElementById('research-live');
    if (!el) return;
    el.innerHTML = awaitingBanner('research lab');
  }

  function hydrateExecution(journal) {
    var el = document.getElementById('execution-live');
    if (!el) return;
    if (!journal || journal.sync_status !== 'live' || !journal.trades || !journal.trades.length) {
      el.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--mx-muted);padding:24px">Awaiting sync — no fills recorded.</td></tr>';
      return;
    }
    var rows = '';
    journal.trades.slice(0, 10).forEach(function (t) {
      var side = (t.side || '').toUpperCase();
      var sideCls = side === 'BUY' || side === 'LONG' ? 'positive' : 'negative';
      var label = side === 'BUY' ? 'BUY' : side === 'SELL' ? 'SELL' : side;
      rows += '<tr><td class="mono">' + (t.ts_utc || '—') + '</td><td>' + (t.symbol || '—') + '</td>' +
        '<td class="' + sideCls + '">' + label + '</td><td>' + (t.qty || '—') + '</td>' +
        '<td class="mono">' + (t.price != null ? t.price : '—') + '</td><td>PAPER</td>' +
        '<td>' + mxBadge('green', 'FILLED') + '</td></tr>';
    });
    el.innerHTML = rows;
  }

  function hydrateReports(snapshot) {
    var el = document.getElementById('reports-live');
    if (!el) return;
    var reports = snapshot && snapshot.reports;
    if (!reports || !reports.length) {
      el.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--mx-muted);padding:24px">Awaiting sync — no reports published.</td></tr>';
      return;
    }
    var rows = '';
    reports.forEach(function (r) {
      rows += '<tr><td><strong>' + r.id + '</strong><br><span style="font-size:10px;color:var(--mx-muted)">' + (r.report_type || '') + '</span></td>' +
        '<td>' + mxBadge('red', (r.report_type || 'PDF').toUpperCase()) + '</td>' +
        '<td class="mono">' + (r.ts_utc || '—') + '</td><td>' + mxBadge('green', 'COMPLETED') + '</td></tr>';
    });
    el.innerHTML = rows;
  }

  function hydrateIndicators(symbol) {
    symbol = symbol || 'NQ';
    fetchJson('/api/agents/indicators/' + symbol).then(function (data) {
      var caption = document.getElementById('indicator-price-caption');
      if (caption && data.indicators && data.indicators.values) {
        var v = data.indicators.values;
        caption.textContent = symbol + ' • close ' + (v.close != null ? v.close : '—') +
          ' • RSI ' + (v.rsi_14 != null ? v.rsi_14 : '—') +
          ' • sync ' + (data.indicators.sync_status || '—');
      }
      var regimeCards = document.querySelectorAll('.regime-card');
      if (regimeCards.length && data.regime) {
        regimeCards.forEach(function (card) {
          var symEl = card.querySelector('strong');
          if (!symEl || symEl.textContent.trim() !== symbol) return;
          var vol = data.regime.volatility || 'NORMAL';
          var bc = vol === 'HIGH' ? 'red' : vol === 'NORMAL' ? 'amber' : 'green';
          var badge = card.querySelector('.badge');
          if (badge) {
            badge.className = 'badge badge-' + bc;
            badge.textContent = vol;
          }
        });
      }
    }).catch(function () { /* keep mock */ });
  }

  function refreshCore() {
    return Promise.all([
      fetchJson('/api/agents/snapshot').then(function (d) { _cache.snapshot = d; }).catch(function () {}),
      fetchJson('/api/account/sync').then(function (d) { _cache.account = d; }).catch(function () {}),
      fetchJson('/api/agents/journal').then(function (d) { _cache.journal = d; }).catch(function () {})
    ]);
  }

  function hydrate(page) {
    page = page || 'home';

    refreshCore().then(function () {
      hydrateHeader(_cache.account);
      if (page === 'home' || page === 'settings') {
        hydrateAgentGrid(_cache.snapshot);
      }
      if (page === 'journal') {
        hydrateJournal(_cache.journal);
      }
      if (page === 'strategy') {
        hydrateStrategy(_cache.snapshot);
      }
      if (page === 'validation') {
        hydrateValidation(_cache.snapshot);
      }
      if (page === 'research') {
        hydrateResearch();
      }
      if (page === 'execution') {
        hydrateExecution(_cache.journal);
      }
      if (page === 'reports') {
        hydrateReports(_cache.snapshot);
      }
    });

    if (page === 'market-pulse') {
      fetchJson('/api/agents/market-pulse').then(function (d) {
        _cache.marketPulse = d;
        if (d.sync_status === 'awaiting_sync') {
          var hdr = document.querySelector('.page-header .page-subtitle');
          if (hdr) hdr.textContent = 'Awaiting sync — MarketPulse agent snapshot unavailable.';
        }
      }).catch(function () {});
    }

    if (page === 'indicators') {
      hydrateIndicators('NQ');
    }
  }

  function startPolling(getPage) {
    if (_timer) clearInterval(_timer);
    hydrate(typeof getPage === 'function' ? getPage() : 'home');
    _timer = setInterval(function () {
      hydrate(typeof getPage === 'function' ? getPage() : 'home');
    }, POLL_MS);
  }

  window.AgentData = {
    hydrate: hydrate,
    startPolling: startPolling,
    getCache: function () { return _cache; }
  };
})();