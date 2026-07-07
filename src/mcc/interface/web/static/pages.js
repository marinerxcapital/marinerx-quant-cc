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
    '<div class="card" style="margin-bottom:16px">' + mxSection('1. Agent Command Grid', '15 Agents &nbsp; View All Agents &rarr;', grid) + '</div>' +
    '<div class="card">' + mxSection('2. Instrument Decision Center', 'Updated: 14:32:18 UTC &nbsp; View All Markets &rarr;', ic) + '</div>';
};

PAGES['market-pulse'] = function() {
  var sparks = [
    ['$TICK','+850','green','EXTREME','red','chart-tick'],
    ['$TRIN','0.82','green','RISK-ON','green','chart-trin'],
    ['$ADD','+1,742','green','','','chart-add'],
    ['$VOLD','+2.8:1','green','','','chart-vold'],
    ['$VIX','14.62','','','','chart-vix']
  ];
  var sc = '<div class="grid-5" style="margin-bottom:16px">';
  sparks.forEach(function(s) {
    sc += '<div class="sparkline-card"><div class="sparkline-label">' + s[0] + '</div><div class="sparkline-value ' +
      (s[2]==='green'?'positive':'') + ' mono">' + s[1] + '</div>' +
      (s[3]?mxBadge(s[4],s[3]):'') + '<div id="' + s[5] + '" style="height:40px"></div><div class="sparkline-ts">14:32:18 UTC</div></div>';
  });
  sc += '</div>';
  var table = '<table class="data-table"><thead><tr><th>Component</th><th>Current</th><th>Direction</th><th>Weight</th><th>Impact</th></tr></thead><tbody>' +
    '<tr><td>TICK</td><td class="num positive">+850</td><td>↑ Positive</td><td>25%</td><td class="num positive">+0.21</td></tr>' +
    '<tr><td>TRIN</td><td class="num">0.82</td><td>↑ Positive</td><td>20%</td><td class="num positive">+0.16</td></tr>' +
    '<tr><td>ADD</td><td class="num positive">+1,742</td><td>↑ Expanding</td><td>25%</td><td class="num positive">+0.24</td></tr>' +
    '<tr><td>VOLD</td><td class="num positive">+2.8:1</td><td>↑ Positive</td><td>20%</td><td class="num positive">+0.15</td></tr>' +
    '<tr><td>VIX</td><td class="num">14.62</td><td>↓ Declining</td><td>10%</td><td class="num positive">+0.09</td></tr></tbody></table>';
  var regime = '<div class="card" style="margin-bottom:16px"><div class="grid-2"><div><div class="badge badge-lg badge-green">RISK-ON</div>' +
    '<p style="margin-top:8px;font-weight:700">Confidence 74%</p><p style="font-size:12px;color:var(--mx-secondary)">TICK positive, ADD expanding, VOLD positive, VIX declining.</p></div>' +
    '<div class="table-wrap">' + table + '<div style="text-align:right;margin-top:8px"><span class="mono positive">Total Impact +0.85</span> &nbsp; <span class="mono positive">Regime Score 85 / 100</span></div></div></div></div>';
  var detail = '<div class="grid-4"><div class="card"><div class="card-title">Breadth Pressure Meter</div><div id="chart-breadth-gauge" style="height:140px"></div><div class="mono positive" style="text-align:center;font-size:18px;font-weight:800">+62 RISK-ON</div></div>' +
    '<div class="card"><div class="card-title">Advance / Decline</div><table class="data-table"><thead><tr><th></th><th>Advancing</th><th>Declining</th><th>%</th></tr></thead><tbody>' +
    '<tr><td>NYSE</td><td class="positive">2,354</td><td class="negative">876</td><td>73%</td></tr>' +
    '<tr><td>NASDAQ</td><td class="positive">2,812</td><td class="negative">921</td><td>74%</td></tr>' +
    '<tr><td>S&amp;P 500</td><td class="positive">387</td><td class="negative">113</td><td>77%</td></tr>' +
    '<tr><td><strong>Total</strong></td><td class="positive"><strong>5,553</strong></td><td class="negative"><strong>1,910</strong></td><td><strong>74%</strong></td></tr></tbody></table></div>' +
    '<div class="card"><div class="card-title">VIX Term Structure</div><div id="chart-vix-term" style="height:140px"></div></div>' +
    '<div class="card"><div class="card-title">Session Breadth Timeline</div><div id="chart-breadth-timeline" style="height:140px"></div></div></div>';
  return '<div class="page-header"><h1 class="page-title">Market Pulse</h1><p class="page-subtitle">Real-time market internals and breadth telemetry.</p></div>' +
    '<div class="tabs"><button class="tab active">Internals</button><button class="tab">Microstructure</button><button class="tab">Heatmaps</button></div>' +
    sc + regime + '<div class="card-title" style="margin-bottom:12px">Market Pulse Detail</div>' + detail;
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
  var regimes = [['NQ','HIGH','TRENDING','72%','high'],['ES','NORMAL','RANGING','61%','normal'],['CL','HIGH','TRENDING','67%','high'],['GC','LOW','RANGING','58%','low']];
  var rg = '<div class="grid-4" style="margin-top:16px">';
  regimes.forEach(function(r) {
    var bc = r[1]==='HIGH'?'red':r[1]==='NORMAL'?'amber':'green';
    rg += '<div class="regime-card ' + r[4] + '"><div style="display:flex;justify-content:space-between"><strong>' + r[0] +
      '</strong>' + mxBadge(bc, r[1]) + '</div><div style="margin:6px 0">' + mxBadge(bc, r[2]) + ' <span class="mono">' + r[3] + '</span></div>' +
      '<div class="regime-prob-bar"><div class="regime-prob-fill" style="width:' + r[3] + ';background:var(--mx-' + bc + '-text)"></div></div></div>';
  });
  rg += '</div>';
  return '<div class="page-header"><h1 class="page-title">Indicators &amp; Regime</h1><p class="page-subtitle">Charting and regime classification.</p></div>' +
    '<div class="grid-2" style="grid-template-columns:280px 1fr;align-items:start"><div>' + lib + '</div>' +
    '<div class="card"><div class="tabs" id="indicator-symbol-tabs"><button class="tab active" data-tv-symbol="NQ">NQ</button><button class="tab" data-tv-symbol="ES">ES</button><button class="tab" data-tv-symbol="CL">CL</button><button class="tab" data-tv-symbol="GC">GC</button></div>' +
    '<p class="mono" id="indicator-price-caption" style="font-size:11px;margin-bottom:8px">NQ • 5m • loading live quote…</p>' +
    '<div id="tv-chart-indicators"></div>' +
    '<div id="chart-nq-candlestick" style="height:0;overflow:hidden"></div></div></div>' +
    '<div class="card-title" style="margin-top:16px">Regime Snapshot</div>' + rg;
};

PAGES.strategy = function() {
  var rows = [
    ['STR-NQ-ORB-001','NQ Opening Range Breakout','v1.8','NQ','RED','2025-05-30 13:54','StrategyRunner','Edge decayed after open.',''],
    ['STR-CL-EIA-002','CL EIA Inventory Drift','v2.1','CL','YELLOW','2025-05-30 12:41','ResearchLab','Needs post-release validation.','selected'],
    ['STR-ESNQ-SPR-003','ES/NQ Spread Reversion','v0.9','ES, NQ','DRAFT','2025-05-29 18:12','ResearchLab','Hypothesis stage only.',''],
    ['STR-GC-VWAP-004','GC VWAP Mean Reversion','v3.0','GC','GREEN','2025-05-30 11:08','ValidationEngine','Stable under current regime.',''],
    ['STR-NQ-MOMO-005','NQ Regime Momentum','v1.4','NQ','TESTED','2025-05-30 10:36','RegimeMonitor','Awaiting verdict memo.',''],
    ['STR-CL-BRK-006','CL London Breakout','v2.7','CL','RED','2025-05-30 09:57','StrategyRunner','Drawdown breach.',''],
    ['STR-ES-IB-007','ES Initial Balance Fade','v1.2','ES','YELLOW','2025-05-29 16:48','DecisionEngine','Mixed validation set.',''],
    ['STR-GC-ADX-008','GC Trend Filter Stack','v1.0','GC','REGISTERED','2025-05-29 15:02','Overseer','Registered for first pass.',''],
    ['STR-NQ-REV-009','NQ Overnight Reversal','v2.5','NQ','RED','2025-05-30 08:21','PerformanceAnalyst','Weak live consistency.','']
  ];
  var tbl = '<table class="data-table"><thead><tr><th>Strategy ID</th><th>Name</th><th>Version</th><th>Instrument(s)</th><th>Status</th><th>Last Updated</th><th>Owner/Agent</th><th>Notes</th></tr></thead><tbody>';
  rows.forEach(function(r) {
    var bc = r[4]==='GREEN'?'green':r[4]==='RED'?'red':r[4]==='YELLOW'?'amber':'neutral';
    tbl += '<tr class="' + r[8] + '"><td class="mono">' + r[0] + '</td><td>' + r[1] + '</td><td>' + r[2] + '</td><td>' + r[3] +
      '</td><td>' + mxBadge(bc, r[4]) + '</td><td class="mono">' + r[5] + '</td><td>' + r[6] + '</td><td>' + r[7] + '</td></tr>';
  });
  tbl += '</tbody></table>';
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
  var hyps = [['CL EIA Drift','42','red','selected'],['NQ ORB Continuation','67','red',''],['GC VWAP Reversion','19','green',''],['ES/NQ Spread Mean Reversion','31','amber',''],['NQ Vol Compression Break','25','red','']];
  var list = '<div class="card"><div class="card-title">Registered Hypotheses</div><ul style="list-style:none">';
  hyps.forEach(function(h) {
    list += '<li style="padding:10px;border-bottom:1px solid var(--mx-border);' + (h[3]==='selected'?'background:var(--mx-blue-soft)':'') + '"><strong>' + h[0] +
      '</strong> <span class="mono" style="float:right">' + h[1] + '</span><br>' + mxBadge(h[2], h[2]==='green'?'GREEN':h[2]==='amber'?'YELLOW':'RED') + '</li>';
  });
  list += '</ul></div>';
  var stats = '<div class="stat-cards"><div class="stat-card"><div class="stat-card-label">OOS Net Profit Factor</div><div class="stat-card-value negative">0.97</div></div>' +
    '<div class="stat-card"><div class="stat-card-label">Deflated Sharpe Ratio</div><div class="stat-card-value negative">0.21</div></div>' +
    '<div class="stat-card"><div class="stat-card-label">Probabilistic Sharpe Ratio</div><div class="stat-card-value negative">48.6%</div></div>' +
    '<div class="stat-card"><div class="stat-card-label">Trial Count</div><div class="stat-card-value">42</div></div>' +
    '<div class="stat-card"><div class="stat-card-label">OOS Trade Count</div><div class="stat-card-value">186</div></div></div>';
  var wf = '<table class="data-table"><thead><tr><th>Fold</th><th>In-Sample Window</th><th>Out-of-Sample Window</th><th>Net P&amp;L</th><th>Pass/Fail</th></tr></thead><tbody>' +
    '<tr><td>1</td><td>2023-01→2023-06</td><td>2023-07→2023-08</td><td class="negative">-$420</td><td>' + mxBadge('red','FAIL') + '</td></tr>' +
    '<tr><td>2</td><td>2023-03→2023-08</td><td>2023-09→2023-10</td><td class="positive">+$190</td><td>' + mxBadge('green','PASS') + '</td></tr>' +
    '<tr><td>3</td><td>2023-05→2023-10</td><td>2023-11→2023-12</td><td class="negative">-$160</td><td>' + mxBadge('red','FAIL') + '</td></tr>' +
    '<tr><td>4</td><td>2023-07→2023-12</td><td>2024-01→2024-02</td><td class="positive">+$85</td><td>' + mxBadge('green','PASS') + '</td></tr>' +
    '<tr><td>5</td><td>2023-09→2024-02</td><td>2024-03→2024-04</td><td class="negative">-$275</td><td>' + mxBadge('red','FAIL') + '</td></tr></tbody></table>';
  var detail = '<div class="verdict-banner"><h3>VERDICT: RED — ARCHIVED</h3><p>OOS net PF 0.97, DSR not significant at 95%, 2/5 folds net-positive.</p></div>' +
    '<h3 style="margin-bottom:12px">CL EIA Inventory-Day Post-Report Drift</h3>' + stats + '<div class="card table-wrap" style="margin-bottom:16px">' + wf + '</div>' +
    '<div class="grid-2"><div class="card"><div class="card-title">Monte Carlo Drawdown Distribution</div><div id="chart-monte-carlo" style="height:220px"></div></div>' +
    '<div class="card"><div class="card-title">Distribution Summary</div><ul class="kv-list"><li><span class="kv-key">Median (50%)</span><span class="kv-val">-14.1%</span></li>' +
    '<li><span class="kv-key">95th Percentile</span><span class="kv-val">-3.2%</span></li><li><span class="kv-key">5th Percentile</span><span class="kv-val negative">-28.7%</span></li>' +
    '<li><span class="kv-key">Observed DD</span><span class="kv-val negative">-17.2%</span></li></ul></div></div>';
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
    '<div class="card-title" style="margin-bottom:12px">Forecast Lab</div>' + cards +
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
  var pills = ['Strategy GREEN','PropGuardian Clear','Size Within Caps','Session Open','No Event Blackout','Data Feed Healthy'];
  var pl = '<div class="guardrail-row">';
  pills.forEach(function(p) { pl += mxBadge('green', p); });
  pl += '</div>';
  var pos = '<table class="data-table"><thead><tr><th>Instrument</th><th>Side</th><th>Qty</th><th>Avg Price</th><th>Mark</th><th>Unrealized P&amp;L</th><th>Stop</th><th>Target</th></tr></thead><tbody>' +
    '<tr><td>NQ</td><td>' + mxBadge('green','LONG') + '</td><td>2</td><td class="mono">18,421.25</td><td class="mono">18,742.50</td><td class="positive">+$642.50</td><td class="mono">18,200.00</td><td class="mono">19,100.00</td></tr>' +
    '<tr><td>GC</td><td>' + mxBadge('neutral','FLAT') + '</td><td>0</td><td>—</td><td class="mono">2,358.40</td><td>$0.00</td><td>—</td><td>—</td></tr>' +
    '<tr><td>CL</td><td>' + mxBadge('red','SHORT') + '</td><td>1</td><td class="mono">77.85</td><td class="mono">77.35</td><td class="negative">-$500.00</td><td class="mono">78.60</td><td class="mono">75.20</td></tr>' +
    '<tr><td>ES</td><td>' + mxBadge('neutral','FLAT') + '</td><td>0</td><td>—</td><td class="mono">5,293.75</td><td>$0.00</td><td>—</td><td>—</td></tr></tbody></table>';
  var fills = '<table class="data-table"><thead><tr><th>Timestamp</th><th>Instrument</th><th>Side</th><th>Qty</th><th>Fill Price</th><th>Route</th><th>Status</th></tr></thead><tbody>' +
    '<tr><td class="mono">2025-05-30 14:21:37</td><td>NQ</td><td class="positive">BUY</td><td>1</td><td class="mono">18,735.25</td><td>SIM-ROUTE-A</td><td>' + mxBadge('green','FILLED') + '</td></tr>' +
    '<tr><td class="mono">2025-05-30 14:10:02</td><td>CL</td><td class="negative">SELL</td><td>1</td><td class="mono">77.85</td><td>SIM-ROUTE-A</td><td>' + mxBadge('green','FILLED') + '</td></tr>' +
    '<tr><td class="mono">2025-05-30 13:45:26</td><td>ES</td><td class="positive">BUY</td><td>2</td><td class="mono">5,285.50</td><td>SIM-ROUTE-A</td><td>' + mxBadge('amber','PARTIAL') + '</td></tr></tbody></table>';
  var form = '<div class="card order-form"><div class="card-title">New Order (Paper Mode)</div><p style="font-size:11px;color:var(--mx-muted);margin-bottom:12px">Order entry is disabled in paper mode. All activity is simulated only.</p>' +
    '<div class="grid-4"><input disabled placeholder="Instrument" style="padding:8px;border:1px solid var(--mx-border);border-radius:6px"><select disabled style="padding:8px"><option>Side</option></select>' +
    '<input disabled value="0" style="padding:8px;border:1px solid var(--mx-border);border-radius:6px"><button disabled class="btn-secondary">Submit Order</button></div></div>';
  return '<div class="page-header"><h1 class="page-title">Execution &amp; Orders</h1></div>' + banner + pl +
    '<div class="grid-2" style="margin:16px 0"><div class="card table-wrap"><div class="card-title">Open Positions (Paper)</div>' + pos + '</div>' +
    '<div class="card table-wrap"><div class="card-title">Recent Fills (Paper)</div>' + fills + '</div></div>' + form;
};

PAGES.journal = function() {
  var rows = [
    ['2025-05-30','11:42:07','NQ','LONG','Opening Range Breakout','STR-NQ-ORB-001','18,612.50','18,675.00','+$312.50','Risk-On','GO','selected'],
    ['2025-05-30','11:18:32','ES','LONG','IB Breakout','STR-ES-IB-007','5,292.50','5,300.25','+$155.00','Risk-On','GO',''],
    ['2025-05-30','10:07:55','CL','SHORT','Inventory Drift Fade','STR-CL-EIA-002','77.42','76.81','+$610.00','Risk-On','GO',''],
    ['2025-05-30','09:38:11','GC','LONG','VWAP Reversion','STR-GC-VWAP-004','2,356.40','2,352.60','-$180.00','Risk-Off','NO-GO OVERRIDE','']
  ];
  var tbl = '<table class="data-table"><thead><tr><th>Date</th><th>Time</th><th>Instrument</th><th>Side</th><th>Setup Tag</th><th>Strategy ID</th><th>Entry</th><th>Exit</th><th>Net P&amp;L</th><th>Regime at Entry</th><th>Decision</th></tr></thead><tbody>';
  rows.forEach(function(r) {
    var sc = r[3]==='LONG'?'green':'red';
    var dc = r[10]==='GO'?'green':'red';
    tbl += '<tr class="' + r[11] + '"><td>' + r[0] + '</td><td class="mono">' + r[1] + '</td><td>' + r[2] + '</td><td>' + mxBadge(sc, r[3]) +
      '</td><td>' + r[4] + '</td><td class="mono">' + r[5] + '</td><td class="mono">' + r[6] + '</td><td class="mono">' + r[7] +
      '</td><td class="' + (r[8].startsWith('+')?'positive':'negative') + '">' + r[8] + '</td><td>' + r[9] + '</td><td>' + mxBadge(dc, r[10]) + '</td></tr>';
  });
  tbl += '</tbody></table>';
  var detail = '<div class="card" style="margin-top:16px;border-left:4px solid var(--mx-blue)"><strong>NQ — Opening Range Breakout</strong>' +
    '<p style="font-size:12px;margin:8px 0"><strong>Decision Engine Reason:</strong> ORB breakout confirmed with 5-min volume expansion, regime Risk-On, validation GREEN.</p>' +
    '<p style="font-size:12px"><strong>Trader Notes:</strong> Entry followed plan. Partial exit was late.</p>' +
    '<div style="margin-top:8px;padding:8px;background:var(--mx-bg);border-radius:6px;font-size:11px">📷 screenshot attached — 2025-05-30 11:55 UTC — ResearchLab</div></div>';
  return '<div class="page-header"><h1 class="page-title">Trade Journal</h1><p class="page-subtitle">Structured trade log with setup context, execution details, and outcomes.</p></div>' +
    '<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap"><select style="padding:8px;border:1px solid var(--mx-border);border-radius:6px"><option>Instrument: All</option></select>' +
    '<input placeholder="Search trades..." style="flex:1;min-width:200px;padding:8px;border:1px solid var(--mx-border);border-radius:6px">' +
    '<button class="btn-secondary">Export CSV</button><button class="btn-primary">New Note</button></div>' +
    '<div class="card table-wrap">' + tbl + '</div>' + detail;
};

PAGES.performance = function() {
  var stats = '<div class="grid-4" style="margin-bottom:12px"><div><span class="mono positive" style="font-size:18px;font-weight:800">+$8,420</span><div style="font-size:10px;color:var(--mx-muted)">Net P&amp;L</div></div>' +
    '<div><span class="mono negative" style="font-size:18px;font-weight:800">-$2,180</span><div style="font-size:10px;color:var(--mx-muted)">Max DD</div></div>' +
    '<div><span class="mono" style="font-size:18px;font-weight:800">58%</span><div style="font-size:10px;color:var(--mx-muted)">Win Rate</div></div>' +
    '<div><span class="mono" style="font-size:18px;font-weight:800">1.42</span><div style="font-size:10px;color:var(--mx-muted)">Profit Factor</div></div></div>';
  var exp = [['Opening Range Breakout',0.28],['Trend Filter',0.18],['VWAP Reversion',0.07],['Momentum Continuation',-0.21],['Overnight Reversal',-0.32]];
  var eb = '';
  exp.forEach(function(e) {
    var w = Math.abs(e[1]) * 100;
    var cls = e[1] >= 0 ? 'green' : 'red';
    eb += '<div style="margin-bottom:6px"><div style="display:flex;justify-content:space-between;font-size:11px"><span>' + e[0] + '</span><span class="mono ' + (e[1]>=0?'positive':'negative') + '">' + e[1] + ' R</span></div>' +
      '<div class="progress-bar"><div class="progress-fill ' + cls + '" style="width:' + w + '%"></div></div></div>';
  });
  var attr = '<div class="card"><div class="card-title">Decision Attribution</div><ul style="list-style:none;font-size:12px;line-height:2">' +
    '<li>✓ Profitable GO calls: <strong class="positive">47</strong></li><li>✗ Unprofitable GO calls: <strong class="negative">34</strong></li>' +
    '<li>GO call hit rate: <strong>58%</strong></li><li>NO-GO counterfactual avoided: <strong>12</strong> losing setups</li></ul></div>';
  var ptable = '<table class="data-table"><thead><tr><th>Decision</th><th>Trades</th><th>Win Rate</th><th>Net P&amp;L (USD)</th><th>Avg P&amp;L (R)</th><th>Profit Factor</th><th>Max DD (USD)</th></tr></thead><tbody>' +
    '<tr><td>GO</td><td>81</td><td>58%</td><td class="positive">+$8,240</td><td>0.42</td><td>1.68</td><td class="negative">-$1,520</td></tr>' +
    '<tr><td>NO-GO</td><td>104</td><td>—</td><td class="positive">+$2,820</td><td>—</td><td>—</td><td>—</td></tr>' +
    '<tr><td>STAND-ASIDE</td><td>63</td><td>—</td><td>$0</td><td>—</td><td>—</td><td>—</td></tr>' +
    '<tr><td><strong>TOTAL</strong></td><td>248</td><td>—</td><td class="positive"><strong>+$9,060</strong></td><td>0.29</td><td>1.42</td><td class="negative">-$2,180</td></tr></tbody></table>';
  return '<div class="page-header"><h1 class="page-title">Performance Analytics</h1><p class="page-subtitle">Paper-simulated performance from live NQ returns (yfinance).</p></div>' +
    '<div class="card" id="tradeify-payout-live" style="margin-bottom:16px"></div>' +
    '<div class="card" style="margin-bottom:16px"><div class="card-title">Benchmark — NQ Futures (TradingView)</div><div id="tv-chart-performance"></div></div>' +
    '<div class="grid-2" style="margin-bottom:16px"><div class="card"><div class="card-title">Equity Curve &amp; Drawdown</div><div id="perf-stats-live">' + stats + '</div>' +
    '<div id="chart-equity-dd" style="height:280px"></div></div>' +
    '<div><div class="card" style="margin-bottom:16px"><div class="card-title">Rolling Sharpe Ratio</div><div class="mono">0.64</div><div id="chart-sharpe" style="height:100px"></div></div>' +
    '<div class="card"><div class="card-title">Rolling Sortino Ratio</div><div class="mono">0.98</div><div id="chart-sortino" style="height:100px"></div></div></div></div>' +
    '<div class="grid-3" style="margin-bottom:16px"><div class="card"><div class="card-title">Expectancy by Setup</div>' + eb + '</div>' +
    '<div class="card"><div class="card-title">Expectancy by Regime</div><p style="font-size:11px">Trending/Low Vol: <span class="positive">0.36 R</span></p></div>' +
    '<div class="card"><div class="card-title">Expectancy by Instrument</div><p style="font-size:11px">NQ: <span class="positive">0.34 R</span> &nbsp; CL: <span class="negative">-0.07 R</span></p></div></div>' +
    '<div class="grid-2">' + attr + '<div class="card table-wrap"><div class="card-title">Performance by Decision</div>' + ptable + '</div></div>';
};

PAGES.reports = function() {
  var reps = [
    ['Weekly Performance — Week of Jun29','Performance Summary','2025-06-30 09:12 UTC','COMPLETED',''],
    ['Verdict Memo — CL EIA Inventory Drift','Validation & Verdict','2025-05-30 12:41 UTC','COMPLETED','selected'],
    ['Verdict Memo — NQ Opening Range','Validation & Verdict','2025-05-30 10:36 UTC','COMPLETED',''],
    ['Risk Summary — PropGuardian','Risk Management','2025-05-28 18:29 UTC','COMPLETED',''],
    ['Monthly Research Digest — June','Research Digest','2025-05-28 14:05 UTC','COMPLETED','']
  ];
  var list = '<table class="data-table"><thead><tr><th>Report</th><th>Type</th><th>Generated</th><th>Status</th></tr></thead><tbody>';
  reps.forEach(function(r) {
    list += '<tr class="' + r[4] + '"><td><strong>' + r[0] + '</strong><br><span style="font-size:10px;color:var(--mx-muted)">' + r[1] + '</span></td><td>' + mxBadge('red','PDF') +
      '</td><td class="mono">' + r[2] + '</td><td>' + mxBadge('green', r[3]) + '</td></tr>';
  });
  list += '</tbody></table>';
  var preview = '<div class="card" style="min-height:400px"><div style="display:flex;justify-content:space-between;margin-bottom:12px"><strong>Verdict Memo — CL EIA Inventory Drift</strong>' +
    '<div><button class="btn-secondary">Download</button> <button class="btn-secondary">Export</button> <button class="btn-primary">Open Full Report</button></div></div>' +
    '<p style="font-size:11px;color:var(--mx-muted)">MarinerX Labs Research System</p>' +
    '<h3 style="margin:12px 0">Verdict Memo — CL EIA Inventory-Day Post-Report Drift</h3>' + mxBadge('red','VERDICT: RED — ARCHIVED') +
    '<p style="font-size:12px;margin:12px 0">OOS net PF 0.97, DSR not significant at 95%, 2/5 folds net-positive.</p>' +
    '<div id="chart-wf-bars" style="height:160px"></div>' +
    '<ul class="kv-list" style="margin-top:12px"><li><span class="kv-key">OOS Net Profit Factor</span><span class="kv-val negative">0.97</span></li>' +
    '<li><span class="kv-key">Trial Count</span><span class="kv-val">42</span></li><li><span class="kv-key">Observed DD</span><span class="kv-val negative">-17.2%</span></li></ul>' +
    '<p style="font-size:10px;color:var(--mx-muted);margin-top:12px">Generated: 2025-05-30 12:41 UTC &nbsp; Page 1 of 7</p></div>';
  return '<div class="page-header"><h1 class="page-title">Reports</h1><p class="page-subtitle">View, download, and manage generated research reports and documents.</p></div>' +
    '<div style="display:grid;grid-template-columns:40% 60%;gap:16px"><div class="card table-wrap"><div class="card-title">Generated Reports</div>' + list + '</div>' + preview + '</div>';
};

PAGES.settings = function() {
  var feeds = '<table class="data-table"><thead><tr><th>Feed</th><th>Status</th><th>Description</th><th>Latency</th></tr></thead><tbody>' +
    '<tr><td>Databento</td><td>' + mxBadge('green','CONNECTED') + '</td><td>Market data (NQ, ES, CL, GC)</td><td class="mono">200 ms</td></tr>' +
    '<tr><td>IQFeed</td><td>' + mxBadge('neutral','NOT CONFIGURED') + '</td><td>Backup market data</td><td>—</td></tr>' +
    '<tr><td>Tradovate</td><td>' + mxBadge('neutral','NOT CONFIGURED') + '</td><td>Futures execution</td><td>—</td></tr>' +
    '<tr><td>Tradeify Sync</td><td>' + mxBadge('blue','LAST SYNCED') + '</td><td>Trade journal sync</td><td>4 MIN AGO</td></tr>' +
    '<tr><td>Railway Deployment</td><td>' + mxBadge('green','HEALTHY') + '</td><td>Application deployment</td><td>100%</td></tr>' +
    '<tr><td>Database</td><td>' + mxBadge('green','HEALTHY') + '</td><td>PostgreSQL database</td><td>100%</td></tr></tbody></table>';
  var config = '<ul class="kv-list"><li><span class="kv-key">Risk Per Trade</span><span class="kv-val">$350</span></li>' +
    '<li><span class="kv-key">Daily Loss Limit</span><span class="kv-val">$2,000</span></li><li><span class="kv-key">Max Contracts</span><span class="kv-val">3</span></li>' +
    '<li><span class="kv-key">Instruments Enabled</span><span class="kv-val">NQ / ES / CL / GC</span></li><li><span class="kv-key">Live Execution</span><span class="kv-val negative">DISABLED</span></li>' +
    '<li><span class="kv-key">Paper Trading</span><span class="kv-val positive">ENABLED</span></li><li><span class="kv-key">Account Mode</span><span class="kv-val">Evaluation</span></li></ul>';
  var danger = '<div class="danger-zone"><p style="font-size:12px;margin-bottom:12px">Critical system controls. Actions are immediate and irreversible.</p>' +
    '<button class="btn-kill" style="width:100%;margin-bottom:12px">GLOBAL KILL SWITCH</button>' +
    '<label style="font-size:12px;display:flex;gap:8px;margin-bottom:12px"><input type="checkbox"> I understand this will flatten/disable all active execution routes</label>' +
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px"><label class="toggle"><input type="checkbox"><span class="toggle-slider"></span></label><span>Live Execution OFF — DISABLED</span></div>' +
    '<input placeholder="confirmation token" style="width:100%;padding:8px;border:1px solid var(--mx-border);border-radius:6px"></div>';
  var audit = '<table class="data-table"><thead><tr><th>Timestamp</th><th>User/System</th><th>Action</th><th>Result</th></tr></thead><tbody>' +
    '<tr><td class="mono">2025-05-30 14:31:02 UTC</td><td>ResearchLab</td><td>Risk config read</td><td>' + mxBadge('green','SUCCESS') + '</td></tr>' +
    '<tr><td class="mono">2025-05-30 14:30:15 UTC</td><td>ResearchLab</td><td>Paper trading enabled</td><td>' + mxBadge('green','SUCCESS') + '</td></tr>' +
    '<tr><td class="mono">2025-05-30 14:29:41 UTC</td><td>ResearchLab</td><td>Live execution disabled</td><td>' + mxBadge('green','SUCCESS') + '</td></tr></tbody></table>';
  return '<div class="page-header"><h1 class="page-title">Settings &amp; System Control</h1><p class="page-subtitle">System configuration, data feeds, execution controls, and audit.</p></div>' +
    '<div class="card" id="tradeify-connector-live" style="margin-bottom:16px"></div>' +
    '<div class="grid-2" style="margin-bottom:16px"><div class="card table-wrap"><div class="card-title">Data &amp; Feed Status</div>' + feeds + '</div>' +
    '<div class="card"><div class="card-title">Configuration (Read-Only)</div>' + config + '</div></div>' +
    '<div class="card" style="margin-bottom:16px">' + danger + '</div>' +
    '<div class="card table-wrap"><div class="card-title">Audit Log</div>' + audit + '</div>';
};
