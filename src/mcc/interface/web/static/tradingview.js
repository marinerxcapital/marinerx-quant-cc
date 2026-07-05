/* TradingView Advanced Chart embed (free interactive widget) */
(function () {
  'use strict';

  var TV_MAP = {
    NQ: 'CME_MINI:NQ1!',
    ES: 'CME_MINI:ES1!',
    CL: 'NYMEX:CL1!',
    GC: 'COMEX:GC1!'
  };
  var _mounted = {};

  function resolveSymbol(mcxSymbol) {
    return TV_MAP[(mcxSymbol || 'NQ').toUpperCase()] || TV_MAP.NQ;
  }

  function mount(containerId, mcxSymbol, height, force) {
    var container = document.getElementById(containerId);
    if (!container) return;
    var tvSymbol = resolveSymbol(mcxSymbol);
    if (!force && _mounted[containerId] === tvSymbol) return;
    _mounted[containerId] = tvSymbol;

    container.innerHTML = '';
    container.style.height = (height || 420) + 'px';
    container.classList.add('tv-chart-panel');

    var wrap = document.createElement('div');
    wrap.className = 'tradingview-widget-container';
    wrap.style.height = '100%';
    wrap.style.width = '100%';

    var inner = document.createElement('div');
    inner.className = 'tradingview-widget-container__widget';
    inner.style.height = '100%';
    inner.style.width = '100%';
    wrap.appendChild(inner);

    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async = true;
    script.text = JSON.stringify({
      autosize: true,
      symbol: tvSymbol,
      interval: '5',
      timezone: 'America/New_York',
      theme: 'light',
      style: '1',
      locale: 'en',
      enable_publishing: false,
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: false,
      support_host: 'https://www.tradingview.com',
      studies: ['STD;RSI', 'STD;MACD']
    });
    wrap.appendChild(script);
    container.appendChild(wrap);

    var credit = document.createElement('div');
    credit.className = 'tv-attribution';
    credit.innerHTML = 'Charts by <a href="https://www.tradingview.com/" target="_blank" rel="noopener">TradingView</a>';
    container.appendChild(credit);
  }

  function reset() {
    _mounted = {};
  }

  function loadConfig() {
    return fetch('/api/live/tradingview').then(function (r) { return r.json(); }).then(function (cfg) {
      if (cfg.symbols) TV_MAP = Object.assign({}, TV_MAP, cfg.symbols);
      return cfg;
    }).catch(function () { return { symbols: TV_MAP }; });
  }

  window.TradingViewMX = {
    mount: mount,
    reset: reset,
    loadConfig: loadConfig,
    symbols: TV_MAP
  };
})();