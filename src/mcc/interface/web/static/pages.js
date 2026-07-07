/* MarinerX Labs Phase 15 — Page Templates */
window.PAGES = {};

function mxBadge(cls, text) {
  return '<span class="badge badge-' + cls + '">' + text + '</span>';
}

function mxSection(title, link, body) {
  var h = '<div class="section-header"><div class="section-title">' + title + '</div>';
  if (link) h += '<a href="#" class="section-link">' + link + '</a>';
  return h + '</div>' + body;
}

function loadingBlock(msg) {
  return '<div style="padding:32px;text-align:center;color:var(--mx-muted)">' + (msg || 'Loading…') + '</div>';
}

PAGES.home = function() {
  var agents = [
    ['Overseer','System oversight & orchestration','Running','Uptime 99.98%','green','green'],
    ['DataOps','Data pipeline & quality control','Running','Latency 128 ms','green','green'],
    ['AccountSync','Account & position synchronization','Syncing','Accounts 12 / 12','blue','blue'],
    ['MarketPulse','Real-time market monitoring','Running','Events/min 1,842','green','green'],
    ['IndicatorEngine','Indicator computation engine','Running','Indicators 312','green','green'],
    ['RegimeMonitor','Market regime detection','Running','Regime Risk-On','green','green'],
    ['StrategyRunner','Strategy execution & scheduling','Running','Strategies 18','green','green'],
    ['ValidationEngine','Model & data validation','Review','Alerts 2','amber','amber'],
    ['ResearchLab','Research & idea incubation','Syncing','Active Ideas 24','blue','blue'],
    ['RiskCommand','Risk monitoring & controls','Running','Risk Score 28 / 100','green','green'],
    ['DecisionEngine','Signal generation & decisioning','Running','Signals 37','green','green'],
    ['ExecutionGateway','Order routing & execution','Running','Fill Rate 98.7%','green','green'],
    ['TradeJournal','Trade logging & annotations','Running','Today Trades 24','green','green'],
    ['PerformanceAnalyst','Performance attribution & analysis','Review','Sharpe (MTD) 1.87','amber','amber'],
    ['ReportPublisher','Report generation & distribution','Blocked','Queue 3','red','red']
  ];
  var grid = '<div class="agent-grid" id="agent-grid-live">';
  agents.forEach(function(a) {
    grid += '<div class="agent-card"><div class="agent-card-header"><span class="agent-card-name">' + a[0] +
      '</span><span class="status-dot ' + a[4] + '"></span></div><div class="agent-card-desc">' + a[1] +
      '</div>' + mxBadge(a[5], a[2]) + '<div class="agent-card-metric">' + a[3] + '</div></div>';
  });
  grid += '</div>';
  var inst = [
    ['NQ','E-MINI NASDAQ-100','GO','18,742.75','+1.24% (+229.25)','positive','Momentum strong, breadth positive, regime supportive.','go','green'],
    ['ES','E-MINI S&P 500','NO-GO','5,293.75','-0.38% (-20.25)','negative','Mixed signals, weakening momentum, risk/reward poor.','no-go','red'],
    ['CL','WTI CRUDE OIL','NO-GO','77.35','-0.91% (-0.71)','negative','Supply pressure elevated, momentum down, vol rising.','no-go','red'],
    ['GC','GOLD COMEX','STAND-ASIDE','2,358.40','+0.12% (+2.80)','positive','Range-bound market, low edge, await breakout.','stand-aside','amber']
  ];
  var ic = '<div class="grid-4">';
  inst.forEach(function(x) {
    ic += '<div class="instrument-card ' + x[7] + '"><div class="instrument-symbol">' + x[0] +
      '</div><div class="instrument-name">' + x[1] + '</div>' + mxBadge(x[8], x[2]) +
      '<div class="instrument-price mono">' + x[3] + '</div><div class="instrument-change ' + x[5] + ' mono">' + x[4] +
      '</div><div class="instrument-reason">' + x[6] + '</div></div>';
  });
  ic += '</div>';
  return '<div class="page-header"><h1 class="page-title">Command Center Home</h1><p class="page-subtitle">System overview and agent command grid.</p></div>' +
    '<div class="card" style="margin-bottom:16px">' + mxSection('1. Agent Command Grid', '<span id="agent-grid-metrics">15 Agents</span> &nbsp; View All Agents &rarr;', grid) + '</div>' +
    '<div class="card">' + mxSection('2. Instrument Decision Center', 'Updated: 14:32:18 UTC &nbsp; View All Markets &rarr;', ic) + '</div>';
};

PAGES['market-pulse'] = function() {
  return '<div class="page-header"><h1 class="page-title">Market Pulse</h1><p class="page-subtitle">Real-time market internals and breadth telemetry.</p></div>' +
    '<div class="tabs"><button class="tab active">Internals</button><button class="tab">Microstructure</button><button class="tab">Heatmaps</button></div>' +
    '<div id="market-pulse-live">' + loadingBlock('Loading market pulse…') + '</div>';
};

PAGES.indicators = function() {
  var inds = [['SMA(20)','Trend',true],['EMA(50)','Trend',true],['RSI(14)','Momentum',true],['MACD(12,26,9)','Momentum',true],
    ['Bollinger Bands(20,2)','Volatility',true],['VWAP + Bands','Overlay',true],['ADX(14)','Trend',false],['Donchian Channel','Trend',false],
    ['Opening Range','Session',false],['Session VWAP','Session',true]];
  var lib = '<div class="card"><div class="card-title">Indicator Library</div>';
  inds.forEach(function(i) {
    lib += '<div class="indicator-row"><div class="indicator-info"><span class="indicator-name">' + i[0] +
      '</span><span class="indicator-cat">' + i[1] + '</span></div><label class="toggle"><input type="checkbox"' +
      (i[2]?' checked':'') + '><span class="toggle-slider"></span></label></div>';
  });
  lib += '</div>';
  return '<div class="page-header"><h1 class="page-title">Indicators &amp; Regime</h1><p class="page-subtitle">Charting and regime classification.</p></div>' +
    '<div class="grid-2" style="grid-template-columns:280px 1fr;align-items:start"><div>' + lib + '</div>' +
    '<div class="card"><div class="tabs" id="indicator-symbol-tabs"><button class="tab active" data-tv-symbol="NQ">NQ</button><button class="tab" data-tv-symbol="ES">ES</button><button class="tab" data-tv-symbol="CL">CL</button><button class="tab" data-tv-symbol="GC">GC</button></div>' +
    '<p class="mono" id="indicator-price-caption" style="font-size:11px;margin-bottom:8px">NQ • 15m • loading…</p>' +
    '<div id="tv-chart-indicators"></div>' +
    '<div id="chart-nq-candlestick" style="height:0;overflow:hidden"></div></div></div>' +
    '<div class="card-title" style="margin-top:16px">Regime Snapshot</div>' +
    '<div id="indicators-regime-live">' + loadingBlock('Loading regime data…') + '</div>';
};

PAGES.strategy = function() {
  var tbl = '<table class="data-table"><thead><tr><th>Strategy ID</th><th>Name</th><th>Version</th><th>Instrument(s)</th><th>Status</th><th>Last Updated</th><th>Owner/Agent</th><th>Notes</th></tr></thead><tbody id="strategy-registry-live"><tr><td colspan="8" style="text-align:center">Loading strategies…</td></tr></tbody></table>';
  var drawer = '<div class="drawer"><div class="drawer-title">Strategy Detail</div><h3 style="font-size:14px">CL EIA Inventory Drift ' + mxBadge('amber','YELLOW') + '</h3>' +
    '<p style="font-size:11px;color:var(--mx-muted);margin:8px 0">STR-CL-EIA-002</p><p style="font-size:12px;margin-bottom:12px">EIA inventory release drift strategy (WTI crude)</p>' +
    '<div class="drawer-section"><h4>Parameters</h4><ul class="kv-list"><li><span class="kv-key">Instrument</span><span class="kv-val">CL</span></li>' +
    '<li><span class="kv-key">Event Window</span><span class="kv-val">10:30–11:00 ET</span></li><li><span class="kv-key">Stop</span><span class="kv-val">0.42</span></li>' +
    '<li><span class="kv-key">Target</span><span class="kv-val">0.88</span></li></ul></div>' +
    '<div class="drawer-section"><h4>Lifecycle</h4><div class="lifecycle"><span class="lifecycle-step">DRAFT</span><span class="lifecycle-arrow">→</span>' +
    '<span class="lifecycle-step">REGISTERED</span><span class="lifecycle-arrow">→</span><span class="lifecycle-step">TESTED</span><span class="lifecycle-arrow">→</span>' +
    '<span class="lifecycle-step" style="background:var(--mx-amber-bg)">VERDICT (YELLOW)</span></div></div>' +
    '<div style="display:flex;gap:8px;margin-top:12px"><button class="btn-secondary">Open Memo</button><button class="btn-primary">Run Validation</button><button class="btn-secondary">Archive</button></div></div>';
  return '<div class="page-header"><h1 class="page-title">Strategy Registry</h1><p class="page-subtitle">Strategy lifecycle tracking and validation status.</p></div>' +
    '<div style="display:flex;gap:8px;margin-bottom:16px"><input placeholder="Search strategies..." style="flex:1;padding:8px;border:1px solid var(--mx-border);border-radius:6px">' +
    '<select style="padding:8px;border:1px solid var(--mx-border);border-radius:6px"><option>Status: All</option></select></div>' +
    '<div class="page-with-drawer"><div class="card table-wrap">' + tbl + '</div>' + drawer + '</div>';
};

PAGES.validation = function() {
  var list = '<div class="card"><div class="card-title">Registered Strategies</div><div id="validation-live">' + loadingBlock('Loading strategies…') + '</div></div>';
  var detail = '<div id="validation-detail-live">' + loadingBlock('Select a strategy and run validation.') + '</div>';
  return '<div class="page-header"><h1 class="page-title">Validation &amp; Verdicts</h1><p class="page-subtitle">Statistical strategy validation and verdict review.</p></div>' +
    '<div style="display:grid;grid-template-columns:260px 1fr;gap:16px">' + list + '<div>' + detail + '</div></div>';
};

PAGES.research = function() {
  var models = [
    ['LightGBM','NQ 15m Direction','SIGNAL','green','0.184','56.8%','53.1%','2025-05-30 13:58 UTC'],
    ['XGBoost','ES 30m Continuation','NO_SIGNAL','neutral','0.221','51.2%','51.0%','2025-05-30 13:42 UTC'],
    ['Logistic Regression','CL Event Filter','NO_SIGNAL','neutral','0.238','49.7%','50.4%','2025-05-30 12:55 UTC'],
    ['CatBoost','GC Vol Regime','NO_SIGNAL','neutral','0.214','52.0%','52.6%','2025-05-30 13:11 UTC']
  ];
  var cards = '<div class="grid-4" style="margin-bottom:16px">';
  models.forEach(function(m) {
    cards += '<div class="card"><div style="display:flex;justify-content:space-between"><strong>' + m[0] + '</strong>' + mxBadge(m[3], m[2]) + '</div>' +
      '<p style="font-size:11px;color:var(--mx-muted)">' + m[1] + '</p><div class="mono" style="font-size:22px;font-weight:800;margin:8px 0">' + m[4] + '</div>' +
      '<div style="font-size:11px">Hit Rate <span class="mono positive">' + m[5] + '</span> &nbsp; Baseline <span class="mono">' + m[6] + '</span></div>' +
      '<div style="height:6px;background:var(--mx-neutral-bg);border-radius:3px;margin:6px 0"><div style="width:57%;height:100%;background:var(--mx-green-text);border-radius:3px"></div></div>' +
      '<div style="font-size:10px;color:var(--mx-muted)">Last trained: ' + m[7] + '</div></div>';
  });
  cards += '</div>';
  var runs = [
    ['RUN-240530-001','a91f3c7','2022-01 to 2024-12','LightGBM','Brier 0.184','SIGNAL','green'],
    ['RUN-240530-002','c44da19','2021-06 to 2024-12','XGBoost','Brier 0.221','NO_SIGNAL','neutral'],
    ['RUN-240530-003','e7b12af','2020-01 to 2024-12','Logistic Regression','Brier 0.238','FAILED_BASELINE','red'],
    ['RUN-240530-004','f2d1bc','2021-01 to 2024-12','CatBoost','Brier 0.214','NO_SIGNAL','neutral'],
    ['RUN-240530-005','5b0e855','2019-01 to 2024-06','LightGBM','Hit Rate 55.9%','PROMOTED_TO_REVIEW','blue']
  ];
  var tbl = '<table class="data-table"><thead><tr><th>Run ID</th><th>Config Hash</th><th>Dataset Window</th><th>Model</th><th>Key Metric</th><th>Result</th><th>Timestamp</th></tr></thead><tbody>';
  runs.forEach(function(r) {
    tbl += '<tr><td class="mono">' + r[0] + '</td><td class="mono">' + r[1] + '</td><td>' + r[2] + '</td><td>' + r[3] +
      '</td><td class="mono">' + r[4] + '</td><td>' + mxBadge(r[6], r[5]) + '</td><td class="mono">2025-05-30</td></tr>';
  });
  tbl += '</tbody></table>';
  return '<div class="page-header"><h1 class="page-title">Research Lab</h1><p class="page-subtitle">Quant and machine-learning experiment tracking.</p></div>' +
    '<div id="research-live"></div><div class="card-title" style="margin-bottom:12px">Forecast Lab</div>' + cards +
    '<div class="card"><div class="card-title">Experiment Tracker</div><div class="table-wrap">' + tbl + '</div></div>';
};

PAGES.risk = function() {
  var top = '<div class="grid-3" id="risk-metrics-live" style="margin-bottom:16px"><div class="card"><div class="card-title">Position Sizing</div>' +
    '<p><strong>Instrument:</strong> NQ</p><p style="font-size:20px;font-weight:800;margin:8px 0">2 contracts</p>' +
    '<div class="tabs"><button class="tab active">Fractional Kelly</button><button class="tab">Vol-Target</button></div>' +
    '<ul class="kv-list"><li><span class="kv-key">Risk per Trade</span><span class="kv-val">$350</span></li>' +
    '<li><span class="kv-key">Stop Distance</span><span class="kv-val">17.5 pts</span></li><li><span class="kv-key">Max Size Cap</span><span class="kv-val">3 contracts</span></li></ul>' +
    '<p style="font-size:11px;color:var(--mx-muted);margin-top:8px">Reduced from Kelly estimate due to intraday volatility expansion.</p></div>' +
    '<div class="card"><div class="card-title">Portfolio VaR</div><div id="chart-var-gauge" style="height:120px"></div>' +
    '<p class="mono" style="text-align:center"><strong>$1,180</strong> / $2,500 limit</p></div>' +
    '<div class="card"><div class="card-title">Expected Shortfall (CVaR)</div><div id="chart-cvar-gauge" style="height:120px"></div>' +
    '<p class="mono" style="text-align:center"><strong>$1,740</strong> / $3,500 limit</p></div></div>';
  var pg = '<div class="card" id="risk-propguardian-live" style="margin-bottom:16px"><div style="display:flex;gap:8px;align-items:center;margin-bottom:12px"><strong style="font-size:16px">PropGuardian</strong>' +
    mxBadge('green','OK') + mxBadge('amber','CAUTION') + mxBadge('red','LOCKOUT') + '</div>' +
    '<div style="margin-bottom:12px"><div style="font-size:11px;margin-bottom:4px">Drawdown Headroom</div><div class="progress-bar"><div class="progress-fill green" style="width:87%"></div></div>' +
    '<span class="mono positive">Remaining Headroom $4,620</span></div>' +
    '<div style="margin-bottom:12px"><div style="font-size:11px;margin-bottom:4px">Daily Loss Progress: $780 / $2,000</div><div class="progress-bar"><div class="progress-fill green" style="width:39%"></div></div></div>' +
    '<ul style="list-style:none;font-size:12px"><li>✓ Daily loss limit – Clear</li><li>✓ Trailing threshold – Clear</li><li>✓ Max contracts – Clear</li><li>✓ No lockout active – Clear</li></ul></div>';
  var exp = '<div class="card table-wrap"><div class="card-title">Portfolio Exposure</div><table class="data-table"><thead><tr><th>Instrument</th><th>Net Exposure</th><th>Gross Exposure</th><th>Contracts</th></tr></thead><tbody>' +
    '<tr><td>NQ</td><td class="positive">+2</td><td>2</td><td>2</td></tr><tr><td>ES</td><td class="negative">-1</td><td>1</td><td>1</td></tr>' +
    '<tr><td>CL</td><td class="positive">+1</td><td>1</td><td>1</td></tr><tr><td>GC</td><td>0</td><td>0</td><td>0</td></tr></tbody></table></div>';
  return '<div class="page-header"><h1 class="page-title">Risk Command</h1><p class="page-subtitle">Sizing, VaR, expected shortfall, drawdown control, and portfolio exposure.</p></div>' +
    '<div class="card" style="margin-bottom:16px"><div class="card-title">Live Market Context (TradingView)</div><div id="tv-chart-risk" style="height:320px"></div></div>' +
    '<div class="card" id="tradeify-risk-live" style="margin-bottom:16px"></div>' +
    top + pg + '<div id="risk-exposure-live">' + exp + '</div>';
};

PAGES.decision = function() {
  var cards = [
    ['NQ','E-MINI NASDAQ-100','GO','68%','18,742.75','Validated trending setup with strong internals.','go','green','selected'],
    ['ES','E-MINI S&P 500','NO-GO','38%','5,293.75','Mixed signals and weakening momentum.','no-go','red',''],
    ['CL','WTI CRUDE OIL','NO-GO','22%','77.35','Supply pressure elevated, momentum down.','no-go','red',''],
    ['GC','GOLD COMEX','STAND-ASIDE','49%','2,358.40','Range-bound market, low edge environment.','stand-aside','amber','']
  ];
  var ic = '<div class="grid-4" id="decision-cards-live" style="margin-bottom:16px">';
  cards.forEach(function(c) {
    ic += '<div class="instrument-card ' + c[6] + (c[8]==='selected'?' selected':'') + '"><div class="instrument-symbol">' + c[0] +
      '</div><div class="instrument-name">' + c[1] + '</div>' + mxBadge('lg badge-' + c[7], c[2]) +
      '<div class="mono" style="margin:6px 0">Confidence: <strong class="' + (c[7]==='green'?'positive':c[7]==='red'?'negative':'') + '">' + c[3] + '</strong></div>' +
      '<div class="instrument-price mono">' + c[4] + '</div><div class="instrument-reason">' + c[5] + '</div></div>';
  });
  ic += '</div>';
  var vetoes = ['Validation passed','Risk passed','Event passed','Data Health passed','Session passed'];
  var vl = '<ul style="list-style:none">';
  vetoes.forEach(function(v) { vl += '<li style="padding:6px 0;color:var(--mx-green-text)">✓ ' + v + ' — <strong>OK</strong></li>'; });
  vl += '</ul>';
  var factors = [['Strategy Signal Strength',75],['Regime Alignment',78],['Internals Alignment',72],['Microstructure Confirmation',60],['Forecast Signal',58],['Risk Headroom Quality',71]];
  var fb = '';
  factors.forEach(function(f) {
    fb += '<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;font-size:11px"><span>' + f[0] + '</span><span class="mono">' + f[1] + '%</span></div>' +
      '<div class="progress-bar"><div class="progress-fill green" style="width:' + f[1] + '%"></div></div></div>';
  });
  var detail = '<div class="card"><div style="display:flex;justify-content:space-between;margin-bottom:12px"><strong>NQ Decision Detail</strong><span class="mono positive">Total Confidence: 68%</span></div>' +
    '<div class="grid-2"><div><div class="card-title">Veto Checklist</div>' + vl + '</div><div><div class="card-title">Factor Breakdown</div>' + fb + '</div></div>' +
    '<div style="margin-top:16px;padding:12px;background:var(--mx-bg);border-radius:8px;font-size:12px"><strong>Reasoning:</strong> NQ is approved because validated setup alignment is present, regime indicator confirms trending state, internals remain risk-on, and PropGuardian headroom remains above required threshold.</div>' +
    '<div class="grid-3" style="margin-top:12px;font-size:12px"><div><strong>Recommended Size:</strong> 2 contracts</div><div><strong>Max Risk:</strong> $350</div><div><strong>Invalidation:</strong> break below opening range midpoint</div></div></div>';
  return '<div class="page-header"><h1 class="page-title">Trade-or-No-Trade Decision Center</h1><p class="page-subtitle">Real-time trade eligibility and decision analytics.</p></div>' +
    '<div id="tradeify-decision-live" style="margin-bottom:16px"></div>' +
    ic +
    '<div class="card" style="margin-bottom:16px"><div class="card-title">Interactive Chart — <span id="decision-tv-symbol">NQ</span> (TradingView)</div><div id="tv-chart-decision"></div></div>' +
    '<div id="decision-detail-live">' + detail + '</div>';
};

PAGES.execution = function() {
  var banner = '<div class="live-banner"><strong>LIVE TRADING: DISABLED</strong><p>Enable requires explicit configuration + confirmation token in Settings.</p></div>';
  return '<div class="page-header"><h1 class="page-title">Execution &amp; Orders</h1></div>' + banner +
    '<div id="execution-live">' + loadingBlock('Loading paper execution state…') + '</div>';
};

PAGES.journal = function() {
  return '<div class="page-header"><h1 class="page-title">Trade Journal</h1><p class="page-subtitle">Structured trade log with setup context, execution details, and outcomes.</p></div>' +
    '<div id="journal-live">' + loadingBlock('Loading journal entries…') + '</div>';
};

PAGES.performance = function() {
  return '<div class="page-header"><h1 class="page-title">Performance Analytics</h1><p class="page-subtitle">Performance from stored paper orders — labeled SIMULATED when empty.</p></div>' +
    '<div class="card" id="tradeify-payout-live" style="margin-bottom:16px"></div>' +
    '<div class="card" style="margin-bottom:16px"><div class="card-title">Benchmark — NQ Futures (TradingView)</div><div id="tv-chart-performance"></div></div>' +
    '<div class="grid-2" style="margin-bottom:16px"><div class="card"><div class="card-title">Equity Curve &amp; Drawdown</div>' +
    '<div id="perf-stats-live">' + loadingBlock('Loading performance summary…') + '</div>' +
    '<div id="chart-equity-dd" style="height:280px"></div></div>' +
    '<div class="card"><div class="card-title">Attribution</div><p style="font-size:12px;color:var(--mx-muted);padding:16px">Breakdown populated when trade history exists.</p></div></div>';
};

PAGES.reports = function() {
  var preview = '<div class="card" style="min-height:400px"><div class="card-title">Report Preview</div>' +
    '<p style="font-size:12px;color:var(--mx-muted);padding:24px">Select a report from the list or generate a new report.</p></div>';
  return '<div class="page-header"><h1 class="page-title">Reports</h1><p class="page-subtitle">View, download, and manage generated research reports and documents.</p></div>' +
    '<div style="display:grid;grid-template-columns:40% 60%;gap:16px"><div class="card" id="reports-live">' + loadingBlock('Loading reports…') + '</div>' + preview + '</div>';
};

PAGES.settings = function() {
  var danger = '<div class="danger-zone"><p style="font-size:12px;margin-bottom:12px">Critical system controls. Actions are immediate and irreversible.</p>' +
    '<button class="btn-kill" style="width:100%;margin-bottom:12px">GLOBAL KILL SWITCH</button>' +
    '<label style="font-size:12px;display:flex;gap:8px;margin-bottom:12px"><input type="checkbox"> I understand this will flatten/disable all active execution routes</label>' +
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px"><label class="toggle"><input type="checkbox"><span class="toggle-slider"></span></label><span>Live Execution OFF — DISABLED</span></div>' +
    '<input placeholder="confirmation token" style="width:100%;padding:8px;border:1px solid var(--mx-border);border-radius:6px"></div>';
  return '<div class="page-header"><h1 class="page-title">Settings &amp; System Control</h1><p class="page-subtitle">System configuration, data feeds, execution controls, and audit.</p></div>' +
    '<div class="card" id="tradeify-connector-live" style="margin-bottom:16px"></div>' +
    '<div id="settings-live">' + loadingBlock('Loading system configuration…') + '</div>' +
    '<div class="card" style="margin-top:16px;margin-bottom:16px">' + danger + '</div>';
};
