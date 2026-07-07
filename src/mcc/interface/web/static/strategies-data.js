/* Strategy Registry — real API wiring */
(function () {
  'use strict';

  function badgeClass(status) {
    if (status === 'GREEN') return 'green';
    if (status === 'RED') return 'red';
    if (status === 'YELLOW') return 'amber';
    return 'neutral';
  }

  function renderTable(strategies) {
    var tbody = document.getElementById('strategy-registry-live');
    if (!tbody) return;
    if (!strategies.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--mx-muted)">No strategies registered.</td></tr>';
      return;
    }
    tbody.innerHTML = strategies.map(function (s) {
      var bc = badgeClass(s.status);
      var updated = (s.updated_at || '').replace('T', ' ').slice(0, 19);
      return '<tr><td class="mono">' + s.strategy_id + '</td><td>' + (s.name || '') + '</td><td>v' + (s.version || 1) +
        '</td><td>' + (s.instrument || '') + '</td><td><span class="badge badge-' + bc + '">' + s.status + '</span></td>' +
        '<td class="mono">' + (updated || '—') + '</td><td>' + (s.owner_agent || '') + '</td><td>' + (s.latest_verdict || '—') + '</td></tr>';
    }).join('');
  }

  function hydrate() {
    var tbody = document.getElementById('strategy-registry-live');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center">Loading strategies…</td></tr>';
    fetch('/api/strategies').then(function (r) { return r.json(); }).then(function (j) {
      renderTable(j.strategies || []);
    }).catch(function () {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--mx-red-text)">Failed to load strategies.</td></tr>';
    });
  }

  window.StrategiesData = { hydrate: hydrate };
})();