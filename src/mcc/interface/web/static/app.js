/* MarinerX Labs Phase 15 — SPA Router + Charts + WebSocket */
(function () {
  'use strict';

  var currentPage = 'home';
  var ws = null;
  var plotlyLayout = {
    paper_bgcolor: '#FFFFFF',
    plot_bgcolor: '#FFFFFF',
    font: { color: '#5B6270', size: 10 },
    margin: { t: 10, r: 10, b: 30, l: 40 },
    xaxis: { gridcolor: '#E2E5EA', linecolor: '#E2E5EA' },
    yaxis: { gridcolor: '#E2E5EA', linecolor: '#E2E5EA' }
  };
  var plotlyConfig = { displayModeBar: false, responsive: true };

  function sparkline(id, color) {
    var el = document.getElementById(id);
    if (!el || typeof Plotly === 'undefined') return;
    var y = [];
    for (var i = 0; i < 20; i++) y.push(Math.sin(i * 0.4) * 10 + 50 + Math.random() * 5);
    Plotly.newPlot(el, [{ x: y.map(function (_, i) { return i; }), y: y, type: 'scatter', mode: 'lines', line: { color: color || '#1D4ED8', width: 1.5 } }], {
      paper_bgcolor: '#FFFFFF', plot_bgcolor: '#FFFFFF', margin: { t: 0, r: 0, b: 0, l: 0 },
      xaxis: { visible: false }, yaxis: { visible: false }, height: 40
    }, plotlyConfig);
  }

  function gauge(id, value, maxVal) {
    var el = document.getElementById(id);
    if (!el || typeof Plotly === 'undefined') return;
    var pct = value / maxVal;
    Plotly.newPlot(el, [{
      type: 'indicator', mode: 'gauge+number', value: value,
      gauge: {
        axis: { range: [0, maxVal], tickcolor: '#E2E5EA' },
        bar: { color: pct < 0.5 ? '#15803D' : pct < 0.8 ? '#B45309' : '#B91C1C' },
        bgcolor: '#E5E7EB', borderwidth: 0
      },
      number: { font: { size: 14 } }
    }], { paper_bgcolor: '#FFFFFF', margin: { t: 20, r: 20, b: 0, l: 20 }, height: 120 }, plotlyConfig);
  }

  function initCharts(page) {
    if (typeof Plotly === 'undefined') return;
    setTimeout(function () {
      if (page === 'market-pulse') {
        ['chart-tick', 'chart-trin', 'chart-add', 'chart-vold', 'chart-vix'].forEach(function (id) { sparkline(id); });
        gauge('chart-breadth-gauge', 62, 100);
        var vixEl = document.getElementById('chart-vix-term');
        if (vixEl) Plotly.newPlot(vixEl, [{ x: ['Spot', '1M', '3M', '6M', '9M', '1Y'], y: [14.62, 15.38, 16.42, 17.89, 18.86, 20.41], type: 'scatter', mode: 'lines+markers', line: { color: '#1D4ED8' } }], plotlyLayout, plotlyConfig);
      }
      if (page === 'indicators') {
        var cEl = document.getElementById('chart-nq-candlestick');
        if (cEl) {
          var n = 40, o = [], h = [], l = [], c = [], x = [];
          var base = 18700;
          for (var i = 0; i < n; i++) {
            var op = base + Math.random() * 80 - 40;
            var cl = op + Math.random() * 30 - 15;
            o.push(op); c.push(cl);
            h.push(Math.max(op, cl) + Math.random() * 20);
            l.push(Math.min(op, cl) - Math.random() * 20);
            x.push(i);
          }
          Plotly.newPlot(cEl, [
            { x: x, open: o, high: h, low: l, close: c, type: 'candlestick', increasing: { line: { color: '#15803D' } }, decreasing: { line: { color: '#B91C1C' } } },
            { x: x, y: c.map(function (v, i) { return v - 20 + i * 0.5; }), type: 'scatter', mode: 'lines', line: { color: '#1D4ED8', width: 1 }, name: 'SMA(20)' }
          ], Object.assign({}, plotlyLayout, { height: 360, xaxis: { rangeslider: { visible: false } } }), plotlyConfig);
        }
      }
      if (page === 'validation') {
        var mcEl = document.getElementById('chart-monte-carlo');
        if (mcEl) {
          var bins = [], freqs = [];
          for (var j = -40; j <= 0; j += 2) { bins.push(j); freqs.push(Math.exp(-Math.pow((j + 14) / 8, 2)) * 200 + Math.random() * 20); }
          Plotly.newPlot(mcEl, [{ x: bins, y: freqs, type: 'bar', marker: { color: '#1D4ED8' } }], Object.assign({}, plotlyLayout, { height: 220, bargap: 0.1 }), plotlyConfig);
        }
      }
      if (page === 'risk') {
        gauge('chart-var-gauge', 1180, 2500);
        gauge('chart-cvar-gauge', 1740, 3500);
      }
      if (page === 'performance') {
        var eqEl = document.getElementById('chart-equity-dd');
        if (eqEl) {
          var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May'];
          var eq = [95000, 98000, 102000, 99000, 108420];
          Plotly.newPlot(eqEl, [
            { x: months, y: eq, type: 'scatter', mode: 'lines', line: { color: '#1D4ED8', width: 2 }, name: 'Equity' },
            { x: months, y: [0, -500, -800, -2180, -1200], type: 'scatter', mode: 'lines', fill: 'tozeroy', line: { color: '#FCA5A5' }, name: 'Drawdown' }
          ], Object.assign({}, plotlyLayout, { height: 280 }), plotlyConfig);
        }
        sparkline('chart-sharpe', '#1D4ED8');
        sparkline('chart-sortino', '#1D4ED8');
      }
      if (page === 'reports') {
        var wfEl = document.getElementById('chart-wf-bars');
        if (wfEl) Plotly.newPlot(wfEl, [{
          x: ['Fold 1', 'Fold 2', 'Fold 3', 'Fold 4', 'Fold 5'],
          y: [-140, 190, -160, 55, -275],
          type: 'bar',
          marker: { color: ['#B91C1C', '#15803D', '#B91C1C', '#15803D', '#B91C1C'] }
        }], Object.assign({}, plotlyLayout, { height: 160 }), plotlyConfig);
      }
    }, 50);
  }

  function navigate(page) {
    if (!window.PAGES || !window.PAGES[page]) page = 'home';
    currentPage = page;
    if (window.TradingViewMX) window.TradingViewMX.reset();
    if (window.TradeifyData) window.TradeifyData.reset();
    var container = document.getElementById('page-content');
    if (container) container.innerHTML = window.PAGES[page]();
    document.querySelectorAll('.sidebar-nav a').forEach(function (a) {
      a.classList.toggle('active', a.getAttribute('data-page') === page);
    });
    initCharts(page);
    if (page === 'home') pollHealth();
    if (window.LiveData) window.LiveData.hydrate(page);
    if (window.AgentData) window.AgentData.hydrate(page);
    if (window.TradeifyData) window.TradeifyData.hydrate(page);
  }

  function updateClock() {
    var el = document.getElementById('utc-clock');
    if (!el) return;
    var now = new Date();
    el.textContent = now.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
  }

  function connectWS() {
    var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(protocol + '//' + location.host + '/ws');
    ws.onmessage = function (ev) {
      try {
        var data = JSON.parse(ev.data);
        if (data.type === 'snapshot' && data.agents) updateAgentGrid(data.agents);
      } catch (e) { /* ignore */ }
    };
    ws.onclose = function () { setTimeout(connectWS, 2000); };
  }

  function triggerKill() {
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: 'kill' }));
    alert('Kill switch signal sent to backend.');
  }

  function updateAgentGrid(agents) {
    var grid = document.getElementById('agent-grid-live');
    if (!grid) return;
    Object.keys(agents).forEach(function (name) {
      var cards = grid.querySelectorAll('.agent-card-name');
      cards.forEach(function (el) {
        if (el.textContent === name) {
          var card = el.closest('.agent-card');
          if (card) {
            var dot = card.querySelector('.status-dot');
            var st = agents[name].status || 'idle';
            if (dot) {
              dot.className = 'status-dot ' + (st === 'working' ? 'green' : st === 'error' ? 'red' : 'neutral');
            }
          }
        }
      });
    });
  }

  function pollHealth() {
    fetch('/health').then(function (r) { return r.json(); }).then(function (j) {
      if (j.agents) updateAgentGrid(j.agents);
    }).catch(function () { /* ignore */ });
  }

  function init() {
    document.querySelectorAll('.sidebar-nav a').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        navigate(a.getAttribute('data-page'));
        location.hash = a.getAttribute('data-page');
      });
    });
    var killBtn = document.getElementById('kill-btn');
    if (killBtn) killBtn.addEventListener('click', triggerKill);
    updateClock();
    setInterval(updateClock, 1000);
    connectWS();
    setInterval(pollHealth, 5000);
    if (window.SystemState) window.SystemState.start();
    if (window.LiveData) window.LiveData.startPolling(function () { return currentPage; });
    if (window.AgentData) window.AgentData.startPolling(function () { return currentPage; });
    if (window.TradeifyData) window.TradeifyData.startPolling(function () { return currentPage; });
    window.__mxCurrentPage = function () { return currentPage; };
    var hash = (location.hash || '#home').slice(1);
    navigate(hash || 'home');
    window.addEventListener('hashchange', function () {
      navigate((location.hash || '#home').slice(1) || 'home');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();