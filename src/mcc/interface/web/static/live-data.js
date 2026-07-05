/* Live dashboard hydration — fetches /api/live/* (yfinance, free/delayed) */
(function () {
  'use strict';

  var POLL_MS = 30000;
  var _timer = null;
  var _lastBars = {};

  function fmtPrice(n, sym) {
    if (n == null) return '—';
    if (sym === 'CL' || sym === 'GC') return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtPct(pct) {
    if (pct == null) return '—';
    var sign = pct >= 0 ? '+' : '';
    return sign + pct.toFixed(2) + '%';
  }

  function decisionClass(d) {
    if (d === 'GO') return { card: 'go', badge: 'green', text: 'GO' };
    if (d === 'NO-GO') return { card: 'no-go', badge: 'red', text: 'NO-GO' };
    return { card: 'stand-aside', badge: 'amber', text: 'STAND-ASIDE' };
  }

  function setLiveBadge() {
    var hdr = document.querySelector('.header-status');
    if (hdr && hdr.textContent.indexOf('LIVE DATA') === -1) {
      hdr.innerHTML = '<span class="status-dot green"></span> LIVE DATA &middot; yfinance (delayed)';
    }
  }

  function hydrateHome(snapshot) {
    if (!snapshot || !snapshot.instruments) return;
    var cards = document.querySelectorAll('.instrument-card');
    snapshot.instruments.forEach(function (q) {
      cards.forEach(function (card) {
        var symEl = card.querySelector('.instrument-symbol');
        if (!symEl || symEl.textContent.trim() !== q.symbol) return;
        var dc = decisionClass(q.decision);
        card.className = 'instrument-card ' + dc.card;
        var badge = card.querySelector('.badge');
        if (badge) {
          badge.className = 'badge badge-' + dc.badge;
          badge.textContent = dc.text;
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
      });
    });
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
    var gauge = document.getElementById('chart-breadth-gauge');
    if (gauge && typeof Plotly !== 'undefined' && data.breadth_score != null) {
      Plotly.newPlot(gauge, [{
        type: 'indicator', mode: 'gauge+number', value: data.breadth_score,
        gauge: {
          axis: { range: [0, 100] },
          bar: { color: data.breadth_score >= 60 ? '#15803D' : '#B45309' },
          bgcolor: '#E5E7EB', borderwidth: 0
        },
        number: { font: { size: 14 } }
      }], { paper_bgcolor: '#FFFFFF', margin: { t: 20, r: 20, b: 0, l: 20 }, height: 120 }, { displayModeBar: false });
    }
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
    var o = b.map(function (row) { return row.open; });
    var h = b.map(function (row) { return row.high; });
    var l = b.map(function (row) { return row.low; });
    var c = b.map(function (row) { return row.close; });
    var sma = bars.sma20 || [];
    var traces = [
      { x: x, open: o, high: h, low: l, close: c, type: 'candlestick',
        increasing: { line: { color: '#15803D' } }, decreasing: { line: { color: '#B91C1C' } } }
    ];
    if (sma.some(function (v) { return v != null; })) {
      traces.push({ x: x, y: sma, type: 'scatter', mode: 'lines', line: { color: '#1D4ED8', width: 1 }, name: 'SMA(20)' });
    }
    var last = b[b.length - 1];
    var cap = document.querySelector('.card .mono');
    if (cap && last) {
      cap.textContent = symbol + ' • 5m • LIVE ' + fmtPrice(last.close, symbol) +
        ' • O ' + last.open + ' H ' + last.high + ' L ' + last.low + ' C';
    }
    Plotly.newPlot(el, traces, {
      paper_bgcolor: '#FFFFFF', plot_bgcolor: '#FFFFFF', font: { color: '#5B6270', size: 10 },
      margin: { t: 10, r: 10, b: 30, l: 40 }, height: 360, xaxis: { rangeslider: { visible: false } }
    }, { displayModeBar: false, responsive: true });
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
    hydrateIndicators: hydrateIndicators
  };
})();