/* Live dashboard hydration — fetches /api/live/* (yfinance, free/delayed) */
(function () {
  'use strict';

  var POLL_MS = 30000;
  var _timer = null;
  var _lastBars = {};
  var _selectedDecision = null;

  function fmtPrice(n, sym) {
    if (n == null) return '—';
    return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtPct(pct) {
    if (pct == null) return '—';
    var sign = pct >= 0 ? '+' : '';
    return sign + pct.toFixed(2) + '%';
  }

  function fmtUsd(n) {
    if (n == null) return '—';
    var sign = n >= 0 ? '+$' : '-$';
    return sign + Math.abs(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
  }

  function decisionClass(d) {
    if (d === 'GO') return { card: 'go', badge: 'green', text: 'GO' };
    if (d === 'NO-GO') return { card: 'no-go', badge: 'red', text: 'NO-GO' };
    return { card: 'stand-aside', badge: 'amber', text: 'STAND-ASIDE' };
  }

  function setLiveBadge() {
    var hdr = document.querySelector('.header-status');
    if (hdr && hdr.textContent.indexOf('LIVE DATA') === -1) {
      hdr.innerHTML = '<span class="status-dot green"></span> LIVE DATA &middot; yfinance + TradingView';
    }
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

  function hydrateHome(snapshot) {
    if (!snapshot || !snapshot.instruments) return;
    document.querySelectorAll('.instrument-card').forEach(function (card) {
      var symEl = card.querySelector('.instrument-symbol');
      if (!symEl) return;
      var q = snapshot.instruments.find(function (i) { return i.symbol === symEl.textContent.trim(); });
      if (!q) return;
      applyInstrumentCard(card, q);
    });
  }

  function applyInstrumentCard(card, q) {
    var dc = decisionClass(q.decision);
    card.className = 'instrument-card ' + dc.card + (card.classList.contains('selected') ? ' selected' : '');
    var badge = card.querySelector('.badge');
    if (badge) {
      badge.className = 'badge badge-lg badge-' + dc.badge;
      badge.textContent = dc.text;
    }
    var conf = card.querySelector('.mono strong');
    if (conf && q.confidence_pct != null) {
      conf.textContent = q.confidence_pct + '%';
      conf.className = dc.badge === 'green' ? 'positive' : dc.badge === 'red' ? 'negative' : '';
    }
    var price = card.querySelector('.instrument-price');
    if (price) price.textContent = fmtPrice(q.price, q.symbol);
    var chg = card.querySelector('.instrument-change');
    if (chg) {
      chg.textContent = fmtPct(q.change_pct) + (q.change != null ? ' (' + (q.change >= 0 ? '+' : '') + q.change + ')' : '');
      chg.className = 'instrument-change mono ' + ((q.change_pct || 0) >= 0 ? 'positive' : 'negative');
    }
    var reason = card.querySelector('.instrument-reason');
    if (reason) reason.textContent = q.reason || '';
  }

  function hydrateMarketPulse(data) {
    if (!data || !data.proxies) return;
    var map = [
      ['$TICK', data.proxies.tick, 'chart-tick'],
      ['$TRIN', data.proxies.trin, 'chart-trin'],
      ['$ADD', data.proxies.add, 'chart-add'],
      ['$VOLD', data.proxies.vold, 'chart-vold'],
      ['$VIX', data.vix && data.vix.value, 'chart-vix']
    ];
    document.querySelectorAll('.sparkline-card').forEach(function (card) {
      var label = card.querySelector('.sparkline-label');
      if (!label) return;
      map.forEach(function (m) {
        if (label.textContent.trim() !== m[0]) return;
        var val = card.querySelector('.sparkline-value');
        if (val && m[1] != null) {
          val.textContent = (m[0] === '$TRIN' || m[0] === '$VIX') ? m[1] : (m[1] > 0 && m[0] !== '$VOLD' ? '+' + m[1] : m[1]);
        }
        if (data.sparklines && data.sparklines[m[2].replace('chart-', '')]) {
          plotSpark(m[2], data.sparklines[m[2].replace('chart-', '')], '#1D4ED8');
        }
      });
    });
    var regimeBadge = document.querySelector('.badge-lg');
    if (regimeBadge && data.regime) {
      regimeBadge.textContent = data.regime;
      regimeBadge.className = 'badge badge-lg ' + (data.regime === 'RISK-ON' ? 'badge-green' : data.regime === 'RISK-OFF' ? 'badge-red' : 'badge-amber');
    }
    if (data.breadth_score != null) plotGauge('chart-breadth-gauge', data.breadth_score, 100);
    var vixTerm = document.getElementById('chart-vix-term');
    if (vixTerm && data.vix_term && data.vix_term.length && typeof Plotly !== 'undefined') {
      Plotly.newPlot(vixTerm, [{
        x: data.vix_term.map(function (p) { return p.label; }),
        y: data.vix_term.map(function (p) { return p.value; }),
        type: 'scatter', mode: 'lines+markers', line: { color: '#1D4ED8' }
      }], {
        paper_bgcolor: '#FFFFFF', plot_bgcolor: '#FFFFFF', font: { color: '#5B6270', size: 10 },
        margin: { t: 10, r: 10, b: 30, l: 40 }, height: 140
      }, { displayModeBar: false, responsive: true });
    }
  }

  function hydrateIndicators(bars, symbol) {
    symbol = symbol || 'NQ';
    if (!bars || !bars.bars || !bars.bars.length || typeof Plotly === 'undefined') return;
    _lastBars[symbol] = bars;
    var el = document.getElementById('chart-nq-candlestick');
    if (!el) return;
    var b = bars.bars;
    var x = b.map(function (row, i) { return i; });
    var traces = [{
      x: x,
      open: b.map(function (row) { return row.open; }),
      high: b.map(function (row) { return row.high; }),
      low: b.map(function (row) { return row.low; }),
      close: b.map(function (row) { return row.close; }),
      type: 'candlestick',
      increasing: { line: { color: '#15803D' } }, decreasing: { line: { color: '#B91C1C' } }
    }];
    var sma = bars.sma20 || [];
    if (sma.some(function (v) { return v != null; })) {
      traces.push({ x: x, y: sma, type: 'scatter', mode: 'lines', line: { color: '#1D4ED8', width: 1 }, name: 'SMA(20)' });
    }
    var last = b[b.length - 1];
    var cap = document.getElementById('indicator-price-caption');
    if (cap && last) {
      cap.textContent = symbol + ' • 5m • LIVE ' + fmtPrice(last.close, symbol) +
        ' • O ' + last.open + ' H ' + last.high + ' L ' + last.low + ' C ' + last.close;
    }
    Plotly.newPlot(el, traces, {
      paper_bgcolor: '#FFFFFF', plot_bgcolor: '#FFFFFF', font: { color: '#5B6270', size: 10 },
      margin: { t: 10, r: 10, b: 30, l: 40 }, height: 360, xaxis: { rangeslider: { visible: false } }
    }, { displayModeBar: false, responsive: true });
  }

  function propBadgeClass(status) {
    if (status === 'OK') return 'green';
    if (status === 'CAUTION') return 'amber';
    return 'red';
  }

  function hydrateRisk(data) {
    if (!data) return;
    var metrics = document.getElementById('risk-metrics-live');
    if (metrics) {
      var cards = metrics.querySelectorAll('.card');
      if (cards[0] && data.sizing) {
        var s = data.sizing;
        var ps = cards[0].querySelectorAll('p');
        if (ps[0]) ps[0].innerHTML = '<strong>Instrument:</strong> ' + s.instrument;
        if (ps[1]) ps[1].innerHTML = '<span style="font-size:20px;font-weight:800;margin:8px 0;display:block">' + s.contracts + ' contract' + (s.contracts === 1 ? '' : 's') + '</span>';
        var kv = cards[0].querySelectorAll('.kv-val');
        if (kv[0]) kv[0].textContent = fmtUsd(s.risk_per_trade_usd).replace('+', '');
        if (kv[1]) kv[1].textContent = s.stop_points + ' pts';
        if (kv[2]) kv[2].textContent = s.max_contracts + ' contracts';
      }
      if (cards[1] && data.var) {
        plotGauge('chart-var-gauge', data.var.value, data.var.limit);
        var varTxt = cards[1].querySelector('.mono');
        if (varTxt) varTxt.innerHTML = '<strong>$' + data.var.value.toLocaleString() + '</strong> / $' + data.var.limit.toLocaleString() + ' limit';
      }
      if (cards[2] && data.cvar) {
        plotGauge('chart-cvar-gauge', data.cvar.value, data.cvar.limit);
        var cvarTxt = cards[2].querySelector('.mono');
        if (cvarTxt) cvarTxt.innerHTML = '<strong>$' + data.cvar.value.toLocaleString() + '</strong> / $' + data.cvar.limit.toLocaleString() + ' limit';
      }
    }

    var pg = document.getElementById('risk-propguardian-live');
    if (pg && data.prop_guardian) {
      var pgData = data.prop_guardian;
      var badgeRow = pg.querySelector('div[style*="display:flex"]');
      if (badgeRow) {
        badgeRow.innerHTML = '<strong style="font-size:16px">PropGuardian</strong>' +
          '<span class="badge badge-' + propBadgeClass(pgData.status) + '">' + pgData.status + '</span>';
      }
      var bars = pg.querySelectorAll('.progress-fill');
      if (bars[0]) {
        bars[0].style.width = pgData.headroom_pct + '%';
        bars[0].className = 'progress-fill ' + (pgData.headroom_pct >= 50 ? 'green' : pgData.headroom_pct >= 25 ? 'amber' : 'red');
      }
      var headroom = pg.querySelector('.mono.positive, .mono.negative, .mono');
      if (headroom) headroom.textContent = 'Remaining Headroom $' + pgData.headroom_usd.toLocaleString();
      if (bars[1]) {
        var dailyPct = Math.min(100, Math.round(pgData.daily_loss_usd / pgData.daily_limit_usd * 100));
        bars[1].style.width = dailyPct + '%';
        bars[1].className = 'progress-fill ' + (dailyPct < 50 ? 'green' : dailyPct < 80 ? 'amber' : 'red');
      }
      var dailyLabel = pg.querySelector('div[style*="margin-bottom:12px"] div');
      if (dailyLabel && dailyLabel.textContent.indexOf('Daily Loss') === 0) {
        dailyLabel.textContent = 'Daily Loss Progress: $' + pgData.daily_loss_usd + ' / $' + pgData.daily_limit_usd;
      }
    }

    var expWrap = document.getElementById('risk-exposure-live');
    if (expWrap && data.exposures) {
      var rows = data.exposures.map(function (e) {
        var netCls = e.net > 0 ? 'positive' : e.net < 0 ? 'negative' : '';
        var netStr = e.net > 0 ? '+' + e.net : String(e.net);
        return '<tr><td>' + e.symbol + '</td><td class="' + netCls + '">' + netStr + '</td><td>' + e.gross + '</td><td>' + e.contracts + '</td></tr>';
      }).join('');
      expWrap.innerHTML = '<div class="card table-wrap"><div class="card-title">Portfolio Exposure</div><table class="data-table"><thead><tr><th>Instrument</th><th>Net Exposure</th><th>Gross Exposure</th><th>Contracts</th></tr></thead><tbody>' + rows + '</tbody></table></div>';
    }

    mountTradingViewForPage('risk', 'NQ');
  }

  function vetoLabel(key) {
    var labels = { validation: 'Validation', risk: 'Risk', event: 'Event', 'data-health': 'Data Health', session: 'Session' };
    return labels[key] || key;
  }

  function renderDecisionDetail(card) {
    if (!card) return '';
    var vetoes = (card.vetoes || []).map(function (v) {
      var ok = v.status === 'OK';
      var color = ok ? 'var(--mx-green-text)' : v.status === 'WARN' ? 'var(--mx-amber-text)' : 'var(--mx-red-text)';
      return '<li style="padding:6px 0;color:' + color + '">' + (ok ? '✓' : v.status === 'WARN' ? '⚠' : '✗') + ' ' + vetoLabel(v.key) + ' — <strong>' + v.status + '</strong></li>';
    }).join('');
    var factors = card.factors || {};
    var factorRows = [
      ['Strategy Signal Strength', factors.strategy_signal],
      ['Regime Alignment', factors.regime_alignment],
      ['Internals Alignment', factors.internals_alignment],
      ['Microstructure Confirmation', factors.microstructure],
      ['Forecast Signal', factors.forecast_signal],
      ['Risk Headroom Quality', factors.risk_headroom]
    ];
    var fb = factorRows.map(function (f) {
      var pct = f[1] || 0;
      return '<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;font-size:11px"><span>' + f[0] + '</span><span class="mono">' + pct + '%</span></div>' +
        '<div class="progress-bar"><div class="progress-fill green" style="width:' + pct + '%"></div></div></div>';
    }).join('');
    var confCls = card.decision === 'GO' ? 'positive' : card.decision === 'NO-GO' ? 'negative' : '';
    return '<div class="card"><div style="display:flex;justify-content:space-between;margin-bottom:12px"><strong>' + card.symbol + ' Decision Detail</strong>' +
      '<span class="mono ' + confCls + '">Total Confidence: ' + (card.confidence_pct || 0) + '%</span></div>' +
      '<div class="grid-2"><div><div class="card-title">Veto Checklist</div><ul style="list-style:none">' + vetoes + '</ul></div>' +
      '<div><div class="card-title">Factor Breakdown</div>' + fb + '</div></div>' +
      '<div style="margin-top:16px;padding:12px;background:var(--mx-bg);border-radius:8px;font-size:12px"><strong>Reasoning:</strong> ' + (card.reason || 'No reasoning available.') + '</div>' +
      '<div class="grid-3" style="margin-top:12px;font-size:12px"><div><strong>Live Price:</strong> ' + fmtPrice(card.price, card.symbol) + '</div>' +
      '<div><strong>Change:</strong> <span class="' + ((card.change_pct || 0) >= 0 ? 'positive' : 'negative') + '">' + fmtPct(card.change_pct) + '</span></div>' +
      '<div><strong>Regime:</strong> ' + (card.regime || '—') + '</div></div></div>';
  }

  function hydrateDecision(data) {
    if (!data || !data.cards) return;
    var primary = _selectedDecision || data.primary_symbol || 'NQ';
    var primaryCard = data.cards.find(function (c) { return c.symbol === primary; }) || data.cards[0];

    document.querySelectorAll('#decision-cards-live .instrument-card').forEach(function (cardEl) {
      var sym = cardEl.querySelector('.instrument-symbol');
      if (!sym) return;
      var q = data.cards.find(function (c) { return c.symbol === sym.textContent.trim(); });
      if (!q) return;
      cardEl.classList.toggle('selected', q.symbol === primaryCard.symbol);
      applyInstrumentCard(cardEl, q);
      if (q.confidence_pct != null) {
        var confLine = cardEl.querySelector('.mono');
        if (confLine) {
          var dc = decisionClass(q.decision);
          confLine.innerHTML = 'Confidence: <strong class="' + (dc.badge === 'green' ? 'positive' : dc.badge === 'red' ? 'negative' : '') + '">' + q.confidence_pct + '%</strong>';
        }
      }
    });

    var detail = document.getElementById('decision-detail-live');
    if (detail && primaryCard) detail.innerHTML = renderDecisionDetail(primaryCard);

    var symEl = document.getElementById('decision-tv-symbol');
    if (symEl && primaryCard) symEl.textContent = primaryCard.symbol;

    mountTradingViewForPage('decision', primaryCard ? primaryCard.symbol : 'NQ');
  }

  function wireDecisionCardClicks() {
    document.querySelectorAll('#decision-cards-live .instrument-card').forEach(function (card) {
      card.style.cursor = 'pointer';
      card.onclick = function () {
        var sym = card.querySelector('.instrument-symbol');
        if (!sym) return;
        _selectedDecision = sym.textContent.trim();
        fetchJson('/api/live/decision').then(hydrateDecision).catch(function () {});
      };
    });
  }

  function hydratePerformance(data) {
    if (!data) return;
    var stats = document.getElementById('perf-stats-live');
    if (stats) {
      var vals = stats.querySelectorAll('.mono');
      if (vals[0]) {
        vals[0].textContent = fmtUsd(data.net_pnl);
        vals[0].className = 'mono ' + (data.net_pnl >= 0 ? 'positive' : 'negative');
      }
      if (vals[1]) {
        vals[1].textContent = fmtUsd(data.max_drawdown);
        vals[1].className = 'mono negative';
      }
      if (vals[2]) vals[2].textContent = (data.win_rate_pct || 0) + '%';
      if (vals[3]) vals[3].textContent = String(data.profit_factor || 0);
    }

    var eqEl = document.getElementById('chart-equity-dd');
    if (eqEl && data.equity_curve && data.equity_curve.length && typeof Plotly !== 'undefined') {
      var dates = data.equity_curve.map(function (p) { return p.date; });
      var equity = data.equity_curve.map(function (p) { return p.equity; });
      var dd = data.equity_curve.map(function (p) { return p.drawdown; });
      Plotly.newPlot(eqEl, [
        { x: dates, y: equity, type: 'scatter', mode: 'lines', line: { color: '#1D4ED8', width: 2 }, name: 'Equity' },
        { x: dates, y: dd, type: 'scatter', mode: 'lines', fill: 'tozeroy', line: { color: '#FCA5A5' }, name: 'Drawdown' }
      ], {
        paper_bgcolor: '#FFFFFF', plot_bgcolor: '#FFFFFF', font: { color: '#5B6270', size: 10 },
        margin: { t: 10, r: 10, b: 30, l: 40 }, height: 280
      }, { displayModeBar: false, responsive: true });

      var deltas = equity.map(function (v, i) { return i ? v - equity[i - 1] : 0; });
      plotSpark('chart-sharpe', deltas.slice(-20), '#1D4ED8');
      plotSpark('chart-sortino', deltas.slice(-20), '#1D4ED8');
    }

    var sharpeMono = document.querySelector('#chart-sharpe') && document.querySelector('#chart-sharpe').previousElementSibling;
    if (sharpeMono && sharpeMono.classList.contains('mono')) sharpeMono.textContent = String(data.sharpe || 0);
    var sortinoMono = document.querySelector('#chart-sortino') && document.querySelector('#chart-sortino').previousElementSibling;
    if (sortinoMono && sortinoMono.classList.contains('mono')) sortinoMono.textContent = String(data.sortino || 0);

    mountTradingViewForPage('performance', 'NQ');
  }

  function mountTradingViewForPage(page, symbol) {
    if (!window.TradingViewMX) return;
    var map = {
      indicators: { id: 'tv-chart-indicators', height: 420 },
      risk: { id: 'tv-chart-risk', height: 320 },
      decision: { id: 'tv-chart-decision', height: 380 },
      performance: { id: 'tv-chart-performance', height: 360 }
    };
    var cfg = map[page];
    if (cfg && document.getElementById(cfg.id)) {
      window.TradingViewMX.mount(cfg.id, symbol || 'NQ', cfg.height);
    }
  }

  function wireIndicatorTabs() {
    var tabs = document.getElementById('indicator-symbol-tabs');
    if (!tabs) return;
    tabs.querySelectorAll('.tab').forEach(function (btn) {
      btn.onclick = function () {
        tabs.querySelectorAll('.tab').forEach(function (t) { t.classList.remove('active'); });
        btn.classList.add('active');
        var sym = btn.getAttribute('data-tv-symbol') || 'NQ';
        if (window.TradingViewMX) window.TradingViewMX.mount('tv-chart-indicators', sym, 420, true);
        fetchJson('/api/live/bars/' + sym).then(function (b) { hydrateIndicators(b, sym); }).catch(function () {});
      };
    });
  }

  function fetchJson(path) {
    return fetch(path).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  function hydrate(page) {
    page = page || 'home';
    fetchJson('/api/live/snapshot').then(function (snap) {
      setLiveBadge();
      if (page === 'home') hydrateHome(snap);
    }).catch(function () { /* keep mock */ });

    if (page === 'market-pulse') {
      fetchJson('/api/live/internals').then(hydrateMarketPulse).catch(function () {});
    }
    if (page === 'indicators') {
      fetchJson('/api/live/bars/NQ').then(function (b) { hydrateIndicators(b, 'NQ'); }).catch(function () {});
      mountTradingViewForPage('indicators', 'NQ');
      wireIndicatorTabs();
    }
    if (page === 'risk') {
      fetchJson('/api/live/risk').then(hydrateRisk).catch(function () {});
    }
    if (page === 'decision') {
      fetchJson('/api/live/decision').then(function (d) {
        hydrateDecision(d);
        wireDecisionCardClicks();
      }).catch(function () {});
    }
    if (page === 'performance') {
      fetchJson('/api/live/performance').then(hydratePerformance).catch(function () {});
    }
  }

  function startPolling(getPage) {
    if (_timer) clearInterval(_timer);
    _timer = setInterval(function () {
      hydrate(typeof getPage === 'function' ? getPage() : 'home');
    }, POLL_MS);
  }

  window.LiveData = {
    hydrate: hydrate,
    startPolling: startPolling,
    hydrateIndicators: hydrateIndicators,
    wireIndicatorTabs: wireIndicatorTabs
  };
})();