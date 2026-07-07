/* Trade-or-No-Trade — real API wiring */
(function () {
  'use strict';

  function hydrate() {
    var detail = document.getElementById('decision-detail-live');
    if (!detail) return;
    detail.innerHTML = '<div class="card"><p>Loading decision engine…</p>' +
      '<button class="btn-primary" id="dec-eval-btn">Evaluate NQ</button></div>';
    var btn = document.getElementById('dec-eval-btn');
    if (btn) btn.addEventListener('click', evaluate);
    fetch('/api/strategies').then(function (r) { return r.json(); }).then(function (j) {
      var green = (j.strategies || []).find(function (s) { return s.status === 'GREEN'; });
      if (green) window.__mxDecisionStrategy = green.strategy_id;
    }).catch(function () { /* ignore */ });
  }

  function evaluate() {
    var detail = document.getElementById('decision-detail-live');
    if (!detail) return;
    detail.innerHTML = '<div class="card"><p>Evaluating…</p></div>';
    var body = { symbol: 'NQ', strategy_id: window.__mxDecisionStrategy || null };
    fetch('/api/decision/evaluate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var bc = d.decision === 'GO' ? 'green' : d.decision === 'STAND-ASIDE' ? 'amber' : 'red';
        var factors = Object.keys(d.factor_scores || {}).map(function (k) {
          return '<li><span class="kv-key">' + k + '</span><span class="kv-val mono">' + d.factor_scores[k] + '</span></li>';
        }).join('');
        detail.innerHTML = '<div class="card"><div style="display:flex;justify-content:space-between;margin-bottom:12px">' +
          '<strong>' + d.symbol + ' Decision</strong><span class="badge badge-' + bc + '">' + d.decision + '</span></div>' +
          '<p class="mono">Confidence: ' + ((d.confidence || 0) * 100).toFixed(1) + '% | ID: ' + (d.decision_id || '—') + '</p>' +
          '<p style="font-size:12px;margin:8px 0">' + (d.rationale || '') + '</p>' +
          '<p style="font-size:11px;color:var(--mx-muted)">' + (d.timestamp || '') + '</p>' +
          '<div class="card-title">Vetoes</div><p>' + ((d.vetoes || []).join(', ') || 'None') + '</div>' +
          '<div class="card-title">Factor Scores</div><ul class="kv-list">' + factors + '</ul>' +
          '<button class="btn-primary" id="dec-eval-btn">Re-evaluate</button></div>';
        var btn = document.getElementById('dec-eval-btn');
        if (btn) btn.addEventListener('click', evaluate);
      }).catch(function () {
        detail.innerHTML = '<div class="card" style="color:var(--mx-red-text)">Decision evaluation failed.</div>';
      });
  }

  window.DecisionData = { hydrate: hydrate, evaluate: evaluate };
})();